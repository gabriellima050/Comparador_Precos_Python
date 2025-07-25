📚 1. IMPORTAÇÕES - Por que cada biblioteca?
pythonimport streamlit as st

O que faz: Streamlit é uma biblioteca para criar aplicações web
Por que usar: Transforma código Python em uma página web bonita automaticamente
Exemplo: st.title() cria um título na página

pythonimport requests

O que faz: Faz requisições HTTP (buscar páginas da internet)
Por que usar: É como um "navegador" do Python - baixa o HTML dos sites
Exemplo: requests.get("https://mercadolivre.com.br") baixa a página

pythonfrom bs4 import BeautifulSoup

O que faz: "Beautiful Soup" analisa e extrai dados do HTML
Por que usar: HTML é complicado, BeautifulSoup facilita encontrar informações
Exemplo: soup.find('h2') encontra o primeiro título h2

pythonimport pandas as pd

O que faz: Pandas trabalha com tabelas de dados (como Excel)
Por que usar: Organiza os preços encontrados em uma tabela
Exemplo: pd.DataFrame() cria uma tabela

pythonimport plotly.express as px

O que faz: Cria gráficos interativos bonitos
Por que usar: Mostra a comparação de preços visualmente
Exemplo: px.bar() cria gráfico de barras

🏗️ 2. CONFIGURAÇÃO DA PÁGINA
pythonst.set_page_config(
    page_title="Comparador de Preços",
    page_icon="🛒",
    layout="wide"
)

O que faz: Define como a página web vai aparecer
page_title: Nome na aba do navegador
page_icon: Ícone na aba (emoji de carrinho)
layout="wide": Usa toda a largura da tela

🤖 3. CLASSE PriceComparator - O "Cérebro" do App
pythonclass PriceComparator:
    def __init__(self):

O que é uma classe: Como um "molde" que cria objetos com funções
init: Função especial que roda quando criamos o objeto
Por que usar: Organiza todas as funções relacionadas em um lugar

🕵️ User-Agents - Disfarce Digital
pythonself.user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    # mais navegadores...
]

O que são: "Identidades falsas" que o código usa
Por que: Sites bloqueiam robôs, então fingimos ser navegadores reais
Como funciona: Cada requisição usa uma identidade diferente

🧹 Função clean_price - Limpeza de Preços
pythondef clean_price(self, price_text):
    if not price_text:
        return None

O que faz: Pega texto como "R$ 1.234,56" e vira número 1234.56
Por que: Sites escrevem preços de formas diferentes, precisamos padronizar
Regex: Expressões regulares encontram padrões no texto

pythonprice_patterns = [
    r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # R$ 1.234,56
    r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',        # 1.234,56
]

Regex explicada:

R\$: Procura "R$" literal
\s*: Zero ou mais espaços
\d{1,3}: 1 a 3 dígitos
(?:\.\d{3})*: Grupos de ".123" (milhares)
(?:,\d{2})?: ",56" opcional (centavos)



🔍 4. FUNÇÕES DE BUSCA - Web Scraping
Mercado Livre:
pythondef search_mercadolivre(self, product):
    search_url = f"https://lista.mercadolivre.com.br/{quote_plus(product)}"

f-string: Forma moderna de juntar texto com variáveis
quote_plus: Converte "iPhone 13" em "iPhone+13" (URL segura)

pythonsession = requests.Session()
session.headers.update(self.get_headers())
response = session.get(search_url, timeout=15)

Session: Mantém "conversa" com o site (como manter login)
headers: "Cabeçalhos" que identificam nosso "navegador falso"
timeout=15: Desiste após 15 segundos se não responder

pythonif response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

status_code 200: "Deu certo!" (como "OK" do HTTP)
BeautifulSoup: Transforma HTML bagunçado em algo organizável
html.parser: Forma de interpretar o HTML

Seletores CSS:
pythonselectors = [
    {'title': 'h2.ui-search-item__title', 'price': '.andes-money-amount__fraction'},
    {'title': '.ui-search-item__title', 'price': '.price-tag-fraction'},
]

