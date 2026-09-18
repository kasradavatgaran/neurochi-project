import hashlib
import logging
import math
import os
import re
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from openai import OpenAI

if TYPE_CHECKING:
    from sentence_transformers.cross_encoder import CrossEncoder

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger("rag_service.retrieve")
LIARA_EMBEDDING_MODEL = os.getenv("LIARA_EMBEDDING_MODEL", "google/gemini-embedding-001")
LIARA_EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("LIARA_EMBEDDING_BATCH_SIZE", "64")))
LIARA_EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("LIARA_EMBEDDING_TIMEOUT_SECONDS", "120"))
LIARA_EMBEDDING_MAX_RETRIES = max(0, int(os.getenv("LIARA_EMBEDDING_MAX_RETRIES", "4")))
LIARA_EMBEDDING_RETRY_DELAY_SECONDS = float(os.getenv("LIARA_EMBEDDING_RETRY_DELAY_SECONDS", "2"))
RAG_ENABLE_RERANKER = os.getenv("RAG_ENABLE_RERANKER", "false").strip().lower() in {"1", "true", "yes", "on"}
RAG_ENABLE_VECTOR_SEARCH = os.getenv("RAG_ENABLE_VECTOR_SEARCH", "false").strip().lower() in {"1", "true", "yes", "on"}
RAG_MIN_HEURISTIC_SCORE = max(1, int(os.getenv("RAG_MIN_HEURISTIC_SCORE", "3")))
RAG_BM25_CANDIDATE_K = max(10, min(int(os.getenv("RAG_BM25_CANDIDATE_K", "20")), 30))
RAG_SEMANTIC_CANDIDATE_K = max(1, min(int(os.getenv("RAG_SEMANTIC_CANDIDATE_K", "10")), RAG_BM25_CANDIDATE_K))
RAG_SEMANTIC_RERANK_K = max(1, min(int(os.getenv("RAG_SEMANTIC_RERANK_K", "5")), RAG_SEMANTIC_CANDIDATE_K))
RAG_LEXICAL_GUARD_K = max(1, min(int(os.getenv("RAG_LEXICAL_GUARD_K", "2")), RAG_SEMANTIC_RERANK_K))
RAG_SEMANTIC_DOCUMENT_CHARS = max(500, int(os.getenv("RAG_SEMANTIC_DOCUMENT_CHARS", "4000")))
RAG_SEMANTIC_CACHE_SIZE = max(50, int(os.getenv("RAG_SEMANTIC_CACHE_SIZE", "500")))
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "safora/reranker-xlm-roberta-large")

QUERY_SYNONYMS = {
    "بچه": ["کودک", "نوزاد", "فرزند"],
    "کودک": ["بچه", "نوزاد", "فرزند"],
    "نوزاد": ["بچه", "کودک", "فرزند"],
    "شیر": ["شیر", "شیر مادر", "شیر خشک", "غذا"],
    "غذا": ["غذا", "شیر", "تغذیه"],
    "نمیخوره": ["نمی خورد", "نخوردن", "غذا نمی خورد", "شیر نمی خورد"],
    "نمی‌خوره": ["نمی خورد", "نخوردن", "غذا نمی خورد", "شیر نمی خورد"],
    "نمیخورد": ["نمی خورد", "نخوردن", "غذا نمی خورد", "شیر نمی خورد"],
    "نمی‌خورد": ["نمی خورد", "نخوردن", "غذا نمی خورد", "شیر نمی خورد"],
    "نخوردن": ["نمی خورد", "غذا نمی خورد", "شیر نمی خورد"],
}

# Query rewriting happens before retrieval, but keep this deterministic layer as a
# safety net.  Common question words and a child's name must not outweigh the
# actual health/development topic when BM25 is used without a cross-encoder.
RETRIEVAL_STOPWORDS = {
    "از", "با", "به", "برای", "در", "را", "که", "و", "یا", "این", "آن",
    "من", "ما", "شما", "چی", "چیه", "چه", "چطور", "چگونه", "چقدر", "کدوم",
    "کرد", "کنم", "کنه", "کنید", "داره", "دارم", "دارند", "است", "هست",
    "می", "نمیشه", "نمیدونم", "لطفا", "لطفاً", "how", "what", "when", "where",
    "why", "do", "does", "is", "are", "the", "a", "an", "for", "to", "of",
    "and", "my", "your", "need", "please",
}

