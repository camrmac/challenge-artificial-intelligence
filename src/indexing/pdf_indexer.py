"""Indexador de arquivos PDF."""

import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer
import numpy as np
import re


class PDFIndexer:
    """Indexador para arquivos PDF."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa o indexador com modelo de embeddings."""
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = []
        self.metadata = []
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto extraído do PDF."""
        # Remove caracteres especiais e normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.,!?;:\-\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=]', ' ', text)
        text = text.strip()
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
        """Divide texto em chunks menores para melhor indexação."""
        # Para PDFs, usamos chunks maiores devido à natureza do conteúdo
        sentences = re.split(r'[.!?]+\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_length + sentence_words > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Mantém overlap
                overlap_sentences = current_chunk[-overlap//20:] if len(current_chunk) > overlap//20 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_words
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_text_pypdf2(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extrai texto usando PyPDF2."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text = ""
                metadata = {
                    'total_pages': len(pdf_reader.pages),
                    'extractor': 'PyPDF2'
                }
                
                # Adiciona metadados do PDF se disponíveis
                if pdf_reader.metadata:
                    pdf_metadata = pdf_reader.metadata
                    metadata.update({
                        'title': pdf_metadata.get('/Title', ''),
                        'author': pdf_metadata.get('/Author', ''),
                        'subject': pdf_metadata.get('/Subject', ''),
                        'creator': pdf_metadata.get('/Creator', ''),
                    })
                
                # Extrai texto de todas as páginas
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n[Página {page_num}]\n" + page_text
                    except Exception as e:
                        print(f"Erro ao extrair página {page_num}: {str(e)}")
                
                return text, metadata
                
        except Exception as e:
            print(f"Erro com PyPDF2 em {file_path}: {str(e)}")
            return "", {}
    
    def extract_text_pdfplumber(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extrai texto usando pdfplumber (melhor para layouts complexos)."""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                metadata = {
                    'total_pages': len(pdf.pages),
                    'extractor': 'pdfplumber'
                }
                
                # Adiciona metadados do PDF se disponíveis
                if pdf.metadata:
                    metadata.update({
                        'title': pdf.metadata.get('Title', ''),
                        'author': pdf.metadata.get('Author', ''),
                        'subject': pdf.metadata.get('Subject', ''),
                        'creator': pdf.metadata.get('Creator', ''),
                    })
                
                # Extrai texto de todas as páginas
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Adiciona informação da tabela se existir
                            tables = page.extract_tables()
                            if tables:
                                table_text = self._process_tables(tables)
                                page_text += f"\n[Tabelas da página {page_num}]\n{table_text}"
                            
                            text += f"\n[Página {page_num}]\n" + page_text
                    except Exception as e:
                        print(f"Erro ao extrair página {page_num}: {str(e)}")
                
                return text, metadata
                
        except Exception as e:
            print(f"Erro com pdfplumber em {file_path}: {str(e)}")
            return "", {}
    
    def _process_tables(self, tables: List[List[List[str]]]) -> str:
        """Converte tabelas extraídas em texto estruturado."""
        table_texts = []
        
        for i, table in enumerate(tables, 1):
            if not table:
                continue
                
            table_text = f"Tabela {i}:\n"
            for row in table:
                if row:  # Verifica se a linha não está vazia
                    clean_row = [cell if cell is not None else "" for cell in row]
                    table_text += " | ".join(clean_row) + "\n"
            
            table_texts.append(table_text)
        
        return "\n".join(table_texts)
    
    def extract_text(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extrai texto do PDF usando o melhor método disponível."""
        # Tenta primeiro com pdfplumber (melhor para layouts complexos)
        text, metadata = self.extract_text_pdfplumber(file_path)
        
        # Se não conseguiu extrair muito texto, tenta com PyPDF2
        if len(text.strip()) < 100:
            text_pypdf2, metadata_pypdf2 = self.extract_text_pypdf2(file_path)
            if len(text_pypdf2.strip()) > len(text.strip()):
                text, metadata = text_pypdf2, metadata_pypdf2
        
        return text, metadata
    
    def index_file(self, file_path: str) -> bool:
        """Indexa um arquivo PDF."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            return False
        
        if file_path.suffix.lower() != '.pdf':
            print(f"Arquivo não é PDF: {file_path}")
            return False
        
        # Extrai texto do PDF
        text, pdf_metadata = self.extract_text(file_path)
        
        if not text.strip():
            print(f"Não foi possível extrair texto de {file_path}")
            return False
        
        # Limpa e divide o texto em chunks
        cleaned_text = self.clean_text(text)
        chunks = self.chunk_text(cleaned_text)
        
        if not chunks:
            print(f"Não foi possível criar chunks de {file_path}")
            return False
        
        # Cria documentos para indexação
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                'content': chunk,
                'source': str(file_path),
                'type': 'pdf',
                'chunk_index': i,
                'total_chunks': len(chunks),
                **pdf_metadata
            }
            documents.append(doc_metadata)
        
        # Gera embeddings para os chunks
        contents = [doc['content'] for doc in documents]
        embeddings = self.model.encode(contents, convert_to_tensor=True)
        
        # Armazena documentos, embeddings e metadados
        self.documents.extend(contents)
        self.embeddings.extend(embeddings.cpu().numpy())
        self.metadata.extend(documents)
        
        print(f"Indexados {len(documents)} chunks de {file_path.name}")
        print(f"  - Total de páginas: {pdf_metadata.get('total_pages', 'N/A')}")
        print(f"  - Extrator usado: {pdf_metadata.get('extractor', 'N/A')}")
        
        return True
    
    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """Busca por similaridade semântica nos PDFs indexados."""
        if not self.embeddings:
            return []
        
        # Gera embedding da consulta
        query_embedding = self.model.encode([query], convert_to_tensor=True)
        
        # Calcula similaridades
        embeddings_array = np.array(self.embeddings)
        similarities = np.dot(embeddings_array, query_embedding.cpu().numpy().T).flatten()
        
        # Filtra resultados por similaridade mínima
        valid_indices = np.where(similarities >= min_similarity)[0]
        
        if len(valid_indices) == 0:
            return []
        
        # Ordena por similaridade
        valid_similarities = similarities[valid_indices]
        sorted_indices = np.argsort(valid_similarities)[::-1][:top_k]
        
        results = []
        for idx in sorted_indices:
            original_idx = valid_indices[idx]
            results.append({
                'content': self.documents[original_idx],
                'similarity': float(similarities[original_idx]),
                'metadata': self.metadata[original_idx]
            })
        
        return results
    
    def search_by_page(self, query: str, page_number: int = None) -> List[Dict[str, Any]]:
        """Busca específica por página."""
        if page_number is None:
            return self.search(query)
        
        # Filtra resultados por página específica
        page_results = []
        for i, meta in enumerate(self.metadata):
            content = self.documents[i]
            if f"[Página {page_number}]" in content:
                page_results.append({
                    'content': content,
                    'metadata': meta
                })
        
        return page_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da indexação."""
        files = set(meta['source'] for meta in self.metadata)
        total_pages = sum(meta.get('total_pages', 0) for meta in self.metadata)
        
        return {
            'total_documents': len(self.documents),
            'total_files': len(files),
            'total_pages': total_pages,
            'files_processed': list(files),
            'average_chunks_per_file': len(self.documents) / len(files) if files else 0
        } 