O que são: "Endereços" dos elementos no HTML
Por que múltiplos: Sites mudam design, então tentamos várias formas
CSS Selector: Linguagem para encontrar elementos (como GPS do HTML)

🎲 5. DADOS SIMULADOS - Plano B
pythondef generate_mock_data(self, product):
    base_prices = {
        'iphone': 3500,
        'notebook': 2800,
        'mouse': 80,
    }

O que faz: Quando sites bloqueiam, cria dados falsos realistas
Por que: Mantém o app funcionando para demonstração
Como: Baseado no produto, estima preços e adiciona variação aleatória

pythonvariation = random.uniform(0.8, 1.3)  # ±30% de variação
price = round(base_price * variation, 2)

random.uniform: Número aleatório entre 0.8 e 1.3
round(..., 2): Arredonda para 2 casas decimais (centavos)

📊 6. ANÁLISE DE DADOS
pythondef analyze_deals(self, results):
    prices = [r['preco'] for r in results]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)

List comprehension: [r['preco'] for r in results] extrai só os preços
min/max/sum: Funções matemáticas básicas
len(): Conta quantos itens tem na lista

pythonsavings_percent = (savings / max_price) * 100 if max_price > 0 else 0

Operador ternário: "Se max_price > 0, calcula %, senão retorna 0"
Por que: Evita divisão por zero (erro matemático)

🎨 7. INTERFACE STREAMLIT
pythonst.title("🛒 Comparador de Preços Inteligente")
st.markdown("Compare preços em diferentes plataformas...")

st.title: Cria título grande na página
st.markdown: Aceita texto com formatação (negrito, emojis, etc.)

pythonwith st.sidebar:
    st.header("ℹ️ Como usar")

sidebar: Barra lateral (como menu)
with: Contexto - tudo dentro vai para a sidebar

pythoncol1, col2 = st.columns([3, 1])
with col1:
    product = st.text_input("🔍 Digite o produto...")
with col2:
    search_button = st.button("🔍 Comparar Preços")

st.columns([3, 1]): Divide tela em 2 colunas (3/4 e 1/4 da largura)
st.text_input: Caixa de texto para usuário digitar
st.button: Botão clicável

⚡ 8. LÓGICA PRINCIPAL
pythonif search_button and product:
    comparator = PriceComparator()
    results = comparator.compare_prices(product)

if search_button and product: Só executa se botão foi clicado E tem texto
Instanciação: Cria um objeto da classe PriceComparator
Chama método: Executa a busca de preços

pythonwith st.spinner("🔍 Buscando preços..."):
    results = comparator.compare_prices(product)

st.spinner: Mostra animação de "carregando" enquanto busca

📈 9. VISUALIZAÇÃO DE DADOS
pythonfig = px.bar(df_sorted, x='site', y='preco', 
            color='preco',
            color_continuous_scale='RdYlGn_r')

px.bar: Gráfico de barras do Plotly
x='site', y='preco': Eixo X são os sites, Y são os preços
color='preco': Cor das barras baseada no preço
RdYlGn_r: Escala de cor (Vermelho-Amarelo-Verde, reversa)

🔗 10. LINKS DINÂMICOS
pythonst.markdown(f"""
<a href="{result['link']}" target="_blank" style="
    background-color: #FF4B4B;
    color: white;
    padding: 0.25rem 0.75rem;
    text-decoration: none;
    border-radius: 0.25rem;
">{link_text}</a>
""", unsafe_allow_html=True)

HTML dentro do Python: Cria botão customizado
target="_blank": Abre em nova aba
unsafe_allow_html=True: Permite código HTML (Streamlit bloqueia por segurança)

🎓 CONCEITOS IMPORTANTES APRENDIDOS:

Web Scraping: Extrair dados de sites automaticamente
APIs REST: Como programas conversam pela internet
Regex: Encontrar padrões em textos
POO (Programação Orientada a Objetos): Organizar código em classes
Tratamento de Erros: try/except para lidar com problemas
Data Science básico: Manipular e visualizar dados
Interface de usuário: Criar apps web interativos

Este projeto combina várias áreas importantes da programação! É um excelente exemplo prático. 🚀