QUERY_SYNONYMS.update({
    "خواب": ["خواب", "ساعت خواب", "میزان خواب", "نیاز به خواب", "برنامه خواب", "تنظیم خواب"],
    "تنظیم": ["تنظیم خواب", "برنامه خواب", "الگوی خواب", "ساعت خواب"],
    "بیخوابی": ["خواب", "مشکل خواب", "بیدار شدن شبانه"],
    "نمیخوابد": ["خواب", "مشکل خواب", "بیدار شدن شبانه"],
    "نمیخوابم": ["خواب", "مشکل خواب"],
})

# Keep retrieval vocabulary Unicode-safe. Some of the legacy dictionary was
# saved with a Windows encoding and cannot match incoming Persian text.
QUERY_SYNONYMS.update({
    "\u062e\u0648\u0627\u0628": [
        "\u062e\u0648\u0627\u0628", "\u0633\u0627\u0639\u062a \u062e\u0648\u0627\u0628", "\u0645\u06cc\u0632\u0627\u0646 \u062e\u0648\u0627\u0628",
        "\u0646\u06cc\u0627\u0632 \u0628\u0647 \u062e\u0648\u0627\u0628", "sleep", "sleeping", "bedtime", "nap", "hours sleep",
    ],
    "\u0646\u06cc\u0627\u0632": ["\u0646\u06cc\u0627\u0632", "\u0645\u06cc\u0632\u0627\u0646", "\u0633\u0627\u0639\u062a", "need", "how much", "hours"],
    "\u0645\u06cc\u0632\u0627\u0646": ["\u0645\u06cc\u0632\u0627\u0646", "\u0645\u0642\u062f\u0627\u0631", "\u0646\u06cc\u0627\u0632", "how much", "duration", "hours"],
    "\u062a\u0646\u0638\u06cc\u0645": ["\u062a\u0646\u0638\u06cc\u0645 \u062e\u0648\u0627\u0628", "\u0628\u0631\u0646\u0627\u0645\u0647 \u062e\u0648\u0627\u0628", "sleep schedule", "sleep routine"],
})
RETRIEVAL_STOPWORDS.update({
    "\u0627\u0632", "\u0628\u0627", "\u0628\u0647", "\u0628\u0631\u0627\u06cc", "\u062f\u0631", "\u0631\u0627", "\u06a9\u0647", "\u0648", "\u06cc\u0627", "\u0627\u06cc\u0646", "\u0622\u0646",
    "\u0686\u06cc", "\u0686\u06cc\u0647", "\u0686\u0647", "\u0686\u0637\u0648\u0631", "\u0686\u06af\u0648\u0646\u0647", "\u0647\u0633\u062a", "\u0627\u0633\u062a", "\u062f\u0627\u0631\u062f", "\u062f\u0627\u0631\u062f\u061f", "\u062a\u0648\u0627\u0646\u0645",
})

# These words describe the conversational form of a question, not its subject.
# A title such as "will butter help a baby sleep" must not win simply because it
# repeats "child", "help", and "sleep" when the parent never mentioned butter.
RETRIEVAL_LOW_SIGNAL_TOKENS = {
    "\u06a9\u0648\u062f\u06a9", "\u06a9\u0648\u062f\u06a9\u0645", "\u0628\u0686\u0647", "\u0646\u0648\u0632\u0627\u062f", "\u0641\u0631\u0632\u0646\u062f",
    "\u06a9\u0645\u06a9", "\u0631\u0627\u0647", "\u0631\u0648\u0634", "\u0631\u0627\u062d\u062a", "\u0631\u0627\u062d\u062a\u062a\u0631", "\u062a\u0631",
    "\u0628\u0627\u0639\u062b", "\u0628\u0647\u062a\u0631", "\u0627\u0646\u062c\u0627\u0645", "\u0634\u0648\u062f", "\u0634\u062f\u0646",
}

