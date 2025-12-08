import os
import logging
import re  
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHUNK_SIZE = 1000  
CHUNK_OVERLAP = 200
TEXT_DIRECTORY = "./farsi_translations"

logger = logging.getLogger("rag_service.process")

def extract_metadata_from_content(content: str, filename: str):
    """
    عنوان و لینک را از متن استخراج می‌کند.
    """
    metadata = {}
    

    url_pattern = r"لینک مقاله اصلی:\s*(https?://\S+)"
    url_match = re.search(url_pattern, content)
    
    if url_match:
        metadata['url'] = url_match.group(1).strip()
    else:
        metadata['url'] = ""


    lines = [line.strip() for line in content.split('\n') if line.strip()]
    if lines:
        metadata['title'] = lines[0]
    else:
        metadata['title'] = filename 

    metadata['source'] = 'نوروچی' 
    metadata['source_file'] = filename
    
    return metadata

def process_all_txts_in_directory() -> list[Document]:
    all_chunks = []
    
    if not os.path.isdir(TEXT_DIRECTORY):
        msg = f"Directory not found: {TEXT_DIRECTORY}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    txt_files = [f for f in os.listdir(TEXT_DIRECTORY) if f.lower().endswith('.txt')]
    
    if not txt_files:
        msg = f"No .txt files found in directory: {TEXT_DIRECTORY}"
        logger.warning(msg)
        raise ValueError(msg)

    logger.info(f"Found {len(txt_files)} .txt file(s) to process.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for txt_file in txt_files:
        file_path = os.path.join(TEXT_DIRECTORY, txt_file)
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            raw_documents = loader.load() 
            
            if not raw_documents:
                continue

            primary_doc = raw_documents[0]
            extracted_meta = extract_metadata_from_content(primary_doc.page_content, txt_file)
            
            primary_doc.metadata.update(extracted_meta)
            

            chunks_from_file = text_splitter.split_documents([primary_doc])
            
            all_chunks.extend(chunks_from_file)
            logger.info(f"Processed '{txt_file}' | Title: {extracted_meta['title']} | Chunks: {len(chunks_from_file)}")
            
        except Exception as e:
            logger.error(f"Failed to process file '{txt_file}': {e}", exc_info=True)
            continue
            
    return all_chunks