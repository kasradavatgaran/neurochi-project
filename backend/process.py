import logging
import os
import re
import json
from urllib.parse import quote, urlparse

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

CHUNK_SIZE = max(1500, int(os.getenv("RAG_CHUNK_SIZE", "3500")))
CHUNK_OVERLAP = max(200, min(int(os.getenv("RAG_CHUNK_OVERLAP", "500")), CHUNK_SIZE - 200))
TEXT_DIRECTORY = "./farsi_translations"
SOURCE_MANIFEST_PATH = os.getenv(
    "RAG_SOURCE_MANIFEST",
    os.path.join(TEXT_DIRECTORY, "source_manifest.json"),
)

logger = logging.getLogger("rag_service.process")

TITLE_PREFIX_PATTERN = re.compile(
    r"^(?:\u0639\u0646\u0648\u0627\u0646|\u0633\u0631\u062e\u0637|\u062a\u06cc\u062a\u0631|\u0633\u0631\u062a\u06cc\u062a\u0631|\u0633\u0631\u0641\u0635\u0644|\u062e\u0628\u0631|\u0645\u0642\u0627\u0644|\u0645\u0642\u062f\u0645\u0647)\s*[:\uff1a-]?\s*"
)
TITLE_LINE_PATTERN = re.compile(
    r"^(?:\u0639\u0646\u0648\u0627\u0646|\u0633\u0631\u062e\u0637|\u062a\u06cc\u062a\u0631|\u0633\u0631\u062a\u06cc\u062a\u0631|\u0633\u0631\u0641\u0635\u0644|\u062e\u0628\u0631)\s*[:\uff1a-]\s*(.+)$"
)
URL_LINE_PATTERN = re.compile(
    r"\u0644\u06cc\u0646\u06a9\s+\u0645\u0642\u0627\u0644\u0647\s+\u0627\u0635\u0644\u06cc\s*[:\uff1a]\s*(https?://\S+)",
    re.IGNORECASE,
)
GENERIC_URL_PATTERN = re.compile(r"(https?://[^\s<>\]\"')]+)", re.IGNORECASE)
NON_TITLE_LINE_PATTERN = re.compile(
    r"^(?:\u0645\u062d\u062a\u0648\u0627\u06cc?\s+\u0645\u0642\u0627\u0644\u0647|\u0645\u0642\u062f\u0645\u0647|\u0645\u0642\u0627\u0644\u0647|\u0645\u062a\u0646\s+\u0645\u0642\u0627\u0644\u0647|\u0645\u062a\u0646|content)\s*[:\uff1a-]?$",
    re.IGNORECASE,
)