TOKEN_CANONICAL_FORMS = {
    "\u0628\u062e\u0648\u0627\u0628\u062f": "\u062e\u0648\u0627\u0628",
    "\u0628\u062e\u0648\u0627\u0628\u0645": "\u062e\u0648\u0627\u0628",
    "\u0628\u062e\u0648\u0627\u0628\u0646": "\u062e\u0648\u0627\u0628",
    "\u062e\u0648\u0627\u0628\u06cc\u062f": "\u062e\u0648\u0627\u0628",
    "\u062e\u0648\u0627\u0628\u06cc\u062f\u0646": "\u062e\u0648\u0627\u0628",
    "\u062e\u0648\u0627\u0628\u0627\u0646\u062f\u0646": "\u062e\u0648\u0627\u0628",
    "\u062e\u0648\u0627\u0628\u0627\u0646\u062f": "\u062e\u0648\u0627\u0628",
    "\u0645\u06cc\u062e\u0648\u0627\u0628\u062f": "\u062e\u0648\u0627\u0628",
    "\u0645\u06cc\u062e\u0648\u0627\u0628\u0647": "\u062e\u0648\u0627\u0628",
}

PERSIAN_DIGITS = str.maketrans("\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9", "0123456789")


def normalize_liara_embedding_model(model: str) -> str:
    normalized = (model or "").strip()
    if not normalized:
        return "google/gemini-embedding-001"
    return normalized


def is_token_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "maximum allowed token limit" in message or "exceeds the maximum allowed token limit" in message


