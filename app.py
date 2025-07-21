"""
Sistema de Aprendizagem Adaptativa - +A Educação
Aplicação principal com interface Streamlit
"""

import streamlit as st
import os
import sys
from pathlib import Path
import time
import json
from typing import Dict, List, Any

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent / 'src'))

# Imports dos módulos personalizados
from src.indexing import TextIndexer, PDFIndexer, VideoIndexer, ImageIndexer
from src.adaptive_learning import AdaptivePromptSystem, DifficultyAnalyzer, ContentGenerator

# Configuração da página
st.set_page_config(
    page_title="Sistema de Aprendizagem Adaptativa - +A Educação",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #2c3e50;
        color: #ffffff !important;
    }
    
    .user-message {
        background-color: #34495e;
        border-left-color: #3498db;
        color: #ffffff !important;
    }
    
    .assistant-message {
        background-color: #27ae60;
        border-left-color: #2ecc71;
        color: #ffffff !important;
    }
    
    .chat-message strong {
        color: #ffffff !important;
    }
    
    /* Texto normal das mensagens - branco */
    .chat-message p {
        color: #ffffff !important;
    }
    
    .chat-message div {
        color: #ffffff !important;
    }
    
    .chat-message span {
        color: #ffffff !important;
    }
    
    /* Todos os elementos de texto das conversas */
    .chat-message * {
        color: #ffffff !important;
    }
    
    /* Blocos de código - texto amarelo/verde em fundo bem escuro */
    .chat-message pre {
        background-color: #1a1a1a !important;
        color: #00ff00 !important;
        border: 1px solid #555555 !important;
        border-radius: 5px !important;
        padding: 1rem !important;
    }
    
    .chat-message pre code {
        color: #00ff00 !important;
        background-color: transparent !important;
    }
    
    .chat-message code {
        color: #ffff00 !important;
        background-color: #1a1a1a !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
    }
    
    /* Elementos específicos do Streamlit */
    .stCode > div {
        background-color: #2e3440 !important;
    }
    
    .stCode code {
        color: #ffffff !important;
    }
    
    .metrics-container {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .resource-card {
        background-color: #2c3e50;
        color: #ffffff !important;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #17a2b8;
        margin-bottom: 0.5rem;
    }
    
    .resource-card * {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializa variáveis da sessão."""
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.indexers = {}
        st.session_state.adaptive_system = None
        st.session_state.chat_history = []
        st.session_state.indexing_progress = {}
        st.session_state.user_profile = None
        st.session_state.loading = False

def load_indexers():
    """Carrega e inicializa todos os indexadores."""
    
    with st.spinner("🔄 Inicializando sistema de indexação..."):
        try:
            # Inicializa indexadores
            st.session_state.indexers = {
                'text': TextIndexer(),
                'pdf': PDFIndexer(),
                'video': VideoIndexer(),
                'image': ImageIndexer()
            }
            
            # Inicializa sistema adaptativo
            st.session_state.adaptive_system = AdaptivePromptSystem(st.session_state.indexers)
            
            # Indexa dados da pasta resources
            index_resources_data()
            
            st.session_state.initialized = True
            st.success("✅ Sistema inicializado com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro na inicialização: {str(e)}")
            st.info("Continuando sem indexação de dados...")
            
            # Sistema mínimo sem indexação
            st.session_state.adaptive_system = AdaptivePromptSystem()
            st.session_state.initialized = True

def index_resources_data():
    """Indexa os dados da pasta resources."""
    
    resources_path = Path("resources")
    if not resources_path.exists():
        st.warning("⚠️ Pasta 'resources' não encontrada. Funcionando sem dados indexados.")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    files_to_process = list(resources_path.glob("*"))
    total_files = len(files_to_process)
    
    if total_files == 0:
        st.warning("⚠️ Nenhum arquivo encontrado na pasta resources.")
        return
    
    processed = 0
    
    for file_path in files_to_process:
        if file_path.is_file():
            status_text.text(f"Processando: {file_path.name}")
            
            try:
                # Determina o indexador baseado na extensão
                extension = file_path.suffix.lower()
                
                if extension in ['.txt']:
                    indexer = st.session_state.indexers['text']
                elif extension in ['.json']:
                    indexer = st.session_state.indexers['text']
                elif extension in ['.pdf']:
                    indexer = st.session_state.indexers['pdf']
                elif extension in ['.mp4', '.avi', '.mov']:
                    indexer = st.session_state.indexers['video']
                elif extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                    indexer = st.session_state.indexers['image']
                else:
                    st.warning(f"⚠️ Tipo de arquivo não suportado: {file_path.name}")
                    processed += 1
                    continue
                
                # Indexa o arquivo
                success = indexer.index_file(str(file_path))
                
                if success:
                    st.session_state.indexing_progress[file_path.name] = "✅ Sucesso"
                else:
                    st.session_state.indexing_progress[file_path.name] = "❌ Falha"
                    
            except Exception as e:
                st.session_state.indexing_progress[file_path.name] = f"❌ Erro: {str(e)[:50]}..."
            
            processed += 1
            progress_bar.progress(processed / total_files)
    
    status_text.text("✅ Indexação concluída!")
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()

def render_main_interface():
    """Renderiza a interface principal."""
    
    # Cabeçalho
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Sistema de Aprendizagem Adaptativa</h1>
        <p>+A Educação - Engenheiro de Inteligência Artificial</p>
        <p><em>Aprendizagem personalizada em fundamentos de programação</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_chat_interface()
    
    with col2:
        render_sidebar_info()

def render_chat_interface():
    """Renderiza a interface de chat."""
    
    st.subheader("💬 Conversa Adaptativa")
    
    # Container para o chat
    chat_container = st.container()
    
    # Exibe histórico do chat
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>🧑‍🎓 Você:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistente:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Mostra recursos adicionais se disponíveis
                if 'resources' in message and message['resources']:
                    with st.expander("📚 Recursos encontrados"):
                        for resource in message['resources'][:3]:
                            st.markdown(f"""
                            <div class="resource-card">
                                <strong>{resource['type'].title()}:</strong> {resource.get('content_preview', 'N/A')}<br>
                                <em>Relevância: {resource.get('similarity', 0)}%</em>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Mostra exercícios se disponíveis
                if 'exercises' in message and message['exercises']:
                    with st.expander("🎯 Exercício prático"):
                        exercise = message['exercises'][0]
                        st.write(f"**Pergunta:** {exercise['question']}")
                        if st.button(f"Ver dica 💡", key=f"hint_{i}"):
                            st.info(f"**Dica:** {exercise['hint']}")
                        if st.button(f"Ver solução 📝", key=f"solution_{i}"):
                            st.code(exercise['solution'], language='python')
                            st.success(f"**Explicação:** {exercise['explanation']}")
    
    # Input do usuário
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Digite sua pergunta sobre programação:",
            placeholder="Ex: O que são variáveis? Como usar loops? Preciso de ajuda com funções...",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("Enviar 🚀")
        with col2:
            if st.form_submit_button("Limpar conversa 🗑️"):
                st.session_state.chat_history = []
                st.session_state.adaptive_system.reset_session()
                st.rerun()
    
    if submit_button and user_input.strip():
        process_user_input(user_input)

def process_user_input(user_input: str):
    """Processa input do usuário e gera resposta adaptativa."""
    
    # Adiciona mensagem do usuário
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Processa com loading
    with st.spinner("🤔 Analisando sua pergunta e gerando resposta personalizada..."):
        try:
            # Gera resposta adaptativa
            response = st.session_state.adaptive_system.process_user_input(user_input)
            
            # Adiciona resposta do assistente
            assistant_message = {
                'role': 'assistant',
                'content': response['message'],
                'resources': response.get('found_resources', []),
                'exercises': response.get('exercises', []),
                'metadata': response.get('metadata', {})
            }
            
            st.session_state.chat_history.append(assistant_message)
            
            # Atualiza perfil do usuário
            st.session_state.user_profile = st.session_state.adaptive_system.difficulty_analyzer.get_user_profile_summary()
            
        except Exception as e:
            error_message = f"❌ Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_message
            })
    
    st.rerun()

