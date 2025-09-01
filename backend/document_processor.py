from typing import List, Dict, Any, Tuple
import pypdf
import trafilatura
from bs4 import BeautifulSoup
import httpx
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def process_pdf(self, file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process PDF file and return chunks with metadata"""
        chunks = []
        metadatas = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        page_chunks = self._chunk_text(text)
                        for chunk in page_chunks:
                            chunks.append(chunk)
                            metadatas.append({
                                "page": page_num,
                                "source": Path(file_path).name,
                                "type": "pdf"
                            })
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
        
        return chunks, metadatas
    
    def process_url(self, url: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process URL content and return chunks with metadata"""
        chunks = []
        metadatas = []
        
        logger.debug(f"[process_url] Starting to process: {url}")
        
        try:
            # Fetch content with timeout
            logger.debug(f"[process_url] Creating HTTP client with 30s timeout")
            with httpx.Client(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                logger.debug(f"[process_url] Sending GET request to {url}")
                response = client.get(url, follow_redirects=True, headers=headers)
                logger.debug(f"[process_url] Response status: {response.status_code}")
                logger.debug(f"[process_url] Response content length: {len(response.text)} chars")
                response.raise_for_status()
                
            # Extract main content - SKIP TRAFILATURA FOR NOW TO ISOLATE ISSUE
            logger.debug(f"[process_url] SKIPPING trafilatura for debugging - using BeautifulSoup directly")
            extracted = None
            
            # logger.debug(f"[process_url] About to call trafilatura.extract() on {len(response.text)} chars")
            # try:
            #     extracted = trafilatura.extract(response.text)
            #     logger.debug(f"[process_url] Trafilatura extract() completed")
            #     logger.debug(f"[process_url] Trafilatura extracted: {len(extracted) if extracted else 0} chars")
            # except Exception as e:
            #     logger.error(f"[process_url] Error during trafilatura extraction: {e}", exc_info=True)
            #     extracted = None
            
            if extracted:
                logger.debug(f"[process_url] Chunking extracted text")
                content_chunks = self._chunk_text(extracted)
                logger.debug(f"[process_url] Created {len(content_chunks)} chunks from trafilatura")
                logger.debug(f"[process_url] Adding trafilatura chunks to return arrays")
                for i, chunk in enumerate(content_chunks):
                    chunks.append(chunk)
                    metadatas.append({
                        "source": url,
                        "type": "web"
                    })
                logger.debug(f"[process_url] Finished adding {len(content_chunks)} trafilatura chunks")
            else:
                # Fallback to BeautifulSoup
                logger.debug(f"[process_url] Using BeautifulSoup fallback")
                logger.debug(f"[process_url] Creating BeautifulSoup parser")
                soup = BeautifulSoup(response.text, 'html.parser')
                logger.debug(f"[process_url] BeautifulSoup parser created successfully")
                
                logger.debug(f"[process_url] Extracting text with get_text()")
                text = soup.get_text(separator=' ', strip=True)
                logger.debug(f"[process_url] BeautifulSoup extracted: {len(text)} chars")
                
                logger.debug(f"[process_url] About to chunk text")
                content_chunks = self._chunk_text(text)
                logger.debug(f"[process_url] Created {len(content_chunks)} chunks from BeautifulSoup")
                
                logger.debug(f"[process_url] Adding BeautifulSoup chunks to return arrays")
                for i, chunk in enumerate(content_chunks):
                    chunks.append(chunk)
                    metadatas.append({
                        "source": url,
                        "type": "web"
                    })
                logger.debug(f"[process_url] Finished adding {len(content_chunks)} BeautifulSoup chunks")
        except httpx.TimeoutException as e:
            logger.error(f"[process_url] Timeout error fetching {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"[process_url] HTTP error fetching {url}: Status {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"[process_url] Unexpected error processing URL {url}: {e}", exc_info=True)
            raise
        
        logger.debug(f"[process_url] Completed processing {url}: {len(chunks)} total chunks")
        return chunks, metadatas
    
    def extract_pdf_links(self, url: str) -> List[str]:
        """Extract PDF links from a webpage"""
        pdf_links = []
        seen_urls = set()
        
        logger.debug(f"[extract_pdf_links] Starting PDF link extraction from: {url}")
        
        try:
            logger.debug(f"[extract_pdf_links] Fetching page content")
            with httpx.Client(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = client.get(url, follow_redirects=True, headers=headers)
                logger.debug(f"[extract_pdf_links] Response status: {response.status_code}")
                response.raise_for_status()
            
            logger.debug(f"[extract_pdf_links] Parsing HTML with BeautifulSoup")
            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a', href=True)
            logger.debug(f"[extract_pdf_links] Found {len(all_links)} total links on page")
            
            # Find all links
            for i, link in enumerate(all_links):
                href = link['href']
                link_text = link.get_text().strip()
                
                # Only log every 10th link to reduce noise, or if it's a potential PDF
                if i % 10 == 0:
                    logger.debug(f"[extract_pdf_links] Progress: Checking link {i+1}/{len(all_links)}")
                
                # Check for PDF indicators
                is_pdf = False
                reason = ""
                
                # Check if URL ends with .pdf
                if href.lower().endswith('.pdf'):
                    is_pdf = True
                    reason = "URL ends with .pdf"
                
                # Check if URL contains PDF indicators
                elif any(indicator in href.lower() for indicator in ['pdf', 'download', 'document']):
                    # Check link text for PDF mentions
                    link_text_lower = link_text.lower()
                    if any(word in link_text_lower for word in ['pdf', 'download', 'document', 'file']):
                        is_pdf = True
                        reason = f"URL contains PDF indicator and text contains: {link_text[:30]}"
                
                # Check for common PDF URL patterns
                elif re.search(r'/files?/|/documents?/|/downloads?/', href.lower()):
                    is_pdf = True
                    reason = "URL matches common PDF pattern"
                
                if is_pdf:
                    logger.debug(f"[extract_pdf_links] PDF detected! Reason: {reason}")
                    # Make absolute URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        from urllib.parse import urljoin
                        full_url = urljoin(url, href)
                    else:
                        from urllib.parse import urljoin
                        full_url = urljoin(url, href)
                    
                    # Avoid duplicates
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        pdf_links.append(full_url)
                        logger.info(f"[extract_pdf_links] Added PDF link: {full_url}")
                    else:
                        logger.debug(f"[extract_pdf_links] Skipping duplicate: {full_url}")
        except httpx.TimeoutException as e:
            logger.error(f"[extract_pdf_links] Timeout fetching {url}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"[extract_pdf_links] HTTP error fetching {url}: Status {e.response.status_code}")
        except Exception as e:
            logger.error(f"[extract_pdf_links] Unexpected error extracting PDF links from {url}: {e}", exc_info=True)
        
        logger.info(f"[extract_pdf_links] Completed: Found {len(pdf_links)} potential PDF links on {url}")
        if pdf_links:
            logger.info(f"[extract_pdf_links] PDF URLs: {pdf_links}")
        return pdf_links
    
    def process_text(self, text: str, source: str = "text") -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process plain text and return chunks with metadata"""
        chunks = self._chunk_text(text)
        metadatas = [{"source": source, "type": "text"} for _ in chunks]
        return chunks, metadatas
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks - FIXED VERSION"""
        logger.debug(f"[_chunk_text] Starting to chunk {len(text)} chars")
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        logger.debug(f"[_chunk_text] After cleaning: {len(text)} chars")
        
        if len(text) <= self.chunk_size:
            logger.debug(f"[_chunk_text] Text small enough, returning single chunk")
            return [text] if text else []
        
        chunks = []
        start = 0
        iteration = 0
        
        while start < len(text):
            iteration += 1
            if iteration > 1000:  # Safety break to prevent infinite loops
                logger.error(f"[_chunk_text] Breaking infinite loop after 1000 iterations")
                break
                
            if iteration % 100 == 0:  # Progress logging
                logger.debug(f"[_chunk_text] Progress: iteration {iteration}, start={start}, len(text)={len(text)}")
            
            end = start + self.chunk_size
            
            # Try to find a sentence boundary
            if end < len(text):
                # Look for sentence end
                for sep in ['. ', '! ', '? ', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + len(sep)  # FIXED: removed -1 that was causing issues
                        break
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) > 10:  # Only add substantial chunks
                chunks.append(chunk)
            
            # FIXED: Ensure we always make progress
            new_start = end - self.overlap if end < len(text) else end
            if new_start <= start:  # Prevent going backwards
                new_start = start + 1
            start = new_start
            
            # Safety check
            if start >= len(text):
                break
        
        logger.debug(f"[_chunk_text] Completed chunking: {len(chunks)} chunks created")
        return chunks