"""Análise de dificuldades e lacunas de conhecimento do usuário."""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class Difficulty(Enum):
    """Níveis de dificuldade identificados."""
    INICIANTE = "iniciante"
    INTERMEDIARIO = "intermediario" 
    AVANCADO = "avancado"
    ESPECIALISTA = "especialista"


class LearningPreference(Enum):
    """Preferências de formato de aprendizagem."""
    TEXTO = "texto"
    VIDEO = "video"
    AUDIO = "audio"
    VISUAL = "visual"
    PRATICO = "pratico"


@dataclass
class KnowledgeGap:
    """Representa uma lacuna de conhecimento identificada."""
    topic: str
    difficulty_level: Difficulty
    confidence_score: float  # 0.0 a 1.0
    evidence: List[str]  # Evidências que levaram à identificação
    related_topics: List[str]
    suggested_resources: List[str]


@dataclass
class UserProfile:
    """Perfil do usuário baseado nas interações."""
    name: Optional[str] = None
    overall_level: Difficulty = Difficulty.INICIANTE
    learning_preferences: List[LearningPreference] = None
    knowledge_gaps: List[KnowledgeGap] = None
    strong_topics: List[str] = None
    interaction_history: List[str] = None
    preferred_explanation_style: str = "simples"  # simples, detalhado, tecnico
    
    def __post_init__(self):
        if self.learning_preferences is None:
            self.learning_preferences = []
        if self.knowledge_gaps is None:
            self.knowledge_gaps = []
        if self.strong_topics is None:
            self.strong_topics = []
        if self.interaction_history is None:
            self.interaction_history = []