def render_sidebar_info():
    """Renderiza informações laterais."""
    
    st.subheader("📊 Seu Progresso")
    
    # Perfil do usuário
    if st.session_state.user_profile:
        profile = st.session_state.user_profile
        
        st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
        st.metric("Nível Atual", profile['overall_level'].title())
        st.metric("Interações", profile['total_interactions'])
        st.metric("Tópicos com Dificuldade", profile['knowledge_gaps_count'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Preferências de aprendizagem
        if profile['learning_preferences']:
            st.subheader("🎯 Suas Preferências")
            for pref in profile['learning_preferences']:
                st.markdown(f"🏷️ **{pref.title()}**")
        
        # Tópicos dominados
        if profile['strong_topics']:
            st.subheader("✅ Tópicos Dominados")
            for topic in profile['strong_topics']:
                st.success(f"• {topic.replace('_', ' ').title()}")
        
        # Lacunas de conhecimento
        if profile['top_knowledge_gaps']:
            st.subheader("📚 Focar em:")
            for gap in profile['top_knowledge_gaps']:
                confidence = int(gap['confidence_score'] * 100)
                st.warning(f"• {gap['topic'].replace('_', ' ').title()} ({confidence}% de incerteza)")
    
    # Dashboard de aprendizagem
    if st.button("📈 Dashboard Completo"):
        show_learning_dashboard()
    
    # Plano de estudos
    if st.button("📅 Gerar Plano de Estudos"):
        show_study_plan()
    
    # Status da indexação
    with st.expander("🔍 Status da Indexação"):
        if st.session_state.indexing_progress:
            for file_name, status in st.session_state.indexing_progress.items():
                st.write(f"**{file_name}:** {status}")
        else:
            st.info("Nenhum arquivo indexado ainda.")

def show_learning_dashboard():
    """Mostra dashboard detalhado de aprendizagem."""
    
    dashboard = st.session_state.adaptive_system.get_learning_dashboard()
    
    st.subheader("📊 Dashboard de Aprendizagem")
    
    # Métricas da sessão
    session_stats = dashboard['session_stats']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Interações", session_stats['total_interactions'])
    with col2:
        st.metric("Duração (min)", session_stats['session_duration_minutes'])
    with col3:
        st.metric("Tópicos Explorados", len(session_stats['topics_explored']))
    with col4:
        st.metric("Tempo Resposta (s)", session_stats['average_response_time'])
    
    # Tópicos explorados
    if session_stats['topics_explored']:
        st.subheader("🎯 Tópicos Explorados nesta Sessão")
        topics_text = ", ".join([topic.replace('_', ' ').title() for topic in session_stats['topics_explored']])
        st.info(topics_text)
    
    # Recomendações
    recommendations = dashboard['learning_recommendations']
    if recommendations['priority_topics']:
        st.subheader("🚀 Próximos Passos Recomendados")
        for step in recommendations['next_steps'][:3]:
            st.write(f"• {step}")

def show_study_plan():
    """Mostra plano de estudos personalizado."""
    
    st.subheader("📅 Plano de Estudos Personalizado")
    
    # Opções do plano
    col1, col2 = st.columns(2)
    with col1:
        weeks = st.selectbox("Duração do plano:", [2, 4, 6, 8], index=1)
    with col2:
        if st.button("Gerar Plano"):
            with st.spinner("Gerando seu plano personalizado..."):
                study_plan = st.session_state.adaptive_system.generate_study_plan(weeks)
                
                st.success(f"✅ Plano de {weeks} semanas criado!")
                
                # Exibe o plano
                for week_plan in study_plan['weekly_schedule']:
                    with st.expander(f"📅 Semana {week_plan['week']} - {week_plan['time_estimate']}"):
                        st.write("**Tópicos:**")
                        for topic in week_plan['topics']:
                            st.write(f"• {topic.replace('_', ' ').title()}")
                        
                        st.write("**Atividades:**")
                        for activity in week_plan['activities'][:3]:  # Primeiras 3 atividades
                            st.write(f"• {activity['description']} ({activity['estimated_time']})")

def render_footer():
    """Renderiza rodapé da aplicação."""
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🏢 **+A Educação**\nMaior Plataforma de Educação do Brasil")
    
    with col2:
        st.info("🤖 **Sistema Adaptativo**\nIA personalizada para aprendizagem")
    
    with col3:
        st.info("📚 **Fundamentos de Programação**\nDesenvolvido para iniciantes e intermediários")

def main():
    """Função principal da aplicação."""
    
    initialize_session_state()
    
    # Inicialização do sistema
    if not st.session_state.initialized:
        st.title("🧠 Sistema de Aprendizagem Adaptativa")
        st.subheader("Inicializando sistema...")
        
        load_indexers()
        
        if st.session_state.initialized:
            st.rerun()
    else:
        # Interface principal
        render_main_interface()
        render_footer()

if __name__ == "__main__":
    main() 