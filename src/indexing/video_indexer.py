"""Indexador de arquivos de vídeo com transcrição automática usando SpeechRecognition."""

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_RECOGNITION_AVAILABLE = True
    print("✅ SpeechRecognition carregado com sucesso")
except ImportError as e:
    print(f"⚠️ SpeechRecognition não disponível: {e}")
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None
    AudioSegment = None

import moviepy.editor as mp
from pathlib import Path
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import tempfile
import os
import re


class VideoIndexer:
    """Indexador para arquivos de vídeo (.mp4, .avi, .mov, .mkv) usando SpeechRecognition."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa o indexador com modelo de embeddings e reconhecedor de fala."""
        self.model = SentenceTransformer(model_name)
        
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.speech_enabled = True
                print("✅ SpeechRecognition inicializado com sucesso")
                
                # Configurações do reconhecedor
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                
            except Exception as e:
                print(f"⚠️ Erro ao inicializar SpeechRecognition: {e}")
                self.recognizer = None
                self.speech_enabled = False
        else:
            self.recognizer = None
            self.speech_enabled = False
            
        self.documents = []
        self.embeddings = []
        self.metadata = []
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.m4v', '.flv', '.wmv'}
    
    def extract_audio(self, video_path: Path) -> Optional[str]:
        """Extrai áudio do vídeo para um arquivo temporário."""
        try:
            # Carrega o vídeo
            video = mp.VideoFileClip(str(video_path))
            
            # Cria arquivo temporário para o áudio
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            # Extrai o áudio
            audio = video.audio
            if audio is None:
                print(f"Vídeo {video_path} não possui faixa de áudio")
                video.close()
                return None
            
            audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
            
            # Limpa recursos
            audio.close()
            video.close()
            
            return temp_audio_path
            
        except Exception as e:
            print(f"Erro ao extrair áudio de {video_path}: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcreve áudio usando SpeechRecognition."""
        if not self.speech_enabled:
            return {
                'text': '[Transcrição não disponível - SpeechRecognition não instalado]',
                'language': 'unknown',
                'segments': []
            }
            
        try:
            # Converte áudio para WAV se necessário
            wav_path = self._convert_to_wav(audio_path)
            
            # Carrega áudio com pydub para dividir em chunks
            audio = AudioSegment.from_wav(wav_path)
            
            # Divide áudio em chunks de 30 segundos (SpeechRecognition funciona melhor com chunks menores)
            chunk_length = 30 * 1000  # 30 segundos em millisegundos
            chunks = []
            
            for i in range(0, len(audio), chunk_length):
                chunk = audio[i:i + chunk_length]
                chunks.append((i / 1000, (i + len(chunk)) / 1000, chunk))  # (start_time, end_time, audio_chunk)
            
            # Transcreve cada chunk
            full_text = ""
            segments = []
            
            print(f"  - Dividindo áudio em {len(chunks)} chunks de ~30s cada")
            
            for i, (start_time, end_time, chunk) in enumerate(chunks):
                try:
                    # Salva chunk temporário
                    chunk_path = f"{wav_path}_chunk_{i}.wav"
                    chunk.export(chunk_path, format="wav")
                    
                    # Transcreve chunk
                    chunk_text = self._transcribe_chunk(chunk_path)
                    
                    if chunk_text.strip():
                        full_text += chunk_text + " "
                        segments.append({
                            'start': start_time,
                            'end': end_time,
                            'text': chunk_text.strip(),
                            'words': []  # SpeechRecognition não fornece palavras individuais
                        })
                    
                    # Remove arquivo temporário
                    try:
                        os.unlink(chunk_path)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"    ⚠️ Erro no chunk {i}: {str(e)}")
                    continue
            
            # Remove arquivo WAV temporário se foi criado
            if wav_path != audio_path:
                try:
                    os.unlink(wav_path)
                except:
                    pass
            
            transcription_data = {
                'text': full_text.strip(),
                'language': 'pt-BR',  # SpeechRecognition não detecta idioma automaticamente
                'segments': segments
            }
            
            return transcription_data
            
        except Exception as e:
            print(f"Erro na transcrição: {str(e)}")
            return {'text': '', 'language': 'unknown', 'segments': []}
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Converte áudio para formato WAV."""
        try:
            # Tenta carregar com pydub
            if audio_path.lower().endswith('.wav'):
                return audio_path
                
            # Converte para WAV
            audio = AudioSegment.from_file(audio_path)
            wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
            audio.export(wav_path, format="wav")
            
            return wav_path
            
        except Exception as e:
            print(f"Erro ao converter áudio: {str(e)}")
            return audio_path
    
    def _transcribe_chunk(self, chunk_path: str) -> str:
        """Transcreve um chunk de áudio usando diferentes engines."""
        
        with sr.AudioFile(chunk_path) as source:
            # Ajusta para ruído ambiente
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = self.recognizer.record(source)
        
        # Tenta diferentes engines em ordem de preferência
        engines = [
            ('Google Web Speech', lambda: self.recognizer.recognize_google(audio_data, language='pt-BR')),
            ('Google Web Speech (EN)', lambda: self.recognizer.recognize_google(audio_data, language='en-US')),
            ('PocketSphinx', lambda: self.recognizer.recognize_sphinx(audio_data))
        ]
        
        for engine_name, transcribe_func in engines:
            try:
                result = transcribe_func()
                if result and result.strip():
                    print(f"    ✅ Transcrito com {engine_name}: {result[:50]}...")
                    return result
            except sr.UnknownValueError:
                # Áudio não foi compreendido
                continue
            except sr.RequestError as e:
                # Erro na requisição (sem internet, etc.)
                print(f"    ⚠️ {engine_name} falhou: {str(e)}")
                continue
            except Exception as e:
                # Outros erros
                print(f"    ⚠️ Erro em {engine_name}: {str(e)}")
                continue
        
        return ""  # Se nenhum engine funcionou
    
    def get_video_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Extrai metadados básicos do vídeo."""
        try:
            video = mp.VideoFileClip(str(video_path))
            
            metadata = {
                'duration': video.duration,
                'fps': video.fps,
                'resolution': (video.w, video.h) if video.w and video.h else None,
                'file_size': video_path.stat().st_size,
                'format': video_path.suffix.lower()
            }
            
            video.close()
            return metadata
            
        except Exception as e:
            print(f"Erro ao extrair metadados de {video_path}: {str(e)}")
            return {
                'duration': None,
                'fps': None,
                'resolution': None,
                'file_size': video_path.stat().st_size if video_path.exists() else 0,
                'format': video_path.suffix.lower()
            }
    
    def format_timestamp(self, seconds: float) -> str:
        """Formata timestamp em formato legível (MM:SS)."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def chunk_transcription(self, transcription: Dict[str, Any], chunk_duration: int = 60) -> List[Dict[str, Any]]:
        """Divide transcrição em chunks baseados em tempo."""
        chunks = []
        current_chunk = {
            'text': '',
            'start_time': 0,
            'end_time': 0,
            'segments': []
        }
        
        for segment in transcription['segments']:
            # Se o segmento ultrapassa o limite do chunk atual
            if segment['start'] >= current_chunk['start_time'] + chunk_duration and current_chunk['text']:
                # Finaliza chunk atual
                current_chunk['text'] = current_chunk['text'].strip()
                if current_chunk['text']:
                    chunks.append(current_chunk)
                
                # Inicia novo chunk
                current_chunk = {
                    'text': segment['text'],
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'segments': [segment]
                }
            else:
                # Adiciona ao chunk atual
                if not current_chunk['text']:
                    current_chunk['start_time'] = segment['start']
                
                current_chunk['text'] += ' ' + segment['text']
                current_chunk['end_time'] = segment['end']
                current_chunk['segments'].append(segment)
        
        # Adiciona último chunk se não estiver vazio
        if current_chunk['text'].strip():
            chunks.append(current_chunk)
        
        # Se não conseguiu criar chunks por tempo, cria por número de palavras
        if not chunks and transcription['text']:
            words = transcription['text'].split()
            word_chunk_size = 200
            
            for i in range(0, len(words), word_chunk_size):
                chunk_words = words[i:i + word_chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                # Estima timestamps baseado na posição proporcional
                total_duration = max([seg['end'] for seg in transcription['segments']], default=0)
                start_ratio = i / len(words)
                end_ratio = min((i + word_chunk_size) / len(words), 1.0)
                
                chunks.append({
                    'text': chunk_text,
                    'start_time': start_ratio * total_duration,
                    'end_time': end_ratio * total_duration,
                    'segments': []  # Não tem segmentos específicos neste caso
                })
        
        return chunks
    
    def index_file(self, file_path: str) -> bool:
        """Indexa um arquivo de vídeo."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            return False
        
        if file_path.suffix.lower() not in self.supported_formats:
            print(f"Formato de vídeo não suportado: {file_path.suffix}")
            return False
        
        print(f"Processando vídeo: {file_path.name}")
        
        # Extrai metadados do vídeo
        video_metadata = self.get_video_metadata(file_path)
        print(f"  - Duração: {video_metadata.get('duration', 0):.1f}s")
        
        # Extrai áudio
        audio_path = self.extract_audio(file_path)
        if not audio_path:
            return False
        
        try:
            if self.speech_enabled:
                print("  - Transcrevendo áudio com SpeechRecognition...")
            else:
                print("  - ⚠️ SpeechRecognition não disponível - criando placeholder...")
                
            # Transcreve áudio
            transcription = self.transcribe_audio(audio_path)
            
            if not transcription['text'].strip() or '[Transcrição não disponível' in transcription['text']:
                if not self.speech_enabled:
                    print("  - Vídeo indexado sem transcrição (SpeechRecognition indisponível)")
                    # Continua com placeholder para não quebrar o sistema
                else:
                    print("  - Nenhum texto foi transcrito")
                    return False
            
            print(f"  - Idioma configurado: {transcription['language']}")  
            print(f"  - Texto extraído: {len(transcription['text'])} caracteres")
            
            # Divide em chunks
            chunks = self.chunk_transcription(transcription)
            print(f"  - Criados {len(chunks)} chunks")
            
            # Cria documentos para indexação
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    'content': chunk['text'],
                    'source': str(file_path),
                    'type': 'video',
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'start_time': chunk['start_time'],
                    'end_time': chunk['end_time'],
                    'start_timestamp': self.format_timestamp(chunk['start_time']),
                    'end_timestamp': self.format_timestamp(chunk['end_time']),
                    'language': transcription['language'],
                    'duration': video_metadata.get('duration'),
                    'resolution': video_metadata.get('resolution'),
                    'fps': video_metadata.get('fps'),
                    'file_size': video_metadata.get('file_size'),
                    'segments_count': len(chunk['segments'])
                }
                documents.append(doc_metadata)
            
            if not documents:
                print("  - Não foi possível criar documentos")
                return False
            
            # Gera embeddings para os chunks
            contents = [doc['content'] for doc in documents]
            embeddings = self.model.encode(contents, convert_to_tensor=True)
            
            # Armazena documentos, embeddings e metadados
            self.documents.extend(contents)
            self.embeddings.extend(embeddings.cpu().numpy())
            self.metadata.extend(documents)
            
            print(f"  - Indexação concluída com sucesso!")
            
            return True
            
        finally:
            # Remove arquivo de áudio temporário
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    print(f"Aviso: Não foi possível remover arquivo temporário: {e}")
    
    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """Busca por similaridade semântica nos vídeos indexados."""
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
            result = {
                'content': self.documents[original_idx],
                'similarity': float(similarities[original_idx]),
                'metadata': self.metadata[original_idx]
            }
            
            # Adiciona informações de tempo para facilitar navegação
            meta = self.metadata[original_idx]
            result['time_info'] = {
                'start': meta.get('start_timestamp', '00:00'),
                'end': meta.get('end_timestamp', '00:00'),
                'duration_seconds': meta.get('end_time', 0) - meta.get('start_time', 0)
            }
            
            results.append(result)
        
        return results
    
    def search_by_timerange(self, query: str, start_seconds: float = None, end_seconds: float = None) -> List[Dict[str, Any]]:
        """Busca em um intervalo específico de tempo."""
        if not self.embeddings:
            return []
        
        # Filtra resultados por intervalo de tempo
        filtered_results = []
        for i, meta in enumerate(self.metadata):
            chunk_start = meta.get('start_time', 0)
            chunk_end = meta.get('end_time', 0)
            
            # Verifica se o chunk está no intervalo desejado
            if start_seconds is not None and chunk_end < start_seconds:
                continue
            if end_seconds is not None and chunk_start > end_seconds:
                continue
            
            filtered_results.append(i)
        
        if not filtered_results:
            return []
        
        # Aplica busca semântica apenas nos chunks filtrados
        query_embedding = self.model.encode([query], convert_to_tensor=True)
        filtered_embeddings = np.array([self.embeddings[i] for i in filtered_results])
        similarities = np.dot(filtered_embeddings, query_embedding.cpu().numpy().T).flatten()
        
        # Ordena por similaridade
        sorted_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in sorted_indices:
            original_idx = filtered_results[idx]
            results.append({
                'content': self.documents[original_idx],
                'similarity': float(similarities[idx]),
                'metadata': self.metadata[original_idx],
                'time_info': {
                    'start': self.metadata[original_idx].get('start_timestamp', '00:00'),
                    'end': self.metadata[original_idx].get('end_timestamp', '00:00'),
                    'duration_seconds': self.metadata[original_idx].get('end_time', 0) - self.metadata[original_idx].get('start_time', 0)
                }
            })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da indexação."""
        files = set(meta['source'] for meta in self.metadata)
        total_duration = sum(meta.get('duration', 0) for meta in self.metadata if meta.get('duration'))
        languages = set(meta.get('language', 'unknown') for meta in self.metadata)
        
        return {
            'total_documents': len(self.documents),
            'total_files': len(files),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': self.format_timestamp(total_duration),
            'languages_detected': list(languages),
            'files_processed': list(files),
            'average_chunks_per_file': len(self.documents) / len(files) if files else 0,
            'supported_formats': list(self.supported_formats),
            'transcription_engine': 'SpeechRecognition' if self.speech_enabled else 'Não disponível'
        } 