def normalize_query_text(text: str) -> str:
    normalized = (text or "").strip().lower()
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "آ": "ا",
        "\u200c": " ",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    # Persian punctuation lies in the same Unicode block as Persian letters;
    # remove it explicitly so «بخوابد؟» normalizes to «بخوابد».
    normalized = re.sub(r"[\u060c\u061b\u061f\u066a-\u066d]", " ", normalized)
    normalized = re.sub(r"[^\w\u0600-\u06FF\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def tokenize_query_text(text: str) -> list[str]:
    tokens = []
    for raw_token in normalize_query_text(text).split():
        token = TOKEN_CANONICAL_FORMS.get(raw_token, raw_token)
        if (
            len(token) > 1
            and token not in RETRIEVAL_STOPWORDS
            and token not in RETRIEVAL_LOW_SIGNAL_TOKENS
        ):
            tokens.append(token)
    return tokens


def _document_age_ranges_in_months(doc: Document) -> list[tuple[float, float]]:
    """Return explicit age labels in a document title, if it has any."""
    title = normalize_query_text(str(doc.metadata.get("title", ""))).translate(PERSIAN_DIGITS)
    ranges: list[tuple[float, float]] = []
    for lower, upper in re.findall(r"(?<!\d)(\d{1,2})\s*(?:تا|to|-|–|—)\s*(\d{1,2})\s*(?:ماهه?|months?)", title):
        start, end = float(lower), float(upper)
        if start <= end:
            ranges.append((start, end))

    # Examples: "برنامه خواب نوزاد 11 ماهه" or "11-month-old sleep".
    if not ranges:
        for month in re.findall(r"(?<!\d)(\d{1,2})\s*(?:ماهه?|month(?:s)? old)", title):
            ranges.append((float(month), float(month)))
    return ranges


def filter_documents_for_child_age(documents: list[Document], age_days: Optional[int]) -> list[Document]:
    """Drop clearly incompatible age-specific articles; retain general articles."""
    if age_days is None or age_days < 0:
        return documents

    age_months = age_days / 30.4375
    compatible = []
    for doc in documents:
        ranges = _document_age_ranges_in_months(doc)
        if not ranges or any(start - 0.25 <= age_months <= end + 0.25 for start, end in ranges):
            compatible.append(doc)
    return compatible


def score_document_heuristically(query: str, doc: Document) -> int:
    query_tokens = set(tokenize_query_text(query))
    if not query_tokens:
        return 0

    title = normalize_query_text(str(doc.metadata.get("title", "")))
    source = normalize_query_text(str(doc.metadata.get("source", "")))
    content = normalize_query_text(doc.page_content[:1200])

    title_tokens = set(title.split())
    source_tokens = set(source.split())
    content_tokens = set(content.split())

    title_overlap = len(query_tokens & title_tokens)
    source_overlap = len(query_tokens & source_tokens)
    content_overlap = len(query_tokens & content_tokens)

    feeding_query = "شیر" in query_tokens and bool(
        {"خورد", "خوره", "غذا", "تغذیه", "نخوردن", "بطری", "شیردهی"} & query_tokens
    )
    feeding_terms = {"شیر", "تغذیه", "غذا", "شیردهی", "بطری", "شیشه", "مکیدن"}
    feeding_hits = len(feeding_terms & title_tokens) + len(feeding_terms & content_tokens)

    if feeding_query and feeding_hits == 0:
        return 0

    phrase_bonus = 0
    if feeding_query:
        phrase_bonus += feeding_hits * 3

    if "شیر" in query_tokens:
        if "شیر" in title or "شیر" in content:
            phrase_bonus += 4
        if "تغذیه" in title or "تغذیه" in content:
            phrase_bonus += 3

    if "بی" in query_tokens and "قراری" in query_tokens:
        if "بی قراری" in title or "بی قراری" in content:
            phrase_bonus += 4

    if "۶" in query_tokens or "6" in query_tokens or "شش" in query_tokens:
        if "۶ ماه" in title or "۶ ماه" in content or "6 ماه" in title or "6 ماه" in content:
            phrase_bonus += 3

    if ("نمی" in query_tokens and ("خورد" in query_tokens or "خوره" in query_tokens)) or "نخوردن" in query_tokens:
        if (
            "نمی خورد" in content
            or "نمیخورد" in content
            or "کم می خورد" in content
            or "رد می کند" in content
            or "رد کردن شیر" in content
        ):
            phrase_bonus += 5

    if {"۶", "6", "شش"} & query_tokens:
        if "نوزاد" in title_tokens or "نوزاد" in content_tokens:
            phrase_bonus += 2

    # A parent asking for the amount of sleep needs a duration/need article,
    # not merely any page that happens to mention sleep or a sleep schedule.
    sleep_duration_query = "خواب" in query_tokens and bool(
        {"میزان", "مقدار", "نیاز", "ساعت", "چقدر"} & query_tokens
    )
    if sleep_duration_query:
        duration_terms = {"میزان", "مقدار", "نیاز", "ساعت"}
        duration_title_hits = len(duration_terms & title_tokens)
        duration_content_hits = len(duration_terms & content_tokens)
        phrase_bonus += (duration_title_hits * 8) + min(duration_content_hits, 3)

    # Unicode-safe sleep/duration scoring. It intentionally recognizes the
    # English article titles stored in the corpus for a Persian parent query.
    sleep_token = "\u062e\u0648\u0627\u0628"
    if sleep_token in query_tokens:
        sleep_terms = {sleep_token, "sleep", "sleeping", "bedtime", "nap", "naps"}
        sleep_hits = len(sleep_terms & title_tokens) + len(sleep_terms & content_tokens)
        if sleep_hits == 0:
            return 0
        phrase_bonus += sleep_hits * 4

        duration_query_tokens = {"\u0645\u06cc\u0632\u0627\u0646", "\u0645\u0642\u062f\u0627\u0631", "\u0646\u06cc\u0627\u0632", "\u0633\u0627\u0639\u062a", "\u0686\u0642\u062f\u0631"}
        if query_tokens & duration_query_tokens:
            duration_markers = {"\u0645\u06cc\u0632\u0627\u0646", "\u0645\u0642\u062f\u0627\u0631", "\u0646\u06cc\u0627\u0632", "\u0633\u0627\u0639\u062a", "need", "hours", "duration"}
            duration_hits = len(duration_markers & title_tokens) + len(duration_markers & content_tokens)
            if "how much" in title or "how much" in content:
                duration_hits += 3
            phrase_bonus += duration_hits * 8

    return (title_overlap * 5) + (source_overlap * 2) + content_overlap + phrase_bonus


def score_document_raw_fallback(query: str, doc: Document) -> int:
    raw_query = str(query or "").strip().lower()
    if not raw_query:
        return 0

    title = str(doc.metadata.get("title", "")).lower()
    source = str(doc.metadata.get("source", "")).lower()
    content = str(doc.page_content[:2000]).lower()
    compact_query = re.sub(r"\s+", " ", raw_query)
    query_parts = [part for part in re.split(r"\s+", compact_query) if len(part) >= 2]

    score = 0
    if compact_query and compact_query in title:
        score += 40
    if compact_query and compact_query in content:
        score += 20

    for part in query_parts:
        if part in title:
            score += 5
        if part in content:
            score += 2
        if part in source:
            score += 1

    if "لینک منبع:" in content:
        score += 1

    return score


def expand_retrieval_query(query: str) -> str:
    tokens = tokenize_query_text(query)
    expanded_tokens = []

    for token in tokens:
        if token not in expanded_tokens:
            expanded_tokens.append(token)

        for synonym in QUERY_SYNONYMS.get(token, []):
            synonym_tokens = tokenize_query_text(synonym)
            for synonym_token in synonym_tokens:
                if synonym_token not in expanded_tokens:
                    expanded_tokens.append(synonym_token)

    return " ".join(expanded_tokens) if expanded_tokens else query


def rerank_documents_heuristically(query: str, retrieved_docs: list[Document], top_n: int = 5) -> list[Document]:
    if not retrieved_docs:
        return []

    query_tokens = set(tokenize_query_text(query))
    if not query_tokens:
        return []

    scored_docs = []
    for index, doc in enumerate(retrieved_docs):
        title = normalize_query_text(str(doc.metadata.get("title", "")))
        source = normalize_query_text(str(doc.metadata.get("source", "")))
        content = normalize_query_text(doc.page_content[:1200])

        title_tokens = set(title.split())
        source_tokens = set(source.split())
        content_tokens = set(content.split())

        title_overlap = len(query_tokens & title_tokens)
        source_overlap = len(query_tokens & source_tokens)
        content_overlap = len(query_tokens & content_tokens)

        phrase_bonus = 0
        joined_query = " ".join(query_tokens)
        if "شیر" in query_tokens and ("نمی" in query_tokens or "نخوردن" in query_tokens):
            if "شیر" in title or "غذا" in title or "تغذیه" in title:
                phrase_bonus += 4
        if any(token in title for token in query_tokens):
            phrase_bonus += 2

        score = (title_overlap * 5) + (source_overlap * 2) + content_overlap + phrase_bonus
        scored_docs.append((score, index, doc))

    scored_docs.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    ranked_docs = [doc for score, _index, doc in scored_docs if score >= RAG_MIN_HEURISTIC_SCORE]
    if not ranked_docs:
        return []
    return ranked_docs[:top_n]


def rerank_documents_heuristically(query: str, retrieved_docs: list[Document], top_n: int = 5) -> list[Document]:
    if not retrieved_docs:
        return []

    scored_docs = []
    for index, doc in enumerate(retrieved_docs):
        score = score_document_heuristically(query, doc)
        scored_docs.append((score, index, doc))

    scored_docs.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    ranked_docs = [doc for score, _index, doc in scored_docs if score >= RAG_MIN_HEURISTIC_SCORE]
    if not ranked_docs:
        return []
    return ranked_docs[:top_n]


def lexical_fallback_search(query: str, documents: list[Document], top_n: int = 10) -> list[Document]:
    if not documents:
        return []

    scored_docs = []
    for index, doc in enumerate(documents):
        heuristic_score = score_document_heuristically(query, doc)
        raw_score = score_document_raw_fallback(query, doc)
        score = (heuristic_score * 3) + raw_score
        if score > 0:
            scored_docs.append((heuristic_score, score, index, doc))

    # Raw substring matches are useful for recall, but they can promote generic
    # words (for example "sleep") over a document whose title exactly matches
    # the parent's intent. Keep both candidate sets; final reranking decides.
    by_combined_score = sorted(scored_docs, key=lambda item: (item[1], -item[2]), reverse=True)
    by_heuristic_score = sorted(scored_docs, key=lambda item: (item[0], -item[2]), reverse=True)

    selected = []
    seen = set()
    for _heuristic_score, _score, _index, doc in [
        *by_combined_score[:top_n],
        *by_heuristic_score[:top_n],
    ]:
        key = (
            doc.metadata.get("source_file"),
            doc.metadata.get("title"),
            doc.metadata.get("url"),
            doc.page_content[:120],
        )
        if key in seen:
            continue
        seen.add(key)
        selected.append(doc)
    return selected


class RetrievalManager:
    """Retrieves with BM25 first, then semantically reranks only its candidates."""

    def __init__(self):
        self.keyword_retriever: BM25Retriever | None = None
        self.documents: list[Document] = []
        self.embeddings: Embeddings | None = self._load_embeddings()
        self._document_embedding_cache: OrderedDict[str, list[float]] = OrderedDict()

    def _load_embeddings(self) -> Embeddings | None:
        if not RAG_ENABLE_VECTOR_SEARCH:
            logger.info("Vector search is disabled; using BM25 plus lexical reranking.")
            return None

        base_url = os.getenv("LIARA_BASE_URL")
        api_key = os.getenv("LIARA_API_KEY")

        if not base_url or not api_key:
            raise RuntimeError("LIARA_BASE_URL or LIARA_API_KEY is not configured.")

        try:
            embeddings = LiaraEmbeddings(
                model=LIARA_EMBEDDING_MODEL,
                base_url=base_url,
                api_key=api_key,
            )
            logger.info("Liara embedding model '%s' loaded.", embeddings.model)
            return embeddings
        except Exception as e:
            logger.warning(
                "Liara embeddings are unavailable. RAG will continue with keyword retrieval: %s",
                e,
            )
            return None

    def setup_retrievers(self, documents: list[Document]):
        self.documents = documents

        logger.info("Creating BM25 candidate retriever (top %s).", RAG_BM25_CANDIDATE_K)
        self.keyword_retriever = BM25Retriever.from_documents(documents)
        self.keyword_retriever.k = RAG_BM25_CANDIDATE_K

        if not self.embeddings:
            logger.warning(
                "Semantic reranking is unavailable because Liara embeddings could not be loaded. "
                "Using BM25 candidates only."
            )
            return

        logger.info(
            "Semantic reranking takes the top %s of %s BM25 candidates and returns %s documents; no full FAISS index is built.",
            RAG_SEMANTIC_CANDIDATE_K,
            RAG_BM25_CANDIDATE_K,
            RAG_SEMANTIC_RERANK_K,
        )

    @staticmethod
    def _document_cache_key(doc: Document) -> str:
        raw_key = "\x1f".join(
            [
                str(doc.metadata.get("source_file", "")),
                str(doc.metadata.get("title", "")),
                str(doc.metadata.get("url", "")),
                doc.page_content,
            ]
        )
        return hashlib.blake2s(raw_key.encode("utf-8"), digest_size=16).hexdigest()

    def _document_source_key(self, doc: Document) -> tuple[str, str]:
        """Identify an article independently of the chunk selected from it."""
        metadata = doc.metadata or {}
        url = str(metadata.get("url") or metadata.get("reference_url") or "").strip().casefold()
        if url:
            return ("url", url)
        source_file = str(metadata.get("source_file") or "").strip().casefold()
        if source_file:
            return ("file", source_file)
        title = str(metadata.get("title") or "").strip().casefold()
        return ("fallback", title or self._document_cache_key(doc))

    @staticmethod
    def _document_embedding_text(doc: Document) -> str:
        title = str(doc.metadata.get("title", "")).strip()
        source = str(doc.metadata.get("source", "")).strip()
        content = doc.page_content[:RAG_SEMANTIC_DOCUMENT_CHARS]
        return f"Title: {title}\nSource: {source}\nContent: {content}"

    def _cache_document_embedding(self, cache_key: str, embedding: list[float]):
        self._document_embedding_cache[cache_key] = embedding
        self._document_embedding_cache.move_to_end(cache_key)
        while len(self._document_embedding_cache) > RAG_SEMANTIC_CACHE_SIZE:
            self._document_embedding_cache.popitem(last=False)

    def _candidate_embeddings(self, candidates: list[Document]) -> dict[str, list[float]]:
        if not self.embeddings:
            return {}

        embeddings_by_key: dict[str, list[float]] = {}
        missing_keys: list[str] = []
        missing_texts: list[str] = []
        for doc in candidates:
            cache_key = self._document_cache_key(doc)
            cached_embedding = self._document_embedding_cache.get(cache_key)
            if cached_embedding is not None:
                self._document_embedding_cache.move_to_end(cache_key)
                embeddings_by_key[cache_key] = cached_embedding
                continue
            missing_keys.append(cache_key)
            missing_texts.append(self._document_embedding_text(doc))

        if missing_texts:
            fresh_embeddings = self.embeddings.embed_documents(missing_texts)
            for cache_key, embedding in zip(missing_keys, fresh_embeddings):
                self._cache_document_embedding(cache_key, embedding)
                embeddings_by_key[cache_key] = embedding

        return embeddings_by_key

    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        numerator = sum(left * right for left, right in zip(first, second))
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        if not first_norm or not second_norm:
            return -1.0
        return numerator / (first_norm * second_norm)

    def _semantic_rerank(
        self,
        query: str,
        candidates: list[Document],
        *,
        relevance_query: str | None = None,
    ) -> list[Document]:
        if not self.embeddings or not candidates:
            return candidates

        try:
            query_embedding = self.embeddings.embed_query(query)
            embeddings_by_key = self._candidate_embeddings(candidates)
            scored = []
            for index, doc in enumerate(candidates):
                embedding = embeddings_by_key.get(self._document_cache_key(doc))
                if embedding is not None:
                    scored.append((self._cosine_similarity(query_embedding, embedding), index, doc))

            scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)

            # Keep a small lexical-relevance guard from the same BM25 pool.
            # The query bridge can be broader than the parent's wording, and a
            # purely semantic score can otherwise replace an exact article
            # (for example, "how much sleep") with a broadly similar one.
            guard_query = relevance_query or query
            lexical_guards = sorted(
                (
                    (score_document_heuristically(guard_query, doc), index, doc)
                    for index, doc in enumerate(candidates)
                ),
                key=lambda item: (item[0], -item[1]),
                reverse=True,
            )
            selected: list[Document] = []
            selected_keys = set()
            selected_source_keys = set()

            for score, _index, doc in lexical_guards:
                if score < RAG_MIN_HEURISTIC_SCORE or len(selected) >= RAG_LEXICAL_GUARD_K:
                    break
                cache_key = self._document_cache_key(doc)
                source_key = self._document_source_key(doc)
                if cache_key not in selected_keys and source_key not in selected_source_keys:
                    selected.append(doc)
                    selected_keys.add(cache_key)
                    selected_source_keys.add(source_key)

            for _score, _index, doc in scored:
                if len(selected) >= RAG_SEMANTIC_RERANK_K:
                    break
                cache_key = self._document_cache_key(doc)
                source_key = self._document_source_key(doc)
                if cache_key not in selected_keys and source_key not in selected_source_keys:
                    selected.append(doc)
                    selected_keys.add(cache_key)
                    selected_source_keys.add(source_key)

            logger.info(
                "Semantic reranked %s BM25 candidates to %s documents (%s lexical guards).",
                len(candidates),
                len(selected),
                min(len(selected), RAG_LEXICAL_GUARD_K),
            )
            return selected or candidates
        except Exception as exc:
            logger.warning("Semantic reranking failed; continuing with BM25 candidates: %s", exc)
            return candidates

    def retrieve_documents(
        self,
        query: str,
        *,
        relevance_query: str | None = None,
        child_age_days: Optional[int] = None,
    ) -> list[Document]:
        if not self.keyword_retriever:
            raise RuntimeError("Retrieval system is not ready.")

        candidates = self.keyword_retriever.invoke(query)
        # Apply the age guard before semantic reranking.  Applying it only after
        # semantic top-k selection can discard the good age-matched chunk while
        # leaving no slot for it to be considered.
        candidates = filter_documents_for_child_age(candidates, child_age_days)
        semantic_candidates = candidates[:RAG_SEMANTIC_CANDIDATE_K]
        return self._semantic_rerank(query, semantic_candidates, relevance_query=relevance_query)


