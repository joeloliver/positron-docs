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
        
        try:
            # Fetch content
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
                
            # Extract main content
            extracted = trafilatura.extract(response.text)
            
            if extracted:
                content_chunks = self._chunk_text(extracted)
                for chunk in content_chunks:
                    chunks.append(chunk)
                    metadatas.append({
                        "source": url,
                        "type": "web"
                    })
            else:
                # Fallback to BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                content_chunks = self._chunk_text(text)
                for chunk in content_chunks:
                    chunks.append(chunk)
                    metadatas.append({
                        "source": url,
                        "type": "web"
                    })
        except Exception as e:
            logger.error(f"Error processing URL: {e}")
            raise
        
        return chunks, metadatas
    
    def extract_pdf_links(self, url: str) -> List[str]:
        """Extract PDF links from a webpage"""
        pdf_links = []
        
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.lower().endswith('.pdf'):
                    # Make absolute URL
                    if href.startswith('http'):
                        pdf_links.append(href)
                    elif href.startswith('/'):
                        from urllib.parse import urljoin
                        pdf_links.append(urljoin(url, href))
        except Exception as e:
            logger.error(f"Error extracting PDF links: {e}")
        
        return pdf_links
    
    def process_text(self, text: str, source: str = "text") -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process plain text and return chunks with metadata"""
        chunks = self._chunk_text(text)
        metadatas = [{"source": source, "type": "text"} for _ in chunks]
        return chunks, metadatas
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a sentence boundary
            if end < len(text):
                # Look for sentence end
                for sep in ['. ', '! ', '? ', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + len(sep) - 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap if end < len(text) else end
        
        return chunks