"""Gerador de conteúdo adaptativo baseado no perfil e dificuldades do usuário."""

from typing import Dict, List, Any, Optional
from .difficulty_analyzer import Difficulty, LearningPreference, UserProfile
import random
import json


class ContentGenerator:
    """Gera conteúdo personalizado baseado no perfil do usuário e dados indexados."""
    
    def __init__(self):
        """Inicializa o gerador de conteúdo."""
        # Templates para diferentes tipos de explicação
        self.explanation_templates = {
            'simples': {
                'introducao': "Vamos começar do básico! {conceito} é {definicao_simples}.",
                'exemplo': "Por exemplo: {exemplo_pratico}",
                'pratica': "Que tal tentarmos um exercício simples? {exercicio}"
            },
            'detalhado': {
                'introducao': "{conceito} é {definicao_completa}.",
                'contexto': "Isso é importante porque {importancia}.",
                'exemplo': "Vamos ver um exemplo prático: {exemplo_detalhado}",
                'pratica': "Para praticar, tente resolver: {exercicio_intermediario}",
                'recursos': "Para saber mais, consulte: {recursos_extras}"
            },
            'tecnico': {
                'introducao': "{conceito}: {definicao_tecnica}",
                'especificacoes': "Especificações técnicas: {detalhes_tecnicos}",
                'implementacao': "Implementação: {codigo_exemplo}",
                'otimizacao': "Considerações de performance: {otimizacoes}",
                'recursos': "Documentação adicional: {docs_tecnicas}"
            }
        }
        
        # Conteúdo base por tópico
        self.topic_content = {
            'variaveis': {
                'definicao_simples': 'como caixinhas onde guardamos informações',
                'definicao_completa': 'espaços na memória que armazenam dados que podem mudar durante a execução do programa',
                'definicao_tecnica': 'referências nomeadas para posições de memória que armazenam valores mutáveis',
                'exemplo_pratico': 'nome = "João" armazena o texto João na variável nome',
                'exemplo_detalhado': '''
# Declaração e uso de variáveis
nome = "Maria"        # String
idade = 25           # Inteiro
altura = 1.65        # Decimal
estudante = True     # Booleano
print(f"{nome} tem {idade} anos")
                ''',
                'exercicio': 'Crie uma variável chamada "cor_favorita" e atribua sua cor preferida a ela.',
                'exercicio_intermediario': 'Crie variáveis para nome, idade e salário de uma pessoa, depois imprima uma frase completa usando essas informações.'
            },
            'funcoes': {
                'definicao_simples': 'blocos de código reutilizáveis que executam uma tarefa específica',
                'definicao_completa': 'estruturas que encapsulam código para realizar operações específicas, podendo receber parâmetros e retornar valores',
                'definicao_tecnica': 'subrotinas que implementam abstração procedimental, permitindo modularização e reutilização de código',
                'exemplo_pratico': 'def cumprimentar(): print("Olá!") - cria uma função que diz olá',
                'exemplo_detalhado': '''
def calcular_area_retangulo(largura, altura):
    """Calcula a área de um retângulo"""
    area = largura * altura
    return area

# Uso da função
resultado = calcular_area_retangulo(5, 3)
print(f"A área é: {resultado}")
                ''',
                'exercicio': 'Crie uma função que receba seu nome e imprima "Olá, [seu nome]!"',
                'exercicio_intermediario': 'Crie uma função que calcule a média de três notas e retorne se o aluno foi aprovado (média >= 7).'
            },
            'loops': {
                'definicao_simples': 'estruturas que repetem o mesmo código várias vezes',
                'definicao_completa': 'estruturas de controle que executam um bloco de código repetidamente enquanto uma condição for verdadeira',
                'definicao_tecnica': 'construtos iterativos que implementam execução repetitiva controlada por predicados ou contadores',
                'exemplo_pratico': 'for i in range(3): print(i) - imprime 0, 1, 2',
                'exemplo_detalhado': '''
# Loop for com range
for i in range(1, 6):
    print(f"Número: {i}")

# Loop while
contador = 0
while contador < 5:
    print(f"Contador: {contador}")
    contador += 1

# Loop através de lista
frutas = ["maçã", "banana", "laranja"]
for fruta in frutas:
    print(f"Fruta: {fruta}")
                ''',
                'exercicio': 'Use um loop para imprimir os números de 1 a 5',
                'exercicio_intermediario': 'Crie um programa que calcule a soma de todos os números de 1 a 100 usando um loop.'
            },
            'listas_arrays': {
                'definicao_simples': 'coleções ordenadas onde podemos guardar vários valores juntos',
                'definicao_completa': 'estruturas de dados que armazenam múltiplos elementos em uma sequência ordenada, acessíveis por índice',
                'definicao_tecnica': 'estruturas de dados indexadas que implementam coleções mutáveis de elementos heterogêneos',
                'exemplo_pratico': 'frutas = ["maçã", "banana", "laranja"] cria uma lista com 3 frutas',
                'exemplo_detalhado': '''
# Criando listas
numeros = [1, 2, 3, 4, 5]
frutas = ["maçã", "banana", "laranja"]
mista = [1, "texto", 3.14, True]

# Acessando elementos
print(frutas[0])  # "maçã" - primeiro elemento
print(frutas[-1]) # "laranja" - último elemento

# Modificando listas
frutas.append("uva")      # Adiciona no final
frutas.insert(1, "pêra")  # Insere na posição 1
print(frutas)             # ['maçã', 'pêra', 'banana', 'laranja', 'uva']
                ''',
                'exercicio': 'Crie uma lista com seus 3 filmes favoritos e imprima o primeiro da lista.',
                'exercicio_intermediario': 'Crie uma lista de números de 1 a 10, depois remova os números pares e imprima o resultado.'
            },
            'strings': {
                'definicao_simples': 'textos ou sequências de caracteres que usamos para armazenar palavras e frases',
                'definicao_completa': 'sequências imutáveis de caracteres Unicode usadas para representar dados textuais',
                'definicao_tecnica': 'objetos imutáveis que implementam sequências de pontos de código Unicode',
                'exemplo_pratico': 'nome = "João" cria uma string com o texto João',
                'exemplo_detalhado': '''
# Criando strings
mensagem = "Olá, mundo!"
nome_completo = "João Silva"
descricao = """Este é um texto
com múltiplas linhas"""

# Operações básicas com strings
print(len(mensagem))           # Tamanho: 11
print(mensagem.upper())        # MAIÚSCULA: "OLÁ, MUNDO!"
print(mensagem.lower())        # minúscula: "olá, mundo!"

# Concatenação
saudacao = "Olá, " + nome_completo
print(saudacao)                # "Olá, João Silva"

# Formatação moderna
idade = 25
print(f"{nome_completo} tem {idade} anos")
                ''',
                'exercicio': 'Crie uma string com seu nome completo e imprima apenas a primeira letra.',
                'exercicio_intermediario': 'Crie um programa que conte quantas vogais existem em uma frase digitada pelo usuário.'
            },
            'formatacao_texto': {
                'definicao_simples': 'técnicas para dar aparência e estilo visual aos textos em páginas web',
                'definicao_completa': 'conjunto de propriedades CSS que controlam a apresentação visual de elementos de texto',
                'definicao_tecnica': 'aplicação de estilos cascata para controlar tipografia, cores e layout de conteúdo textual',
                'exemplo_pratico': 'color: blue; font-weight: bold; muda a cor para azul e deixa em negrito',
                'exemplo_detalhado': '''
/* CSS para formatação de texto */
.titulo {
    color: #333;           /* Cor cinza escuro */
    font-size: 24px;       /* Tamanho da fonte */
    font-weight: bold;     /* Texto em negrito */
    text-align: center;    /* Centralizado */
}

.paragrafo {
    color: #666;           /* Cor cinza médio */
    font-family: Arial;    /* Fonte Arial */
    line-height: 1.5;      /* Espaçamento entre linhas */
    margin-bottom: 10px;   /* Margem inferior */
}

/* HTML usando as classes */
<h1 class="titulo">Meu Título</h1>
<p class="paragrafo">Este é um parágrafo com estilo.</p>
                ''',
                'exercicio': 'Crie um CSS que deixe um título vermelho e em negrito.',
                'exercicio_intermediario': 'Crie estilos para um artigo com título, subtítulo e parágrafos, cada um com cores e tamanhos diferentes.'
            },
            'html_basico': {
                'definicao_simples': 'linguagem de marcação usada para criar estrutura de páginas web',
                'definicao_completa': 'HyperText Markup Language - linguagem que define a estrutura e conteúdo de documentos web usando elementos e tags',
                'definicao_tecnica': 'linguagem declarativa baseada em elementos aninhados que define a semântica estrutural de documentos hipertexto',
                'exemplo_pratico': '<h1>Título</h1> cria um título principal na página',
                'exemplo_detalhado': '''
<!DOCTYPE html>
<html>
<head>
    <title>Minha Primeira Página</title>
</head>
<body>
    <h1>Título Principal</h1>
    <h2>Subtítulo</h2>
    <p>Este é um parágrafo com <strong>texto em negrito</strong>.</p>
    <ul>
        <li>Item 1 da lista</li>
        <li>Item 2 da lista</li>
    </ul>
    <a href="https://google.com">Link para Google</a>
</body>
</html>
                ''',
                'exercicio': 'Crie uma página HTML simples com um título e um parágrafo.',
                'exercicio_intermediario': 'Crie uma página sobre você com título, descrição, lista de hobbies e um link para suas redes sociais.'
            }
        }
        
        # Recursos por formato preferido
        self.format_resources = {
            LearningPreference.VIDEO: {
                'plataformas': ['YouTube', 'Coursera', 'Udemy'],
                'sugestoes': [
                    'Procure por tutoriais visuais do tópico',
                    'Assista aulas práticas com demonstrações',
                    'Use vídeos com legendas para melhor compreensão'
                ]
            },
            LearningPreference.TEXTO: {
                'plataformas': ['MDN', 'W3Schools', 'documentação oficial'],
                'sugestoes': [
                    'Leia documentação oficial',
                    'Consulte tutoriais escritos passo-a-passo',
                    'Faça anotações dos conceitos principais'
                ]
            },
            LearningPreference.PRATICO: {
                'plataformas': ['Replit', 'CodePen', 'GitHub'],
                'sugestoes': [
                    'Pratique com exercícios hands-on',
                    'Crie pequenos projetos pessoais',
                    'Participe de coding challenges'
                ]
            },
            LearningPreference.VISUAL: {
                'plataformas': ['Diagrams.net', 'Miro', 'Canva'],
                'sugestoes': [
                    'Use diagramas e flowcharts',
                    'Crie mapas mentais dos conceitos',
                    'Visualize dados com gráficos'
                ]
            }
        }
    
    def generate_personalized_explanation(self, 
                                        topic: str, 
                                        user_profile: UserProfile, 
                                        search_results: List[Dict] = None) -> Dict[str, Any]:
        """Gera explicação personalizada baseada no perfil do usuário."""
        
        # Determina o estilo de explicação
        style = user_profile.preferred_explanation_style
        template = self.explanation_templates.get(style, self.explanation_templates['simples'])
        
        # Obtém conteúdo base do tópico
        topic_data = self.topic_content.get(topic, {})
        if not topic_data:
            return self._generate_generic_explanation(topic, style, search_results)
        
        # Monta explicação personalizada
        explanation = {
            'topic': topic,
            'style': style,
            'user_level': user_profile.overall_level.value,
            'topic_data': topic_data,  # IMPORTANTE: Adiciona dados do tópico
            'content': {},
            'resources': [],
            'next_steps': []
        }
        
        # Preenche conteúdo baseado no template
        for section, template_text in template.items():
            content_key = section
            if section in ['introducao', 'conclusao']:
                content_key = 'content_text'
            
            # Substitui placeholders com conteúdo específico
            filled_content = self._fill_template(template_text, topic, topic_data, search_results)
            explanation['content'][section] = filled_content
        
        # Adiciona recursos baseados nas preferências
        explanation['resources'] = self._generate_learning_resources(
            topic, user_profile.learning_preferences, user_profile.overall_level
        )
        
        # Sugere próximos passos
        explanation['next_steps'] = self._generate_next_steps(topic, user_profile)
        
        return explanation
    
    def _fill_template(self, template: str, topic: str, topic_data: Dict, search_results: List[Dict] = None) -> str:
        """Preenche template com dados específicos."""
        # Dados básicos para substituição
        substitutions = {
            'conceito': topic.replace('_', ' ').title(),
            **topic_data
        }
        
        # Adiciona conteúdo dos resultados de busca se disponível
        if search_results:
            relevant_content = self._extract_relevant_content(search_results, topic)
            substitutions.update(relevant_content)
        
        # Adiciona valores padrão para chaves comuns que podem faltar
        default_values = {
            'resumo_simples': f'Em resumo, {topic.replace("_", " ")} é um conceito fundamental em programação.',
            'resumo_detalhado': f'Para concluir, dominar {topic.replace("_", " ")} é essencial para seu desenvolvimento como programador.',
            'contexto_adicional': '',
            'exemplos_reais': '',
            'detalhes_extras': ''
        }
        
        # Atualiza com valores padrão apenas para chaves que não existem
        for key, default_value in default_values.items():
            if key not in substitutions:
                substitutions[key] = default_value
        
        # Substitui placeholders
        try:
            filled_template = template.format(**substitutions)
            
            # Remove linhas que ficaram vazias ou com apenas "[conteúdo não disponível]"
            lines = filled_template.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                if line and '[conteúdo não disponível]' not in line and line != '.':
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines) if clean_lines else f"Vamos explorar {topic.replace('_', ' ').title()}!"
            
        except KeyError as e:
            # Se ainda houver erro, retorna mensagem simples
            return f"Vamos aprender sobre {topic.replace('_', ' ').title()}!"
    
    def _extract_relevant_content(self, search_results: List[Dict], topic: str) -> Dict[str, str]:
        """Extrai conteúdo relevante dos resultados de busca."""
        if not search_results:
            return {}
        
        # Pega os primeiros resultados mais relevantes
        top_results = search_results[:3]
        
        extracted = {
            'contexto_adicional': '',
            'exemplos_reais': '',
            'detalhes_extras': ''
        }
        
        for result in top_results:
            content = result.get('content', '')
            if len(content) > 100:  # Conteúdo substancial
                # Extrai trecho relevante
                sentences = content.split('.')[:2]  # Primeiras 2 frases
                extracted['contexto_adicional'] += ' '.join(sentences) + '. '
        
        return extracted
    
    def _generate_generic_explanation(self, topic: str, style: str, search_results: List[Dict] = None) -> Dict[str, Any]:
        """Gera explicação genérica quando não há conteúdo específico."""
        explanation = {
            'topic': topic,
            'style': style,
            'content': {
                'introducao': f'Vamos explorar o tópico: {topic.replace("_", " ").title()}',
                'conteudo': 'Este é um tópico importante na programação.',
                'recursos': 'Consulte a documentação oficial para mais detalhes.'
            },
            'resources': [],
            'next_steps': [
                'Pesquise mais sobre este tópico',
                'Pratique com exemplos básicos',
                'Consulte documentação oficial'
            ]
        }
        
        # Adiciona conteúdo dos resultados de busca se disponível
        if search_results:
            relevant_content = self._extract_relevant_content(search_results, topic)
            explanation['content']['conteudo'] = relevant_content.get('contexto_adicional', explanation['content']['conteudo'])
        
        return explanation
    
    def _generate_learning_resources(self, topic: str, preferences: List[LearningPreference], level: Difficulty) -> List[Dict[str, Any]]:
        """Gera recursos de aprendizagem personalizados."""
        resources = []
        
        # Se não há preferências, usa padrões baseados no nível
        if not preferences:
            if level == Difficulty.INICIANTE:
                preferences = [LearningPreference.VIDEO, LearningPreference.PRATICO]
            else:
                preferences = [LearningPreference.TEXTO, LearningPreference.PRATICO]
        
        # Gera recursos para cada preferência
        for pref in preferences:
            resource_data = self.format_resources.get(pref, {})
            
            resource = {
                'type': pref.value,
                'title': f'{pref.value.title()} sobre {topic.replace("_", " ").title()}',
                'platforms': resource_data.get('plataformas', []),
                'suggestions': resource_data.get('sugestoes', []),
                'difficulty': level.value
            }
            
            resources.append(resource)
        
        return resources
    
    def _generate_next_steps(self, topic: str, user_profile: UserProfile) -> List[str]:
        """Gera próximos passos personalizados."""
        steps = []
        
        # Passos baseados no nível
        if user_profile.overall_level == Difficulty.INICIANTE:
            steps = [
                f'Pratique os conceitos básicos de {topic.replace("_", " ")}',
                'Faça exercícios simples para fixar o conhecimento',
                'Assista tutoriais introdutórios sobre o tópico'
            ]
        elif user_profile.overall_level == Difficulty.INTERMEDIARIO:
            steps = [
                f'Aprofunde seu conhecimento em {topic.replace("_", " ")}',
                'Resolva problemas práticos usando este conceito',
                'Explore variações e casos especiais'
            ]
        else:
            steps = [
                f'Explore aspectos avançados de {topic.replace("_", " ")}',
                'Analise implementações otimizadas',
                'Contribua com projetos open source relacionados'
            ]
        
        # Adiciona passos baseados nas lacunas de conhecimento
        related_gaps = [gap.topic for gap in user_profile.knowledge_gaps 
                       if any(related in gap.related_topics for related in [topic])]
        
        if related_gaps:
            steps.append(f'Também estude: {", ".join(related_gaps[:2])}')
        
        return steps
    
    def generate_interactive_exercise(self, topic: str, level: Difficulty) -> Dict[str, Any]:
        """Gera exercício interativo baseado no tópico e nível."""
        exercises = {
            'variaveis': {
                Difficulty.INICIANTE: {
                    'question': 'Crie uma variável chamada "minha_idade" e atribua sua idade a ela. Depois imprima o valor.',
                    'hint': 'Use: minha_idade = [sua idade] e print(minha_idade)',
                    'solution': 'minha_idade = 25\nprint(minha_idade)',
                    'explanation': 'Variáveis são criadas com o operador = (atribuição)'
                },
                Difficulty.INTERMEDIARIO: {
                    'question': 'Crie variáveis para armazenar nome, idade e salário de uma pessoa. Calcule o salário anual e imprima uma frase completa.',
                    'hint': 'Lembre-se de multiplicar o salário mensal por 12',
                    'solution': 'nome = "João"\nidade = 30\nsalario_mensal = 5000\nsalario_anual = salario_mensal * 12\nprint(f"{nome}, {idade} anos, ganha R${salario_anual} por ano")',
                    'explanation': 'Podemos combinar diferentes tipos de variáveis em cálculos e strings formatadas'
                }
            },
            'funcoes': {
                Difficulty.INICIANTE: {
                    'question': 'Crie uma função chamada "dizer_ola" que imprima "Olá, mundo!"',
                    'hint': 'Use def nome_funcao(): seguido do código indentado',
                    'solution': 'def dizer_ola():\n    print("Olá, mundo!")\n\ndizer_ola()',
                    'explanation': 'Funções são definidas com def e chamadas usando seu nome seguido de ()'
                },
                Difficulty.INTERMEDIARIO: {
                    'question': 'Crie uma função que receba dois números e retorne a média deles.',
                    'hint': 'Use return para retornar o resultado da divisão por 2',
                    'solution': 'def calcular_media(num1, num2):\n    media = (num1 + num2) / 2\n    return media\n\nresultado = calcular_media(8, 6)\nprint(resultado)',
                    'explanation': 'Funções podem receber parâmetros e retornar valores usando return'
                }
            }
        }
        
        topic_exercises = exercises.get(topic, {})
        exercise = topic_exercises.get(level)
        
        if not exercise:
            # Exercício genérico se não houver específico
            exercise = {
                'question': f'Pratique conceitos relacionados a {topic.replace("_", " ")}',
                'hint': 'Consulte a documentação oficial para exemplos',
                'solution': 'Varia dependendo da implementação',
                'explanation': f'Este tópico é importante para o desenvolvimento em programação'
            }
        
        return {
            'topic': topic,
            'level': level.value,
            'type': 'coding_exercise',
            **exercise
        }
    
    def generate_quiz_questions(self, topic: str, level: Difficulty, num_questions: int = 3) -> List[Dict[str, Any]]:
        """Gera questões de quiz baseadas no tópico e nível."""
        
        quiz_bank = {
            'variaveis': {
                Difficulty.INICIANTE: [
                    {
                        'question': 'Qual símbolo é usado para atribuir um valor a uma variável em Python?',
                        'options': ['=', '==', '->', ':='],
                        'correct': 0,
                        'explanation': 'O símbolo = é usado para atribuição, while == é usado para comparação'
                    },
                    {
                        'question': 'Qual nome de variável é INVÁLIDO em Python?',
                        'options': ['minha_idade', '2nome', 'nome2', '_nome'],
                        'correct': 1,
                        'explanation': 'Nomes de variáveis não podem começar com números'
                    }
                ],
                Difficulty.INTERMEDIARIO: [
                    {
                        'question': 'O que acontece quando você tenta usar uma variável não declarada?',
                        'options': ['Retorna 0', 'Retorna None', 'Gera NameError', 'Cria automaticamente'],
                        'correct': 2,
                        'explanation': 'Python gera um NameError quando tenta usar uma variável não definida'
                    }
                ]
            },
            'funcoes': {
                Difficulty.INICIANTE: [
                    {
                        'question': 'Qual palavra-chave é usada para criar uma função em Python?',
                        'options': ['function', 'def', 'func', 'create'],
                        'correct': 1,
                        'explanation': 'A palavra-chave "def" é usada para definir funções em Python'
                    }
                ]
            }
        }
        
        topic_questions = quiz_bank.get(topic, {}).get(level, [])
        
        # Se não há questões específicas, gera questões genéricas
        if not topic_questions:
            topic_questions = [{
                'question': f'Qual é um conceito importante relacionado a {topic.replace("_", " ")}?',
                'options': ['Opção A', 'Opção B', 'Opção C', 'Opção D'],
                'correct': 0,
                'explanation': 'Esta é uma questão de exemplo. Consulte materiais específicos para questões detalhadas.'
            }]
        
        # Retorna questões aleatórias até o número solicitado
        selected_questions = random.sample(topic_questions, min(num_questions, len(topic_questions)))
        
        return [
            {
                'id': i + 1,
                'topic': topic,
                'level': level.value,
                **question
            }
            for i, question in enumerate(selected_questions)
        ]
    
    def generate_study_plan(self, user_profile: UserProfile, topics: List[str], duration_weeks: int = 4) -> Dict[str, Any]:
        """Gera plano de estudos personalizado."""
        
        plan = {
            'duration_weeks': duration_weeks,
            'user_level': user_profile.overall_level.value,
            'learning_preferences': [pref.value for pref in user_profile.learning_preferences],
            'weekly_schedule': [],
            'resources': [],
            'milestones': []
        }
        
        # Organiza tópicos por prioridade (lacunas de conhecimento primeiro)
        priority_topics = []
        gap_topics = [gap.topic for gap in user_profile.knowledge_gaps]
        
        # Adiciona tópicos com lacunas primeiro
        for topic in topics:
            if topic in gap_topics:
                priority_topics.append((topic, 'high_priority'))
        
        # Adiciona outros tópicos
        for topic in topics:
            if topic not in gap_topics:
                priority_topics.append((topic, 'normal_priority'))
        
        # Distribui tópicos por semanas
        topics_per_week = max(1, len(priority_topics) // duration_weeks)
        
        for week in range(duration_weeks):
            start_idx = week * topics_per_week
            end_idx = min(start_idx + topics_per_week, len(priority_topics))
            week_topics = priority_topics[start_idx:end_idx]
            
            week_plan = {
                'week': week + 1,
                'topics': [topic for topic, _ in week_topics],
                'priority_topics': [topic for topic, priority in week_topics if priority == 'high_priority'],
                'activities': self._generate_week_activities(
                    [topic for topic, _ in week_topics], 
                    user_profile
                ),
                'time_estimate': '5-8 horas'
            }
            
            plan['weekly_schedule'].append(week_plan)
        
        # Adiciona marcos importantes
        plan['milestones'] = [
            f'Semana {week}: Dominar {", ".join(week_plan["topics"])}'
            for week, week_plan in enumerate(plan['weekly_schedule'], 1)
        ]
        
        return plan
    
    def _generate_week_activities(self, topics: List[str], user_profile: UserProfile) -> List[Dict[str, str]]:
        """Gera atividades para uma semana específica."""
        activities = []
        
        for topic in topics:
            # Atividade baseada nas preferências do usuário
            if LearningPreference.VIDEO in user_profile.learning_preferences:
                activities.append({
                    'type': 'video',
                    'description': f'Assistir tutoriais sobre {topic.replace("_", " ")}',
                    'estimated_time': '1-2 horas'
                })
            
            if LearningPreference.PRATICO in user_profile.learning_preferences:
                activities.append({
                    'type': 'practice',
                    'description': f'Fazer exercícios práticos de {topic.replace("_", " ")}',
                    'estimated_time': '2-3 horas'
                })
            
            activities.append({
                'type': 'reading',
                'description': f'Ler documentação sobre {topic.replace("_", " ")}',
                'estimated_time': '30-45 min'
            })
            
            activities.append({
                'type': 'quiz',
                'description': f'Fazer quiz de {topic.replace("_", " ")} para testar conhecimento',
                'estimated_time': '15-30 min'
            })
        
        return activities 