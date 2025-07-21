"""Indexador de arquivos de imagem com análise de metadados e descrição automática."""

from PIL import Image, ExifTags
from pathlib import Path
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import hashlib
import json
import cv2


class ImageIndexer:
    """Indexador para arquivos de imagem (.jpg, .jpeg, .png, .bmp, .gif, .tiff)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa o indexador com modelo de embeddings."""
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = []
        self.metadata = []
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    
    def extract_exif_data(self, image_path: Path) -> Dict[str, Any]:
        """Extrai dados EXIF da imagem."""
        try:
            image = Image.open(image_path)
            exif_data = {}
            
            if hasattr(image, '_getexif'):
                exif_dict = image._getexif()
                if exif_dict is not None:
                    for tag, value in exif_dict.items():
                        decoded = ExifTags.TAGS.get(tag, tag)
                        exif_data[decoded] = value
            
            image.close()
            return exif_data
            
        except Exception as e:
            print(f"Erro ao extrair EXIF de {image_path}: {str(e)}")
            return {}
    
    def get_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Extrai metadados básicos da imagem."""
        try:
            # Metadados básicos do arquivo
            file_stats = image_path.stat()
            
            # Abre imagem para análise
            image = Image.open(image_path)
            
            # Calcula hash da imagem para detecção de duplicatas
            with open(image_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            metadata = {
                'file_size': file_stats.st_size,
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'file_hash': file_hash,
                'aspect_ratio': round(image.width / image.height, 2) if image.height > 0 else 0,
                'total_pixels': image.width * image.height,
                'color_mode': self._get_color_mode_description(image.mode)
            }
            
            # Adiciona dados EXIF se disponíveis
            exif_data = self.extract_exif_data(image_path)
            if exif_data:
                metadata['exif'] = exif_data
                
                # Extrai informações úteis do EXIF
                if 'DateTime' in exif_data:
                    metadata['date_taken'] = str(exif_data['DateTime'])
                
                if 'Make' in exif_data and 'Model' in exif_data:
                    metadata['camera'] = f"{exif_data['Make']} {exif_data['Model']}"
                
                if 'Software' in exif_data:
                    metadata['software'] = str(exif_data['Software'])
            
            image.close()
            return metadata
            
        except Exception as e:
            print(f"Erro ao extrair metadados de {image_path}: {str(e)}")
            return {
                'file_size': image_path.stat().st_size if image_path.exists() else 0,
                'format': image_path.suffix.lower(),
                'error': str(e)
            }
    
    def _get_color_mode_description(self, mode: str) -> str:
        """Retorna descrição do modo de cor da imagem."""
        mode_descriptions = {
            '1': 'Preto e Branco (1-bit)',
            'L': 'Escala de Cinza (8-bit)',
            'P': 'Paleta (8-bit)',
            'RGB': 'RGB (24-bit)',
            'RGBA': 'RGB com Transparência (32-bit)',
            'CMYK': 'CMYK (32-bit)',
            'YCbCr': 'YCbCr (24-bit)',
            'LAB': 'LAB (24-bit)',
            'HSV': 'HSV (24-bit)'
        }
        return mode_descriptions.get(mode, f'Desconhecido ({mode})')
    
    def analyze_image_colors(self, image_path: Path, top_colors: int = 5) -> Dict[str, Any]:
        """Analisa as cores dominantes da imagem."""
        try:
            # Abre imagem com OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                return {}
            
            # Converte BGR para RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Redimensiona para acelerar processamento
            height, width = img_rgb.shape[:2]
            if width > 300:
                scale = 300 / width
                new_width = 300
                new_height = int(height * scale)
                img_rgb = cv2.resize(img_rgb, (new_width, new_height))
            
            # Reshape para análise de cores
            pixels = img_rgb.reshape(-1, 3).astype(np.uint8)  # Força tipo uint8
            
            # Análise básica de cores
            colors_analysis = {
                'mean_color': [int(c) for c in np.mean(pixels, axis=0)],
                'dominant_colors': [],
                'brightness': float(np.mean(pixels)),
                'contrast': float(np.std(pixels))
            }
            
            # Encontra cores dominantes de forma mais simples e segura
            # Converte cada pixel RGB para string para contagem
            pixel_colors = []
            for pixel in pixels:
                color_key = f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
                pixel_colors.append(color_key)
            
            # Conta cores únicas
            from collections import Counter
            color_counts = Counter(pixel_colors)
            most_common = color_counts.most_common(top_colors)
            
            for hex_color, count in most_common:
                # Converte hex de volta para RGB
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                colors_analysis['dominant_colors'].append({
                    'rgb': [r, g, b],
                    'hex': f'#{hex_color}',
                    'percentage': float(count / len(pixels) * 100)
                })
            
            return colors_analysis
            
        except Exception as e:
            print(f"Erro na análise de cores de {image_path}: {str(e)}")
            return {}
    
    def generate_image_description(self, image_path: Path, metadata: Dict[str, Any]) -> str:
        """Gera descrição textual da imagem baseada em metadados."""
        descriptions = []
        
        # Informações básicas
        if 'width' in metadata and 'height' in metadata:
            size_desc = f"Imagem de {metadata['width']}x{metadata['height']} pixels"
            
            # Classifica tamanho
            total_pixels = metadata.get('total_pixels', 0)
            if total_pixels > 2000000:  # > 2MP
                size_desc += " (alta resolução)"
            elif total_pixels > 500000:  # > 0.5MP
                size_desc += " (resolução média)"
            else:
                size_desc += " (baixa resolução)"
            
            descriptions.append(size_desc)
        
        # Formato e modo de cor
        if 'format' in metadata:
            format_desc = f"Formato {metadata['format']}"
            if 'color_mode' in metadata:
                format_desc += f" em {metadata['color_mode']}"
            descriptions.append(format_desc)
        
        # Proporção da imagem
        if 'aspect_ratio' in metadata:
            ratio = metadata['aspect_ratio']
            if ratio > 1.5:
                descriptions.append("Imagem em formato paisagem (horizontal)")
            elif ratio < 0.75:
                descriptions.append("Imagem em formato retrato (vertical)")
            else:
                descriptions.append("Imagem em formato quadrado ou próximo")
        
        # Informações da câmera
        if 'camera' in metadata:
            descriptions.append(f"Capturada com {metadata['camera']}")
        
        if 'date_taken' in metadata:
            descriptions.append(f"Data da foto: {metadata['date_taken']}")
        
        # Informações técnicas do EXIF
        exif = metadata.get('exif', {})
        technical_info = []
        
        if 'FocalLength' in exif:
            focal_length = exif['FocalLength']
            if isinstance(focal_length, tuple) and len(focal_length) == 2:
                focal_mm = focal_length[0] / focal_length[1] if focal_length[1] != 0 else focal_length[0]
                technical_info.append(f"focal {focal_mm:.1f}mm")
        
        if 'FNumber' in exif:
            f_number = exif['FNumber']
            if isinstance(f_number, tuple) and len(f_number) == 2:
                f_stop = f_number[0] / f_number[1] if f_number[1] != 0 else f_number[0]
                technical_info.append(f"f/{f_stop:.1f}")
        
        if 'ExposureTime' in exif:
            exposure = exif['ExposureTime']
            if isinstance(exposure, tuple) and len(exposure) == 2:
                shutter = exposure[0] / exposure[1] if exposure[1] != 0 else exposure[0]
                if shutter < 1:
                    technical_info.append(f"1/{int(1/shutter)}s")
                else:
                    technical_info.append(f"{shutter:.1f}s")
        
        if 'ISOSpeedRatings' in exif:
            iso = exif['ISOSpeedRatings']
            technical_info.append(f"ISO {iso}")
        
        if technical_info:
            descriptions.append(f"Configurações: {', '.join(technical_info)}")
        
        # Análise de cores
        colors = metadata.get('colors_analysis', {})
        if 'brightness' in colors:
            brightness = colors['brightness']
            if brightness > 200:
                descriptions.append("Imagem clara/brilhante")
            elif brightness < 80:
                descriptions.append("Imagem escura")
            else:
                descriptions.append("Imagem com iluminação média")
        
        if 'dominant_colors' in colors and colors['dominant_colors']:
            color_names = []
            for color_info in colors['dominant_colors'][:3]:  # Top 3 cores
                rgb = color_info['rgb']
                color_name = self._get_color_name(rgb)
                percentage = color_info['percentage']
                color_names.append(f"{color_name} ({percentage:.1f}%)")
            
            if color_names:
                descriptions.append(f"Cores dominantes: {', '.join(color_names)}")
        
        # Informações do arquivo
        if 'file_size' in metadata:
            size_mb = metadata['file_size'] / (1024 * 1024)
            if size_mb > 10:
                descriptions.append(f"Arquivo grande ({size_mb:.1f}MB)")
            elif size_mb < 0.5:
                descriptions.append(f"Arquivo pequeno ({size_mb*1024:.0f}KB)")
        
        return ". ".join(descriptions) + "."
    
    def _get_color_name(self, rgb: List[int]) -> str:
        """Converte RGB em nome de cor aproximado."""
        r, g, b = rgb
        
        # Cores básicas
        if max(rgb) - min(rgb) < 30:  # Tons de cinza
            if max(rgb) > 200:
                return "branco"
            elif max(rgb) < 80:
                return "preto"
            else:
                return "cinza"
        
        # Cores primárias e secundárias
        if r > g + 50 and r > b + 50:
            if r > 200 and g < 100 and b < 100:
                return "vermelho"
            elif g > 100 or b > 100:
                return "rosa"
        
        if g > r + 50 and g > b + 50:
            return "verde"
        
        if b > r + 50 and b > g + 50:
            return "azul"
        
        if r > 150 and g > 150 and b < 100:
            return "amarelo"
        
        if r > 100 and g < 150 and b > 100:
            return "roxo"
        
        if r > 150 and g > 100 and b < 100:
            return "laranja"
        
        return "colorido"
    
    def index_file(self, file_path: str) -> bool:
        """Indexa um arquivo de imagem."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            return False
        
        if file_path.suffix.lower() not in self.supported_formats:
            print(f"Formato de imagem não suportado: {file_path.suffix}")
            return False
        
        print(f"Processando imagem: {file_path.name}")
        
        # Extrai metadados da imagem
        image_metadata = self.get_image_metadata(file_path)
        
        # Analisa cores da imagem
        colors_analysis = self.analyze_image_colors(file_path)
        if colors_analysis:
            image_metadata['colors_analysis'] = colors_analysis
        
        # Gera descrição textual
        description = self.generate_image_description(file_path, image_metadata)
        
        print(f"  - Dimensões: {image_metadata.get('width', 'N/A')}x{image_metadata.get('height', 'N/A')}")
        print(f"  - Formato: {image_metadata.get('format', 'N/A')}")
        
        # Cria documento para indexação
        doc_metadata = {
            'content': description,
            'source': str(file_path),
            'type': 'image',
            'chunk_index': 0,
            'total_chunks': 1,
            **image_metadata
        }
        
        # Gera embedding para a descrição
        embedding = self.model.encode([description], convert_to_tensor=True)
        
        # Armazena documento, embedding e metadados
        self.documents.append(description)
        self.embeddings.append(embedding.cpu().numpy()[0])
        self.metadata.append(doc_metadata)
        
        print(f"  - Indexação concluída!")
        
        return True
    
    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.2) -> List[Dict[str, Any]]:
        """Busca por similaridade semântica nas imagens indexadas."""
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
            meta = self.metadata[original_idx]
            
            result = {
                'content': self.documents[original_idx],
                'similarity': float(similarities[original_idx]),
                'metadata': meta
            }
            
            # Adiciona informações visuais úteis
            result['visual_info'] = {
                'dimensions': f"{meta.get('width', 'N/A')}x{meta.get('height', 'N/A')}",
                'format': meta.get('format', 'N/A'),
                'size_mb': round(meta.get('file_size', 0) / (1024*1024), 2),
                'aspect_ratio': meta.get('aspect_ratio', 0)
            }
            
            results.append(result)
        
        return results
    
    def search_by_properties(self, 
                           min_width: int = None, 
                           max_width: int = None,
                           min_height: int = None,
                           max_height: int = None,
                           formats: List[str] = None) -> List[Dict[str, Any]]:
        """Busca imagens por propriedades específicas."""
        filtered_results = []
        
        for i, meta in enumerate(self.metadata):
            # Filtros de dimensões
            if min_width and meta.get('width', 0) < min_width:
                continue
            if max_width and meta.get('width', float('inf')) > max_width:
                continue
            if min_height and meta.get('height', 0) < min_height:
                continue
            if max_height and meta.get('height', float('inf')) > max_height:
                continue
            
            # Filtro de formato
            if formats and meta.get('format', '').lower() not in [f.lower() for f in formats]:
                continue
            
            filtered_results.append({
                'content': self.documents[i],
                'metadata': meta,
                'visual_info': {
                    'dimensions': f"{meta.get('width', 'N/A')}x{meta.get('height', 'N/A')}",
                    'format': meta.get('format', 'N/A'),
                    'size_mb': round(meta.get('file_size', 0) / (1024*1024), 2),
                    'aspect_ratio': meta.get('aspect_ratio', 0)
                }
            })
        
        return filtered_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da indexação."""
        if not self.metadata:
            return {}
        
        files = set(meta['source'] for meta in self.metadata)
        formats = [meta.get('format', 'unknown') for meta in self.metadata]
        total_size = sum(meta.get('file_size', 0) for meta in self.metadata)
        
        # Estatísticas de dimensões
        widths = [meta.get('width', 0) for meta in self.metadata if meta.get('width')]
        heights = [meta.get('height', 0) for meta in self.metadata if meta.get('height')]
        
        return {
            'total_images': len(self.documents),
            'total_files': len(files),
            'formats_distribution': {format_name: formats.count(format_name) for format_name in set(formats)},
            'total_size_mb': round(total_size / (1024*1024), 2),
            'average_size_mb': round(total_size / len(self.metadata) / (1024*1024), 2) if self.metadata else 0,
            'dimension_stats': {
                'avg_width': round(sum(widths) / len(widths), 1) if widths else 0,
                'avg_height': round(sum(heights) / len(heights), 1) if heights else 0,
                'max_width': max(widths) if widths else 0,
                'max_height': max(heights) if heights else 0,
                'min_width': min(widths) if widths else 0,
                'min_height': min(heights) if heights else 0,
            },
            'files_processed': list(files),
            'supported_formats': list(self.supported_formats)
        } 