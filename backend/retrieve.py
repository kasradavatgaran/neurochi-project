import os
import logging
import shutil 
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS as LangchainFAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers.cross_encoder import CrossEncoder
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from dotenv import load_dotenv
VECTOR_DB_PATH = "faiss_index"
GEMINI_EMBEDDING_MODEL = "models/embedding-001" 
CROSS_ENCODER_MODEL = 'safora/reranker-xlm-roberta-large'
load_dotenv()
logger = logging.getLogger("rag_service.retrieve")

class RetrievalManager:
    """Manages the creation and operation of document retrieval systems."""
    def __init__(self):
        self.db: LangchainFAISS | None = None
        self.embeddings: GoogleGenerativeAIEmbeddings | None = self._load_embeddings()
        self.ensemble_retriever: EnsembleRetriever | None = None

    def _load_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        try:


            embeddings = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                task_type="retrieval_document" 
            )
            logger.info(f"Gemini Embedding model '{GEMINI_EMBEDDING_MODEL}' loaded.")
            return embeddings
        except Exception as e:
            logger.critical(f"FATAL: Failed to load Gemini embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Could not load embedding model") from e

    def setup_retrievers(self, documents: list[Document]):
        if not self.embeddings:
            raise RuntimeError("Embeddings are not loaded, cannot setup retrievers.")

        faiss_retriever = None

        if os.path.exists(VECTOR_DB_PATH) and os.listdir(VECTOR_DB_PATH):
            logger.info(f"Checking existing FAISS index at: {VECTOR_DB_PATH}")
            try:

                self.db = LangchainFAISS.load_local(
                    folder_path=VECTOR_DB_PATH, 
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )

                faiss_retriever = self.db.as_retriever(search_kwargs={"k": 10})
                logger.info("FAISS index loaded successfully.")
            except Exception as e:
                logger.warning(f"Existing index is incompatible or corrupt (likely different model): {e}. Rebuilding...")
                faiss_retriever = None 

        if not faiss_retriever:
            logger.info(f"Creating new FAISS index with GEMINI for {len(documents)} chunks.")
            try:

                

                self.db = LangchainFAISS.from_documents(documents, self.embeddings)
                
                if os.path.exists(VECTOR_DB_PATH):
                    shutil.rmtree(VECTOR_DB_PATH) 
                os.makedirs(VECTOR_DB_PATH, exist_ok=True) 
                
                self.db.save_local(VECTOR_DB_PATH) 
                
                faiss_retriever = self.db.as_retriever(search_kwargs={"k": 10})
                logger.info(f"FAISS index created and SAVED to: {VECTOR_DB_PATH}")
            except Exception as e:
                logger.error(f"Failed to create/save FAISS index: {e}", exc_info=True)
                raise RuntimeError("Failed to create FAISS index.") from e

        logger.info("Creating BM25 (keyword) retriever.")
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = 10

        # 4. Ensemble
        logger.info("Combining retrievers for Hybrid Search.")
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever], 
            weights=[0.5, 0.5]
        )
        
    def retrieve_documents(self, query: str) -> list[Document]:
        if not self.ensemble_retriever:
            raise RuntimeError("Retrieval system is not ready.")
        

        return self.ensemble_retriever.invoke(query)

def load_cross_encoder_model() -> CrossEncoder:
    """Loads the cross-encoder model for re-ranking."""
    try:
        model = CrossEncoder(CROSS_ENCODER_MODEL)
        logger.info(f"Cross-encoder model '{CROSS_ENCODER_MODEL}' loaded.")
        return model
    except Exception as e:
        logger.critical(f"FATAL: Failed to load cross-encoder model: {e}", exc_info=True)
        raise RuntimeError("Could not load cross-encoder model") from e

def re_rank_documents(cross_encoder: CrossEncoder, query: str, retrieved_docs: list[Document], top_n: int = 5) -> list[Document]:
    """Re-ranks documents using the cross-encoder model."""
    if not retrieved_docs or not cross_encoder:
        return retrieved_docs 
        
    pairs = [[query, doc.page_content] for doc in retrieved_docs]
    scores = cross_encoder.predict(pairs)
    
    doc_scores = sorted(zip(retrieved_docs, scores), key=lambda x: x[1], reverse=True)
    
    ranked_docs = [doc for doc, score in doc_scores[:top_n]]
    logger.info(f"Re-ranked {len(retrieved_docs)} docs, selected top {len(ranked_docs)}.")
    return ranked_docs