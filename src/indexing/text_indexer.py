"""Indexador de arquivos de texto simples."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer
import numpy as np


class TextIndexer:
    """Indexador para arquivos de texto (.txt, .json)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa o indexador com modelo de embeddings."""
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = []
        self.metadata = []
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto."""
        # Remove caracteres especiais e normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Divide texto em chunks menores para melhor indexação."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
                
        return chunks
    
    def process_txt_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Processa arquivo .txt."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_content = self.clean_text(content)
            chunks = self.chunk_text(cleaned_content)
            
            documents = []
            for i, chunk in enumerate(chunks):
                documents.append({
                    'content': chunk,
                    'source': str(file_path),
                    'type': 'text',
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                
            return documents
            
        except Exception as e:
            print(f"Erro ao processar {file_path}: {str(e)}")
            return []
    
    def process_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Processa arquivo .json."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        content = self._extract_text_from_dict(item)
                        documents.append({
                            'content': content,
                            'source': str(file_path),
                            'type': 'json',
                            'item_index': i,
                            'raw_data': item
                        })
            elif isinstance(data, dict):
                content = self._extract_text_from_dict(data)
                documents.append({
                    'content': content,
                    'source': str(file_path),
                    'type': 'json',
                    'raw_data': data
                })
                
            return documents
            
        except Exception as e:
            print(f"Erro ao processar {file_path}: {str(e)}")
            return []
    
    def _extract_text_from_dict(self, data: Dict) -> str:
        """Extrai texto de um dicionário."""
        text_parts = []
        
        for key, value in data.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(map(str, value))}")
            elif isinstance(value, dict):
                nested_text = self._extract_text_from_dict(value)
                text_parts.append(f"{key}: {nested_text}")
        
        return " ".join(text_parts)
    
    def index_file(self, file_path: str) -> bool:
        """Indexa um arquivo específico."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            return False
        
        documents = []
        
        if file_path.suffix.lower() == '.txt':
            documents = self.process_txt_file(file_path)
        elif file_path.suffix.lower() == '.json':
            documents = self.process_json_file(file_path)
        else:
            print(f"Tipo de arquivo não suportado: {file_path.suffix}")
            return False
        
        if documents:
            # Gera embeddings para os documentos
            contents = [doc['content'] for doc in documents]
            embeddings = self.model.encode(contents, convert_to_tensor=True)
            
            # Armazena documentos, embeddings e metadados
            self.documents.extend(contents)
            self.embeddings.extend(embeddings.cpu().numpy())
            self.metadata.extend(documents)
            
            print(f"Indexados {len(documents)} chunks de {file_path}")
            return True
        
        return False
    
    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.2) -> List[Dict[str, Any]]:
        """Busca por similaridade semântica."""
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da indexação."""
        return {
            'total_documents': len(self.documents),
            'total_files': len(set(meta['source'] for meta in self.metadata)),
            'types': list(set(meta['type'] for meta in self.metadata))
        } 