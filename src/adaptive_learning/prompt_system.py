"""Sistema de prompt adaptativo que integra análise de dificuldades e geração de conteúdo."""

from typing import Dict, List, Any, Optional, Union
from .difficulty_analyzer import DifficultyAnalyzer, Difficulty, LearningPreference
from .content_generator import ContentGenerator
import json
import time


class AdaptivePromptSystem:
    """Sistema principal que orquestra a análise adaptativa e geração de respostas."""
    
    def __init__(self, indexers: Optional[Dict] = None):
        """Inicializa o sistema adaptativo.
        
        Args:
            indexers: Dicionário com indexadores para diferentes tipos de dados
                     {'text': TextIndexer, 'pdf': PDFIndexer, 'video': VideoIndexer, 'image': ImageIndexer}
        """
        self.difficulty_analyzer = DifficultyAnalyzer()
        self.content_generator = ContentGenerator()
        self.indexers = indexers or {}
        self.conversation_history = []
        self.session_start = time.time()
        
        # Configurações do sistema
        self.max_search_results = 5
        self.similarity_threshold = 0.3
        self.conversation_memory = 10  # Últimas 10 interações
        
        # Templates de prompts para diferentes situações
        self.prompt_templates = {
            'welcome': """
Olá! 👋 Sou seu assistente de aprendizagem adaptativa em programação.

Vou te ajudar de forma personalizada, adaptando minhas explicações ao seu nível e preferências de aprendizagem.

Para começar, que tal me contar:
- O que você gostaria de aprender hoje?
- Você prefere explicações simples, detalhadas ou técnicas?
- Gosta mais de vídeos, textos, exemplos práticos ou diagramas?

Quanto mais você interage comigo, melhor consigo personalizar o conteúdo para você! 🚀
            """,
            
            'clarification': """
Para te ajudar melhor, preciso entender um pouco mais sobre sua dúvida.

Você poderia me dar mais detalhes sobre:
{clarification_points}

Isso me ajudará a encontrar o conteúdo mais relevante e adaptar a explicação ao seu nível.
            """,
            
            'difficulty_detected': """
Percebi que você pode estar com dificuldades em {topic}. Não se preocupe, é normal! 

Vamos abordar isso passo a passo:
{personalized_explanation}

{additional_resources}
            """,
            
            'progress_acknowledgment': """
Excelente! Vejo que você está dominando {topic}. 🎉

Que tal avançarmos para algo mais desafiador? Sugiro explorar:
{next_challenges}
            """
        }
    
    def process_user_input(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Processa entrada do usuário e gera resposta adaptativa."""
        
        # Registra início do processamento
        start_time = time.time()
        
        # Analisa a entrada do usuário
        analysis = self.difficulty_analyzer.analyze_user_input(user_input)
        
        # Atualiza perfil do usuário
        self.difficulty_analyzer.update_user_profile(analysis, user_input)
        
        # Busca conteúdo relevante nos dados indexados
        search_results = self._search_indexed_content(user_input, analysis['detected_topics'])
        
        # Gera resposta adaptativa
        response = self._generate_adaptive_response(
            user_input, analysis, search_results, context
        )
        
        # Adiciona à história da conversa
        interaction = {
            'timestamp': time.time(),
            'user_input': user_input,
            'analysis': analysis,
            'response': response,
            'processing_time': time.time() - start_time
        }
        self.conversation_history.append(interaction)
        
        # Mantém apenas as últimas interações na memória
        if len(self.conversation_history) > self.conversation_memory:
            self.conversation_history = self.conversation_history[-self.conversation_memory:]
        
        return response
    
    def _search_indexed_content(self, query: str, detected_topics: List[str]) -> List[Dict[str, Any]]:
        """Busca conteúdo relevante nos dados indexados."""
        all_results = []
        
        # Busca em todos os indexadores disponíveis
        for indexer_type, indexer in self.indexers.items():
            try:
                # Busca principal pela query
                results = indexer.search(query, top_k=3, min_similarity=self.similarity_threshold)
                
                for result in results:
                    result['source_type'] = indexer_type
                    all_results.append(result)
                
                # Busca adicional por tópicos detectados
                for topic in detected_topics:
                    topic_query = topic.replace('_', ' ')
                    topic_results = indexer.search(topic_query, top_k=2, min_similarity=0.2)
                    
                    for result in topic_results:
                        result['source_type'] = indexer_type
                        result['is_topic_search'] = True
                        all_results.append(result)
                        
            except Exception as e:
                print(f"Erro na busca no indexador {indexer_type}: {str(e)}")
                continue
        
        # Remove duplicatas e ordena por relevância
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.get('similarity', 0), reverse=True)
        
        return sorted_results[:self.max_search_results]
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove resultados duplicados baseado no conteúdo."""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.get('content', '')[:100])  # Primeiros 100 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _generate_adaptive_response(self, 
                                   user_input: str, 
                                   analysis: Dict[str, Any], 
                                   search_results: List[Dict[str, Any]],
                                   context: Optional[Dict] = None) -> Dict[str, Any]:
        """Gera resposta adaptativa baseada na análise e busca."""
        
        user_profile = self.difficulty_analyzer.user_profile
        
        response = {
            'message': '',
            'explanation': None,
            'resources': [],
            'exercises': [],
            'next_steps': [],
            'user_feedback_request': '',
            'metadata': {
                'detected_topics': analysis['detected_topics'],
                'difficulty_level': analysis['difficulty_level'].value,
                'question_type': analysis['question_type'],
                'search_results_count': len(search_results),
                'user_level': user_profile.overall_level.value,
                'preferences': [pref.value for pref in user_profile.learning_preferences]
            }
        }
        
        # Determina o tipo de resposta baseado na análise
        if not analysis['detected_topics'] and analysis['question_type'] == 'geral':
            # Primeira interação ou pergunta muito genérica
            response['message'] = self._generate_welcome_or_clarification(user_input, analysis)
            
        elif analysis['detected_topics']:
            # Tópicos específicos detectados
            main_topic = analysis['detected_topics'][0]  # Tópico principal
            
            # Gera explicação personalizada
            explanation = self.content_generator.generate_personalized_explanation(
                main_topic, user_profile, search_results
            )
            response['explanation'] = explanation
            
            # Monta mensagem principal
            response['message'] = self._format_main_response(
                main_topic, explanation, analysis, search_results
            )
            
            # Gera exercícios se apropriado
            if LearningPreference.PRATICO in user_profile.learning_preferences:
                exercise = self.content_generator.generate_interactive_exercise(
                    main_topic, user_profile.overall_level
                )
                response['exercises'].append(exercise)
            
            # Gera recursos adicionais
            response['resources'] = explanation.get('resources', [])
            
            # Próximos passos
            response['next_steps'] = explanation.get('next_steps', [])
            
        else:
            # Não conseguiu identificar tópicos específicos
            response['message'] = self._generate_fallback_response(user_input, search_results)
        
        # Adiciona solicitação de feedback
        response['user_feedback_request'] = self._generate_feedback_request(analysis, user_profile)
        
        # Adiciona informações contextais dos dados encontrados
        if search_results:
            response['found_resources'] = self._format_found_resources(search_results)
        
        return response
    
    def _generate_welcome_or_clarification(self, user_input: str, analysis: Dict[str, Any]) -> str:
        """Gera mensagem de boas-vindas ou pedido de esclarecimento."""
        
        interaction_count = len(self.conversation_history)
        
        if interaction_count == 0:
            # Primeira interação
            return self.prompt_templates['welcome'].strip()
        
        else:
            # Precisa de esclarecimento
            clarification_points = []
            
            if not analysis['detected_topics']:
                clarification_points.append("• Qual tópico específico você gostaria de aprender?")
            
            if analysis['question_type'] == 'geral':
                clarification_points.append("• Você tem alguma dúvida específica ou gostaria de uma introdução ao tópico?")
            
            if not analysis['format_preferences']:
                clarification_points.append("• Como prefere aprender: vídeos, textos, exemplos práticos ou diagramas?")
            
            return self.prompt_templates['clarification'].format(
                clarification_points='\n'.join(clarification_points)
            ).strip()
    
    def _format_main_response(self, 
                             topic: str, 
                             explanation: Dict[str, Any], 
                             analysis: Dict[str, Any], 
                             search_results: List[Dict[str, Any]]) -> str:
        """Formata a resposta principal com base na explicação gerada."""
        
        # Inicia com a explicação principal
        message_parts = []
        
        # Título baseado no tipo de pergunta
        question_type = analysis['question_type']
        topic_display = topic.replace('_', ' ').title()
        
        if question_type == 'definição':
            message_parts.append(f"📚 **{topic_display} - Conceito e Definição**\n")
        elif question_type == 'como_fazer':
            message_parts.append(f"⚡ **Como trabalhar com {topic_display}**\n")
        elif question_type == 'exemplo':
            message_parts.append(f"💡 **Exemplos práticos de {topic_display}**\n")
        else:
            message_parts.append(f"🎯 **Vamos falar sobre {topic_display}**\n")
        
        # PRIORIDADE: Conteúdo estruturado PRIMEIRO
        content = explanation.get('content', {})
        
        # 1. Introdução estruturada
        if 'introducao' in content and content['introducao']:
            message_parts.append(content['introducao'])
            message_parts.append("")
        
        # 2. Exemplo prático estruturado (PRINCIPAL)
        # Obtém dados do tópico diretamente do content generator
        from .content_generator import ContentGenerator
        cg = ContentGenerator()
        topic_data = cg.topic_content.get(topic, {})
        
        if 'exemplo_detalhado' in topic_data:
            message_parts.append("💻 **Exemplo prático:**")
            example = topic_data['exemplo_detalhado']
            # Detecta linguagem do código
            if topic in ['formatacao_texto', 'html_basico', 'css_basico']:
                message_parts.append(f"```html\n{example}\n```")
            else:
                message_parts.append(f"```python\n{example}\n```")
            message_parts.append("")
        elif 'exemplo_pratico' in topic_data:
            message_parts.append("💡 **Exemplo:**")
            message_parts.append(topic_data['exemplo_pratico'])
            message_parts.append("")
        
        # 3. Só usa contexto dos PDFs se NÃO tiver conteúdo estruturado
        if not topic_data and search_results:
            best_result = search_results[0]
            if best_result.get('similarity', 0) > 0.3:
                message_parts.append("📖 **Conteúdo encontrado nos materiais:**")
                content_snippet = best_result.get('content', '')[:200]
                if len(content_snippet) > 50:
                    message_parts.append(f"*{content_snippet}...*")
                message_parts.append("")
        
        # 4. Adiciona outras seções do conteúdo estruturado
        if 'pratica' in content and content['pratica']:
            message_parts.append("🎯 **Para praticar:**")
            message_parts.append(content['pratica'])
            message_parts.append("")
        
        # 5. Conclusão estruturada se disponível
        if 'conclusao' in content:
            conclusao_text = content['conclusao']
            if conclusao_text and '[conteúdo não disponível]' not in conclusao_text and len(conclusao_text.strip()) > 10:
                message_parts.append(conclusao_text)
                message_parts.append("")
        
        return '\n'.join(message_parts)
    
    def _generate_fallback_response(self, user_input: str, search_results: List[Dict[str, Any]]) -> str:
        """Gera resposta quando não consegue identificar tópicos específicos."""
        
        message_parts = [
            "🤔 Entendo que você tem uma dúvida, mas preciso de mais clareza para te ajudar melhor.",
            ""
        ]
        
        # Se encontrou algo na busca, usa isso
        if search_results:
            message_parts.extend([
                "📚 **Encontrei algumas informações que podem ser relevantes:**",
                ""
            ])
            
            for i, result in enumerate(search_results[:2], 1):
                content = result.get('content', '')[:150]
                source_type = result.get('source_type', 'conteúdo')
                message_parts.append(f"**{i}. De {source_type}:**")
                message_parts.append(f"*{content}...*")
                message_parts.append("")
        
        message_parts.extend([
            "💬 **Para te ajudar melhor, você poderia:**",
            "• Reformular sua pergunta de forma mais específica",
            "• Mencionar qual tópico de programação te interessa",
            "• Dizer se está com dificuldade em algo específico",
            ""
        ])
        
        return '\n'.join(message_parts)
    
    def _format_found_resources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formata recursos encontrados na busca."""
        formatted_resources = []
        
        for result in search_results:
            resource = {
                'type': result.get('source_type', 'unknown'),
                'content_preview': result.get('content', '')[:100] + '...',
                'similarity': round(result.get('similarity', 0) * 100, 1),
                'metadata': result.get('metadata', {})
            }
            
            # Adiciona informações específicas por tipo
            metadata = result.get('metadata', {})
            
            if resource['type'] == 'pdf':
                resource['pages'] = metadata.get('total_pages')
                resource['source_file'] = metadata.get('source', '').split('/')[-1]
                
            elif resource['type'] == 'video':
                resource['duration'] = metadata.get('start_timestamp', '') + ' - ' + metadata.get('end_timestamp', '')
                resource['language'] = metadata.get('language')
                
            elif resource['type'] == 'image':
                resource['dimensions'] = f"{metadata.get('width', 'N/A')}x{metadata.get('height', 'N/A')}"
                resource['format'] = metadata.get('format')
            
            formatted_resources.append(resource)
        
        return formatted_resources
    
    def _generate_feedback_request(self, analysis: Dict[str, Any], user_profile) -> str:
        """Gera solicitação de feedback personalizada."""
        
        feedback_requests = []
        
        # Baseado no nível detectado
        if analysis['difficulty_level'] == Difficulty.INICIANTE:
            feedback_requests.extend([
                "Esta explicação ficou clara para você?",
                "Gostaria de ver mais exemplos práticos?",
                "Prefere que eu simplifique mais alguma parte?"
            ])
        else:
            feedback_requests.extend([
                "Esta abordagem atendeu sua necessidade?",
                "Gostaria de mais detalhes técnicos?",
                "Tem algum caso específico que gostaria de explorar?"
            ])
        
        # Baseado nas preferências (ou falta delas)
        if not user_profile.learning_preferences:
            feedback_requests.extend([
                "Como prefere aprender: vídeos, textos ou exercícios práticos?",
                "Que tipo de explicação funciona melhor para você?"
            ])
        
        # Seleciona uma pergunta aleatória
        import random
        return random.choice(feedback_requests) if feedback_requests else "Como posso melhorar minha ajuda?"
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Retorna dashboard com progresso de aprendizagem do usuário."""
        
        user_profile = self.difficulty_analyzer.user_profile
        
        dashboard = {
            'user_profile': self.difficulty_analyzer.get_user_profile_summary(),
            'learning_recommendations': self.difficulty_analyzer.get_learning_recommendations(),
            'session_stats': {
                'total_interactions': len(self.conversation_history),
                'session_duration_minutes': round((time.time() - self.session_start) / 60, 1),
                'topics_explored': list(set([
                    topic for interaction in self.conversation_history 
                    for topic in interaction['analysis']['detected_topics']
                ])),
                'average_response_time': round(sum([
                    interaction['processing_time'] 
                    for interaction in self.conversation_history
                ]) / len(self.conversation_history), 2) if self.conversation_history else 0
            },
            'progress_indicators': {
                'knowledge_gaps_identified': len(user_profile.knowledge_gaps),
                'strong_areas': len(user_profile.strong_topics),
                'learning_preferences_identified': len(user_profile.learning_preferences),
                'overall_level': user_profile.overall_level.value
            }
        }
        
        return dashboard
    
    def generate_study_plan(self, duration_weeks: int = 4) -> Dict[str, Any]:
        """Gera plano de estudos personalizado baseado no perfil do usuário."""
        
        user_profile = self.difficulty_analyzer.user_profile
        
        # Identifica tópicos para estudo (lacunas + tópicos explorados)
        topics_to_study = []
        
        # Prioriza lacunas de conhecimento
        for gap in user_profile.knowledge_gaps:
            topics_to_study.append(gap.topic)
        
        # Adiciona tópicos relacionados
        for gap in user_profile.knowledge_gaps:
            topics_to_study.extend(gap.related_topics)
        
        # Remove duplicatas
        topics_to_study = list(set(topics_to_study))
        
        # Se não há lacunas identificadas, usa tópicos da conversa
        if not topics_to_study:
            topics_to_study = list(set([
                topic for interaction in self.conversation_history[-5:]  # Últimas 5 interações
                for topic in interaction['analysis']['detected_topics']
            ]))
        
        # Gera plano usando o content generator
        study_plan = self.content_generator.generate_study_plan(
            user_profile, topics_to_study, duration_weeks
        )
        
        return study_plan
    
    def reset_session(self):
        """Reinicia a sessão mantendo aprendizados do perfil do usuário."""
        self.conversation_history = []
        self.session_start = time.time()
        # Nota: Mantém o perfil do usuário para continuidade do aprendizado
    
    def export_session_data(self) -> Dict[str, Any]:
        """Exporta dados da sessão para análise ou backup."""
        return {
            'session_start': self.session_start,
            'session_duration': time.time() - self.session_start,
            'user_profile': self.difficulty_analyzer.get_user_profile_summary(),
            'conversation_history': [
                {
                    'timestamp': interaction['timestamp'],
                    'user_input': interaction['user_input'],
                    'detected_topics': interaction['analysis']['detected_topics'],
                    'difficulty_level': interaction['analysis']['difficulty_level'].value,
                    'response_preview': interaction['response']['message'][:100] + '...'
                }
                for interaction in self.conversation_history
            ],
            'learning_progress': {
                'topics_explored': list(set([
                    topic for interaction in self.conversation_history
                    for topic in interaction['analysis']['detected_topics']
                ])),
                'total_interactions': len(self.conversation_history)
            }
        } 