def clean_title(raw_title: str) -> str:
    if not raw_title:
        return ""

    title = raw_title.replace("\ufeff", " ").strip()
    title = re.sub(r"^[#\-\s*]+", "", title)
    title = TITLE_PREFIX_PATTERN.sub("", title)
    title = title.strip().strip("\"'“”‘’«»()[]{}*_")
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def fallback_title_from_filename(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    stem = stem.replace("_", " ").replace("-", " ")
    return clean_title(stem) or filename


def is_reasonable_title(title: str) -> bool:
    if not title:
        return False
    if GENERIC_URL_PATTERN.search(title):
        return False
    if len(title) > 160:
        return False
    if len(title.split()) > 24:
        return False
    return True


def should_skip_title_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if URL_LINE_PATTERN.match(stripped) or GENERIC_URL_PATTERN.search(stripped):
        return True
    if NON_TITLE_LINE_PATTERN.match(stripped):
        return True
    return False


def extract_site_name(url: str) -> str:
    if not url:
        return "\u0645\u0646\u0628\u0639 \u0646\u0627\u0645\u0634\u062e\u0635"

    hostname = urlparse(url).netloc.lower().strip()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname or "\u0645\u0646\u0628\u0639 \u0646\u0627\u0645\u0634\u062e\u0635"


def extract_metadata_from_content(content: str, filename: str):
    metadata = {}

    url_match = URL_LINE_PATTERN.search(content) or GENERIC_URL_PATTERN.search(content)
    metadata["url"] = url_match.group(1).strip() if url_match else ""

    lines = [line.strip() for line in content.split("\n") if line.strip()]
    title = ""

    for line in lines:
        title_match = TITLE_LINE_PATTERN.match(line)
        if not title_match:
            continue

        candidate = clean_title(title_match.group(1))
        if is_reasonable_title(candidate):
            title = candidate
            break

    if not title:
        for line in lines[:20]:
            if should_skip_title_line(line):
                continue

            candidate = clean_title(line)
            if is_reasonable_title(candidate):
                title = candidate
                break

    metadata["title"] = title or fallback_title_from_filename(filename)
    metadata["source"] = extract_site_name(metadata["url"])
    metadata["source_name"] = metadata["source"]
    metadata["source_file"] = filename

    return metadata


def load_source_manifest() -> dict:
    if not os.path.isfile(SOURCE_MANIFEST_PATH):
        return {}
    try:
        with open(SOURCE_MANIFEST_PATH, "r", encoding="utf-8") as manifest_file:
            return json.load(manifest_file)
    except Exception as exc:
        logger.warning("Could not load RAG source manifest: %s", exc)
        return {}


def build_local_source_url(filename: str) -> str:
    return f"/rag/source-files/{quote(filename, safe='')}"


def get_reference_url(metadata: dict) -> str:
    return metadata.get("url") or build_local_source_url(metadata["source_file"])


def strip_document_scaffolding(content: str) -> str:
    cleaned_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if TITLE_LINE_PATTERN.match(stripped):
            continue
        if URL_LINE_PATTERN.match(stripped):
            continue
        if NON_TITLE_LINE_PATTERN.match(stripped):
            continue
        cleaned_lines.append(line)

    cleaned_content = "\n".join(cleaned_lines).strip()
    return cleaned_content or content.strip()


def build_chunk_content(metadata: dict, chunk_text: str, chunk_index: int, total_chunks: int) -> str:
    reference_url = get_reference_url(metadata)
    source_name = metadata.get("source") or extract_site_name(metadata.get("url", ""))
    body = chunk_text.strip()
    return (
        f"موضوع مقاله: {metadata['title']}\n"
        f"سایت: {source_name}\n"
        f"لینک منبع: {reference_url}\n"
        f"بخش سند: {chunk_index}/{total_chunks}\n\n"
        f"{body}"
    )


def process_all_txts_in_directory() -> list[Document]:
    all_chunks = []

    if not os.path.isdir(TEXT_DIRECTORY):
        msg = f"Directory not found: {TEXT_DIRECTORY}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    txt_files = [f for f in os.listdir(TEXT_DIRECTORY) if f.lower().endswith(".txt")]

    if not txt_files:
        msg = f"No .txt files found in directory: {TEXT_DIRECTORY}"
        logger.warning(msg)
        raise ValueError(msg)

    logger.info("Found %s .txt file(s) to process.", len(txt_files))
    source_manifest = load_source_manifest()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    for txt_file in txt_files:
        file_path = os.path.join(TEXT_DIRECTORY, txt_file)
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            raw_documents = loader.load()

            if not raw_documents:
                continue

            primary_doc = raw_documents[0]
            extracted_meta = extract_metadata_from_content(primary_doc.page_content, txt_file)
            manifest_meta = source_manifest.get(txt_file, {})
            if manifest_meta.get("title"):
                extracted_meta["title"] = manifest_meta["title"]
            if manifest_meta.get("url"):
                extracted_meta["url"] = manifest_meta["url"]
            if manifest_meta.get("source_name"):
                extracted_meta["source_name"] = manifest_meta["source_name"]
                extracted_meta["source"] = manifest_meta["source_name"]
            elif extracted_meta.get("url"):
                extracted_meta["source_name"] = extract_site_name(extracted_meta["url"])
            cleaned_content = strip_document_scaffolding(primary_doc.page_content)
            raw_chunks = text_splitter.split_text(cleaned_content)

            chunks_from_file = []
            total_chunks = max(1, len(raw_chunks))
            for chunk_index, chunk_text in enumerate(raw_chunks, start=1):
                chunk_metadata = dict(extracted_meta)
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["chunk_count"] = total_chunks
                chunk_metadata["reference_url"] = get_reference_url(extracted_meta)
                chunks_from_file.append(
                    Document(
                        page_content=build_chunk_content(chunk_metadata, chunk_text, chunk_index, total_chunks),
                        metadata=chunk_metadata,
                    )
                )

            all_chunks.extend(chunks_from_file)

            logger.info(
                "Processed '%s' | Title: %s | Chunks: %s",
                txt_file,
                extracted_meta["title"],
                len(chunks_from_file),
            )
        except Exception as exc:
            logger.error("Failed to process file '%s': %s", txt_file, exc, exc_info=True)
            continue

    return all_chunks
