"""Translate NHS and incomplete Kinedu articles into the local RAG corpus.

The job is intentionally resumable.  It persists each successful title/body
segment and keeps at most eight Liara requests in flight; a completed request
is immediately replaced by the next pending segment.

Run from ``backend``:
    python translate_rag_sources.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from generate import call_liara_chat_completion


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "farsi_translations"
SOURCE_MANIFEST_PATH = OUTPUT_DIRECTORY / "source_manifest.json"
PROGRESS_PATH = OUTPUT_DIRECTORY / "translation_progress.json"
KINDU_DIRECTORY = PROJECT_ROOT / "kinedu"
NHS_DIRECTORY = PROJECT_ROOT / "nhs"
TRANSLATION_VERSION = "liara-fa-v1"
PERSIAN_PATTERN = re.compile(r"[\u0600-\u06FF]")
DEFAULT_MAX_INPUT_CHARS = 12_000
DEFAULT_WORKERS = 8
DEFAULT_RETRIES = 3


@dataclass(frozen=True)
class Article:
    key: str
    provider: str
    output_name: str
    title: str
    url: str
    body: str
    fingerprint: str


@dataclass(frozen=True)
class TranslationJob:
    key: str
    article_key: str
    kind: str
    input_text: str
    fingerprint: str


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_translation(value: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in str(value or "").replace("\r\n", "\n").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    temporary_path.replace(path)


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        handle.write(value.strip() + "\n")
    temporary_path.replace(path)


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else fallback
    except (OSError, ValueError):
        return fallback


def is_valid_translation(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return len(text) >= 300 and bool(PERSIAN_PATTERN.search(text))


def kinedu_url_from_slug(slug: str) -> str:
    return f"https://blog.kinedu.com/{slug.strip('/')}/"


def read_json_article(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def build_articles() -> tuple[list[Article], list[str]]:
    articles: list[Article] = []
    errors: list[str] = []

    for path in sorted(KINDU_DIRECTORY.glob("*.json")):
        try:
            data = read_json_article(path)
            title = compact_text(data.get("title_text") or data.get("title"))
            body = str(data.get("content_text") or data.get("content") or "").strip()
            if not title or not body:
                raise ValueError("missing title_text or content_text")
            url = compact_text(data.get("url") or data.get("link")) or kinedu_url_from_slug(path.stem)
            fingerprint = sha256_text(f"kinedu\n{title}\n{url}\n{body}")
            articles.append(
                Article(
                    key=f"kinedu:{path.stem}",
                    provider="kinedu",
                    output_name=f"{path.stem}.txt",
                    title=title,
                    url=url,
                    body=body,
                    fingerprint=fingerprint,
                )
            )
        except ValueError as exc:
            errors.append(str(exc))

    for path in sorted(NHS_DIRECTORY.glob("*.json")):
        try:
            data = read_json_article(path)
            title = compact_text(data.get("title"))
            description = compact_text(data.get("description"))
            paragraphs = data.get("content_paragraphs")
            if not isinstance(paragraphs, list):
                paragraphs = []
            body_parts = [description] if description else []
            body_parts.extend(str(item).strip() for item in paragraphs if str(item).strip())
            body = "\n\n".join(body_parts).strip()
            url = compact_text(data.get("url"))
            if not title or not body or not url:
                raise ValueError("missing title, URL, or content_paragraphs")
            fingerprint = sha256_text(f"nhs\n{title}\n{url}\n{body}")
            articles.append(
                Article(
                    key=f"nhs:{path.stem}",
                    provider="nhs",
                    output_name=f"nhs__{path.stem}.txt",
                    title=title,
                    url=url,
                    body=body,
                    fingerprint=fingerprint,
                )
            )
        except ValueError as exc:
            errors.append(str(exc))

    return articles, errors


def split_at_paragraphs(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text.replace("\r\n", "\n")) if part.strip()]
    parts: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs or [text.strip()]:
        while len(paragraph) > max_chars:
            split_at = paragraph.rfind(". ", 0, max_chars)
            split_at = split_at + 1 if split_at >= max_chars // 2 else max_chars
            prefix, paragraph = paragraph[:split_at].strip(), paragraph[split_at:].strip()
            if prefix:
                if current:
                    parts.append("\n\n".join(current))
                    current, current_length = [], 0
                parts.append(prefix)

        additional = len(paragraph) + (2 if current else 0)
        if current and current_length + additional > max_chars:
            parts.append("\n\n".join(current))
            current, current_length = [], 0
        current.append(paragraph)
        current_length += additional

    if current:
        parts.append("\n\n".join(current))
    return parts or [text.strip()]


def build_jobs(articles: Iterable[Article], progress: dict, max_input_chars: int, force: bool) -> tuple[list[TranslationJob], list[Article]]:
    jobs: list[TranslationJob] = []
    translation_articles: list[Article] = []
    completed_jobs = progress.setdefault("jobs", {})

    for article in articles:
        output_path = OUTPUT_DIRECTORY / article.output_name
        needs_translation = force or article.provider == "nhs" and not is_valid_translation(output_path)
        if article.provider == "kinedu":
            needs_translation = force or not is_valid_translation(output_path)
        if not needs_translation:
            continue

        translation_articles.append(article)
        job_inputs = [("title", 0, article.title)]
        job_inputs.extend(("body", index, segment) for index, segment in enumerate(split_at_paragraphs(article.body, max_input_chars), start=1))

        for kind, index, input_text in job_inputs:
            key = f"{article.key}:{kind}:{index}"
            fingerprint = sha256_text(f"{TRANSLATION_VERSION}\n{article.fingerprint}\n{kind}\n{index}\n{input_text}")
            saved = completed_jobs.get(key, {})
            if saved.get("fingerprint") == fingerprint and compact_text(saved.get("text")):
                continue
            jobs.append(TranslationJob(key, article.key, kind, input_text, fingerprint))

    return jobs, translation_articles


def job_messages(job: TranslationJob) -> list[dict]:
    if job.kind == "title":
        task = "Translate the following article title into natural Persian. Return only the Persian title."
    else:
        task = (
            "Translate the following child-health article passage into natural Persian. Preserve paragraph breaks, headings, "
            "lists, measurements, and uncertainty. Do not summarize, add medical advice, add a title, add a URL, or write commentary."
        )
    return [{"role": "system", "content": task}, {"role": "user", "content": job.input_text}]


def translate_job(job: TranslationJob, retries: int) -> str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = call_liara_chat_completion(job_messages(job), temperature=0, reasoning_effort="low")
            translated = compact_text(response) if job.kind == "title" else normalize_translation(response)
            if not translated or not PERSIAN_PATTERN.search(translated):
                raise RuntimeError("Liara response is not a Persian translation")
            return translated
        except Exception as exc:  # noqa: BLE001 - record provider errors for resume
            last_error = exc
            if attempt < retries:
                time.sleep(min(8, attempt * 2))
    raise RuntimeError(f"translation failed after {retries} attempts: {last_error}") from last_error


def source_name(url: str) -> str:
    hostname = urlparse(url).netloc.lower()
    return hostname[4:] if hostname.startswith("www.") else hostname


def compose_article(article: Article, progress: dict, max_input_chars: int) -> str | None:
    saved_jobs = progress.get("jobs", {})
    title_key = f"{article.key}:title:0"
    title = compact_text(saved_jobs.get(title_key, {}).get("text"))
    segments = split_at_paragraphs(article.body, max_input_chars)
    translated_segments = [compact_text(saved_jobs.get(f"{article.key}:body:{index}", {}).get("text")) for index in range(1, len(segments) + 1)]
    if not title or any(not value for value in translated_segments):
        return None

    return (
        f"\u0639\u0646\u0648\u0627\u0646: {title}\n"
        f"\u0644\u06cc\u0646\u06a9 \u0645\u0642\u0627\u0644\u0647 \u0627\u0635\u0644\u06cc: {article.url}\n"
        f"\u0645\u0646\u0628\u0639: {source_name(article.url)}\n\n"
        + "\n\n".join(translated_segments)
    )


def update_source_manifest(articles: Iterable[Article], translated_articles: Iterable[Article], progress: dict, max_input_chars: int) -> int:
    manifest = load_json(SOURCE_MANIFEST_PATH, {})
    translated_keys = {article.key for article in translated_articles}
    changed = 0

    for article in articles:
        entry = {"url": article.url, "source_name": source_name(article.url)}
        if article.key in translated_keys:
            title = compact_text(progress.get("jobs", {}).get(f"{article.key}:title:0", {}).get("text"))
            if title:
                entry["title"] = title
        if manifest.get(article.output_name) != entry:
            manifest[article.output_name] = entry
            changed += 1

    if changed or not SOURCE_MANIFEST_PATH.exists():
        atomic_write_json(SOURCE_MANIFEST_PATH, manifest)
    return changed


def run_queue(jobs: list[TranslationJob], progress: dict, workers: int, retries: int) -> tuple[int, list[str]]:
    if not jobs:
        return 0, []

    completed = 0
    failures: list[str] = []
    pending = iter(jobs)
    in_flight: dict[Future, TranslationJob] = {}

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="liara-translation") as executor:
        for _ in range(min(workers, len(jobs))):
            job = next(pending, None)
            if job is not None:
                in_flight[executor.submit(translate_job, job, retries)] = job

        while in_flight:
            done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in done:
                job = in_flight.pop(future)
                try:
                    text = future.result()
                    progress["jobs"][job.key] = {"fingerprint": job.fingerprint, "text": text, "completed_at": int(time.time())}
                    progress.get("failures", {}).pop(job.key, None)
                    completed += 1
                    print(f"completed {completed}/{len(jobs)}: {job.key}")
                except Exception as exc:  # noqa: BLE001 - surfaced in the final report
                    message = f"{job.key}: {exc}"
                    progress.setdefault("failures", {})[job.key] = message
                    failures.append(message)
                    print(f"failed: {message}")
                atomic_write_json(PROGRESS_PATH, progress)

                next_job = next(pending, None)
                if next_job is not None:
                    in_flight[executor.submit(translate_job, next_job, retries)] = next_job

    return completed, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate NHS and incomplete Kinedu RAG sources with Liara.")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--max-input-chars", type=int, default=DEFAULT_MAX_INPUT_CHARS)
    parser.add_argument("--force", action="store_true", help="Re-translate valid outputs too.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.workers != DEFAULT_WORKERS:
        raise SystemExit(f"This pipeline intentionally requires exactly {DEFAULT_WORKERS} concurrent requests.")
    if args.retries < 1 or args.max_input_chars < 1_000:
        raise SystemExit("--retries must be positive and --max-input-chars must be at least 1000.")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    progress = load_json(PROGRESS_PATH, {"version": TRANSLATION_VERSION, "jobs": {}, "failures": {}})
    progress.setdefault("jobs", {})
    progress.setdefault("failures", {})

    articles, input_errors = build_articles()
    jobs, translation_articles = build_jobs(articles, progress, args.max_input_chars, args.force)
    print(f"sources={len(articles)} translation_articles={len(translation_articles)} pending_jobs={len(jobs)}")
    if input_errors:
        print(f"input_errors={len(input_errors)}")
        for error in input_errors:
            print(f"input_error: {error}")
    if args.dry_run:
        return 0 if not input_errors else 2

    completed, failures = run_queue(jobs, progress, args.workers, args.retries)
    written = 0
    for article in translation_articles:
        rendered = compose_article(article, progress, args.max_input_chars)
        if rendered is None:
            failures.append(f"{article.key}: one or more translation segments are incomplete")
            continue
        atomic_write_text(OUTPUT_DIRECTORY / article.output_name, rendered)
        written += 1

    manifest_updates = update_source_manifest(articles, translation_articles, progress, args.max_input_chars)
    atomic_write_json(PROGRESS_PATH, progress)
    print(
        f"completed_jobs={completed} outputs_written={written} manifest_updates={manifest_updates} "
        f"failures={len(failures) + len(input_errors)}"
    )
    return 0 if not failures and not input_errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