class LiaraEmbeddings(Embeddings):
    def __init__(self, *, model: str, base_url: str, api_key: str):
        requested_model = normalize_liara_embedding_model(model)
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=LIARA_EMBEDDING_TIMEOUT_SECONDS,
            max_retries=2,
        )
        self.model = self._resolve_working_model(requested_model)

    def _candidate_models(self, requested_model: str) -> list[str]:
        candidates = []

        def add(candidate: str):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        add(requested_model)

        if requested_model.startswith("openai/"):
            add(requested_model.split("/", 1)[1])
        elif requested_model.startswith("google/"):
            add(requested_model.split("/", 1)[1])
        else:
            openai_aliases = {
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            }
            google_aliases = {
                "gemini-embedding-001",
            }
            if requested_model in openai_aliases:
                add(f"openai/{requested_model}")
            if requested_model in google_aliases:
                add(f"google/{requested_model}")

        add("text-embedding-3-small")
        add("text-embedding-3-large")
        add("text-embedding-ada-002")

        return candidates

    def _resolve_working_model(self, requested_model: str) -> str:
        last_error = None

        for candidate in self._candidate_models(requested_model):
            try:
                response = self.client.embeddings.create(
                    model=candidate,
                    input=["model probe"],
                    # Liara's Google embedding endpoint rejects the OpenAI
                    # client's default base64 response format.
                    encoding_format="float",
                )
                _ = response.data[0].embedding
                if candidate != requested_model:
                    logger.warning(
                        "Configured Liara embedding model '%s' was not accepted. Using '%s' instead.",
                        requested_model,
                        candidate,
                    )
                return candidate
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            f"No working Liara embedding model found for configured value '{requested_model}'."
        ) from last_error

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        last_error = None

        for attempt in range(1, LIARA_EMBEDDING_MAX_RETRIES + 2):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float",
                )
                return [item.embedding for item in response.data]
            except Exception as exc:
                if is_token_limit_error(exc):
                    if len(texts) == 1:
                        raise RuntimeError(
                            "A single text chunk exceeded Liara's embedding token limit. "
                            "Reduce CHUNK_SIZE in process.py."
                        ) from exc

                    midpoint = max(1, len(texts) // 2)
                    logger.warning(
                        "Liara embedding batch hit token limit with %s texts. Splitting into %s and %s.",
                        len(texts),
                        midpoint,
                        len(texts) - midpoint,
                    )
                    return self._embed_batch(texts[:midpoint]) + self._embed_batch(texts[midpoint:])

                status_code = getattr(exc, "status_code", None)
                if status_code is not None and 400 <= status_code < 500 and status_code != 429:
                    raise

                last_error = exc
                if attempt > LIARA_EMBEDDING_MAX_RETRIES:
                    break

                delay_seconds = LIARA_EMBEDDING_RETRY_DELAY_SECONDS * attempt
                logger.warning(
                    "Liara embedding batch failed for %s texts (attempt %s/%s): %s. Retrying in %.1fs.",
                    len(texts),
                    attempt,
                    LIARA_EMBEDDING_MAX_RETRIES + 1,
                    exc,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

        raise RuntimeError(
            f"Liara embedding batch failed after {LIARA_EMBEDDING_MAX_RETRIES + 1} attempts."
        ) from last_error

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings = []
        total_texts = len(texts)
        progress_interval = max(LIARA_EMBEDDING_BATCH_SIZE * 10, 512)

        for start_index in range(0, total_texts, LIARA_EMBEDDING_BATCH_SIZE):
            batch = texts[start_index : start_index + LIARA_EMBEDDING_BATCH_SIZE]
            all_embeddings.extend(self._embed_batch(batch))

            processed_count = start_index + len(batch)
            if processed_count == total_texts or processed_count % progress_interval == 0:
                logger.info(
                    "Liara embeddings progress: %s/%s chunks processed.",
                    processed_count,
                    total_texts,
                )

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]


def load_cross_encoder_model() -> Optional["CrossEncoder"]:
    if not RAG_ENABLE_RERANKER:
        logger.info("RAG reranker is disabled. Skipping cross-encoder load.")
        return None

    try:
        from sentence_transformers.cross_encoder import CrossEncoder

        model = CrossEncoder(CROSS_ENCODER_MODEL)
        logger.info(f"Cross-encoder model '{CROSS_ENCODER_MODEL}' loaded.")
        return model
    except Exception as e:
        logger.error(f"Failed to load cross-encoder model '{CROSS_ENCODER_MODEL}': {e}", exc_info=True)
        raise RuntimeError("Could not load cross-encoder model") from e


def re_rank_documents(
    cross_encoder: "CrossEncoder",
    query: str,
    retrieved_docs: list[Document],
    top_n: int = 5,
) -> list[Document]:
    if not retrieved_docs or not cross_encoder:
        return retrieved_docs

    pairs = [[query, doc.page_content] for doc in retrieved_docs]
    scores = cross_encoder.predict(pairs)

    doc_scores = sorted(zip(retrieved_docs, scores), key=lambda x: x[1], reverse=True)
    ranked_docs = [doc for doc, _score in doc_scores[:top_n]]
    logger.info("Re-ranked %s docs, selected top %s.", len(retrieved_docs), len(ranked_docs))
    return ranked_docs