class DifficultyAnalyzer:
    """Analisa as dificuldades e preferências de aprendizagem do usuário."""
    
    def __init__(self):
        """Inicializa o analisador."""
        self.user_profile = UserProfile()
        self.programming_topics = {
            # Tópicos básicos
            "variaveis": ["variable", "var", "variável", "declaração", "atribuição"],
            "tipos_dados": ["int", "string", "float", "boolean", "tipo", "dados"],
            "operadores": ["operador", "aritmetico", "comparação", "logico", "+", "-", "*", "/"],
            "estruturas_controle": ["if", "else", "elif", "condicional", "decisão"],
            "loops": ["for", "while", "loop", "repetição", "iteração", "laço"],
            
            # Tópicos intermediários
            "funcoes": ["function", "função", "def", "return", "parametro", "argumento"],
            "listas_arrays": ["list", "array", "lista", "vetor", "index", "indice"],
            "dicionarios": ["dict", "dictionary", "dicionário", "chave", "valor", "key", "value"],
            "strings": ["string", "texto", "caractere", "substring", "concatenação", "manipulação texto", "texto python"],
            "arquivos": ["file", "arquivo", "read", "write", "open", "close"],
            
            # Tópicos de formatação e estilo (HTML/CSS)
            "formatacao_texto": ["estilo", "formatação", "css", "html", "fonte", "cor", "tamanho", "negrito", "italico"],
            "html_basico": ["html", "tag", "elemento", "navegador", "pagina web", "markup"],
            "css_basico": ["css", "estilo", "cor", "fonte", "layout", "classe", "seletor"],
            
            # Tópicos avançados
            "orientacao_objetos": ["class", "object", "objeto", "método", "atributo", "herança"],
            "tratamento_erros": ["exception", "error", "erro", "try", "catch", "finally"],
            "algoritmos": ["algoritmo", "recursão", "ordenação", "busca", "complexidade"],
            "estruturas_dados": ["stack", "queue", "tree", "árvore", "grafo", "hash"],
            "design_patterns": ["pattern", "padrão", "singleton", "factory", "observer"]
        }
        
        # Palavras que indicam diferentes níveis de dificuldade
        self.difficulty_indicators = {
            Difficulty.INICIANTE: [
                "não sei", "não entendo", "como fazer", "o que é", "explicar", 
                "básico", "simples", "começar", "aprender", "primeiro", "iniciante"
            ],
            Difficulty.INTERMEDIARIO: [
                "como usar", "diferença entre", "quando usar", "melhor forma",
                "prática", "exemplo", "aplicar", "implementar"
            ],
            Difficulty.AVANCADO: [
                "otimizar", "performance", "eficiência", "complexidade",
                "design", "arquitetura", "padrão", "avançado"
            ],
            Difficulty.ESPECIALISTA: [
                "especialista", "expert", "profissional", "produção",
                "escala", "enterprise", "distribuído", "microservices"
            ]
        }
        
        # Indicadores de preferência de formato
        self.format_preferences = {
            LearningPreference.TEXTO: [
                "leia", "ler", "texto", "documentação", "artigo", "escrever", "explicação"
            ],
            LearningPreference.VIDEO: [
                "vídeo", "video", "assistir", "ver", "demonstração", "tutorial", "aula"
            ],
            LearningPreference.VISUAL: [
                "imagem", "gráfico", "diagrama", "visual", "desenho", "esquema", "mostrar"
            ],
            LearningPreference.PRATICO: [
                "prática", "exercício", "exemplo", "código", "implementar", "fazer", "testar"
            ]
        }
    
    def analyze_user_input(self, user_input: str) -> Dict[str, Any]:
        """Analisa uma entrada do usuário para identificar dificuldades e preferências."""
        user_input_lower = user_input.lower()
        
        analysis = {
            'detected_topics': [],
            'difficulty_level': Difficulty.INICIANTE,
            'knowledge_gaps': [],
            'format_preferences': [],
            'confidence_indicators': [],
            'question_type': self._classify_question_type(user_input)
        }
        
        # Identifica tópicos mencionados
        for topic, keywords in self.programming_topics.items():
            if any(keyword in user_input_lower for keyword in keywords):
                analysis['detected_topics'].append(topic)
        
        # Analisa nível de dificuldade
        difficulty_scores = {level: 0 for level in Difficulty}
        for level, indicators in self.difficulty_indicators.items():
            for indicator in indicators:
                if indicator in user_input_lower:
                    difficulty_scores[level] += 1
        
        # Determina o nível com maior pontuação
        if max(difficulty_scores.values()) > 0:
            analysis['difficulty_level'] = max(difficulty_scores, key=difficulty_scores.get)
        
        # Identifica preferências de formato
        for format_pref, keywords in self.format_preferences.items():
            if any(keyword in user_input_lower for keyword in keywords):
                analysis['format_preferences'].append(format_pref)
        
        # Identifica indicadores de confiança/incerteza
        confidence_keywords = {
            'baixa': ["não sei", "não entendo", "confuso", "difícil", "ajuda", "não consigo"],
            'media': ["mais ou menos", "acho que", "talvez", "provavelmente"],
            'alta': ["sei que", "certeza", "fácil", "domino", "conheco bem"]
        }
        
        for level, keywords in confidence_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                analysis['confidence_indicators'].append(level)
        
        return analysis
    
    def _classify_question_type(self, user_input: str) -> str:
        """Classifica o tipo de pergunta do usuário."""
        user_input_lower = user_input.lower()
        
        question_patterns = {
            'definição': [r'^o que é', r'^qual é', r'^defina', r'^explique o conceito'],
            'como_fazer': [r'^como', r'como fazer', r'como usar', r'como implementar'],
            'diferença': [r'diferença entre', r'qual a diferença', r'diferente de'],
            'exemplo': [r'exemplo', r'demonstre', r'mostre', r'ilustre'],
            'comparação': [r'melhor', r'pior', r'comparar', r'versus', r'vs'],
            'solução_problema': [r'erro', r'problema', r'não funciona', r'bug', r'resolver'],
            'boas_praticas': [r'boa prática', r'recomendação', r'padrão', r'convenção']
        }
        
        for question_type, patterns in question_patterns.items():
            if any(re.search(pattern, user_input_lower) for pattern in patterns):
                return question_type
        
        return 'geral'
    
    def update_user_profile(self, analysis: Dict[str, Any], user_input: str) -> None:
        """Atualiza o perfil do usuário com base na análise."""
        # Adiciona à história de interações
        self.user_profile.interaction_history.append(user_input)
        
        # Atualiza nível geral (média ponderada)
        current_level = analysis['difficulty_level']
        if len(self.user_profile.interaction_history) == 1:
            self.user_profile.overall_level = current_level
        else:
            # Combina nível atual com histórico
            levels_numeric = {
                Difficulty.INICIANTE: 1,
                Difficulty.INTERMEDIARIO: 2,
                Difficulty.AVANCADO: 3,
                Difficulty.ESPECIALISTA: 4
            }
            
            current_numeric = levels_numeric[current_level]
            profile_numeric = levels_numeric[self.user_profile.overall_level]
            
            # Média ponderada com mais peso para interações recentes
            new_numeric = (profile_numeric * 0.7 + current_numeric * 0.3)
            
            # Converte de volta para enum
            if new_numeric <= 1.5:
                self.user_profile.overall_level = Difficulty.INICIANTE
            elif new_numeric <= 2.5:
                self.user_profile.overall_level = Difficulty.INTERMEDIARIO
            elif new_numeric <= 3.5:
                self.user_profile.overall_level = Difficulty.AVANCADO
            else:
                self.user_profile.overall_level = Difficulty.ESPECIALISTA
        
        # Atualiza preferências de formato
        for pref in analysis['format_preferences']:
            if pref not in self.user_profile.learning_preferences:
                self.user_profile.learning_preferences.append(pref)
        
        # Identifica lacunas de conhecimento
        for topic in analysis['detected_topics']:
            if 'baixa' in analysis['confidence_indicators']:
                gap = KnowledgeGap(
                    topic=topic,
                    difficulty_level=analysis['difficulty_level'],
                    confidence_score=0.3,  # Baixa confiança
                    evidence=[user_input],
                    related_topics=self._get_related_topics(topic),
                    suggested_resources=[]
                )
                
                # Verifica se já existe esta lacuna
                existing_gap = next((g for g in self.user_profile.knowledge_gaps if g.topic == topic), None)
                if existing_gap:
                    existing_gap.evidence.append(user_input)
                    existing_gap.confidence_score = min(existing_gap.confidence_score + 0.1, 1.0)
                else:
                    self.user_profile.knowledge_gaps.append(gap)
            
            elif 'alta' in analysis['confidence_indicators']:
                # Remove das lacunas se existir e adiciona aos tópicos fortes
                self.user_profile.knowledge_gaps = [
                    g for g in self.user_profile.knowledge_gaps if g.topic != topic
                ]
                if topic not in self.user_profile.strong_topics:
                    self.user_profile.strong_topics.append(topic)
        
        # Atualiza estilo de explicação baseado no nível
        if self.user_profile.overall_level == Difficulty.INICIANTE:
            self.user_profile.preferred_explanation_style = "simples"
        elif self.user_profile.overall_level == Difficulty.INTERMEDIARIO:
            self.user_profile.preferred_explanation_style = "detalhado"
        else:
            self.user_profile.preferred_explanation_style = "tecnico"
    
    def _get_related_topics(self, topic: str) -> List[str]:
        """Retorna tópicos relacionados ao tópico dado."""
        relationships = {
            "variaveis": ["tipos_dados", "operadores"],
            "tipos_dados": ["variaveis", "operadores", "strings"],
            "estruturas_controle": ["operadores", "loops"],
            "loops": ["estruturas_controle", "listas_arrays"],
            "funcoes": ["variaveis", "tipos_dados", "estruturas_controle"],
            "listas_arrays": ["loops", "funcoes", "strings"],
            "orientacao_objetos": ["funcoes", "variaveis", "tratamento_erros"],
            "algoritmos": ["estruturas_dados", "loops", "funcoes"],
        }
        
        return relationships.get(topic, [])
    
    def get_learning_recommendations(self) -> Dict[str, Any]:
        """Gera recomendações de aprendizagem baseadas no perfil do usuário."""
        recommendations = {
            'priority_topics': [],
            'suggested_formats': [],
            'next_steps': [],
            'explanation_style': self.user_profile.preferred_explanation_style
        }
        
        # Prioriza lacunas de conhecimento
        sorted_gaps = sorted(
            self.user_profile.knowledge_gaps, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )
        
        recommendations['priority_topics'] = [gap.topic for gap in sorted_gaps[:5]]
        
        # Sugere formatos baseado nas preferências
        if self.user_profile.learning_preferences:
            recommendations['suggested_formats'] = self.user_profile.learning_preferences
        else:
            # Formatos padrão baseados no nível
            if self.user_profile.overall_level == Difficulty.INICIANTE:
                recommendations['suggested_formats'] = [LearningPreference.VIDEO, LearningPreference.PRATICO]
            else:
                recommendations['suggested_formats'] = [LearningPreference.TEXTO, LearningPreference.PRATICO]
        
        # Próximos passos baseados no nível e lacunas
        if self.user_profile.overall_level == Difficulty.INICIANTE:
            recommendations['next_steps'] = [
                "Começar com conceitos básicos de programação",
                "Praticar com exercícios simples",
                "Assistir tutoriais introdutórios"
            ]
        elif self.user_profile.overall_level == Difficulty.INTERMEDIARIO:
            recommendations['next_steps'] = [
                "Aprofundar em estruturas de dados",
                "Praticar resolução de problemas",
                "Aprender boas práticas de programação"
            ]
        else:
            recommendations['next_steps'] = [
                "Estudar design patterns",
                "Otimizar algoritmos existentes",
                "Explorar arquiteturas avançadas"
            ]
        
        return recommendations
    
    def get_user_profile_summary(self) -> Dict[str, Any]:
        """Retorna um resumo do perfil do usuário."""
        return {
            'overall_level': self.user_profile.overall_level.value,
            'total_interactions': len(self.user_profile.interaction_history),
            'knowledge_gaps_count': len(self.user_profile.knowledge_gaps),
            'strong_topics': self.user_profile.strong_topics,
            'learning_preferences': [pref.value for pref in self.user_profile.learning_preferences],
            'preferred_explanation_style': self.user_profile.preferred_explanation_style,
            'top_knowledge_gaps': [
                {
                    'topic': gap.topic,
                    'confidence_score': gap.confidence_score,
                    'related_topics': gap.related_topics
                }
                for gap in sorted(self.user_profile.knowledge_gaps, key=lambda x: x.confidence_score)[:3]
            ]
        } 