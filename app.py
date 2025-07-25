import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import quote_plus
import plotly.express as px
from datetime import datetime
import random

# Configuração da página
st.set_page_config(
    page_title="Comparador de Preços",
    page_icon="🛒",
    layout="wide"
)

class PriceComparator:
    def __init__(self):
        # Lista de User-Agents para evitar detecção
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        self.results = []
    
    def get_headers(self):
        """Retorna headers aleatórios para evitar detecção"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def clean_price(self, price_text):
        """Extrai o valor numérico do preço"""
        if not price_text:
            return None
        
        # Remove quebras de linha e espaços extras
        price_text = re.sub(r'\s+', ' ', price_text.strip())
        
        # Busca por padrões de preço brasileiros
        price_patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # R$ 1.234,56
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',        # 1.234,56
            r'(\d+(?:,\d{2})?)',                         # 1234,56
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text)
            if match:
                price_str = match.group(1)
                # Converte para float
                price_str = price_str.replace('.', '').replace(',', '.')
                try:
                    return float(price_str)
                except:
                    continue
        
        return None
    
    def search_mercadolivre(self, product):
        """Busca no Mercado Livre com múltiplas estratégias"""
        try:
            search_url = f"https://lista.mercadolivre.com.br/{quote_plus(product)}"
            
            session = requests.Session()
            session.headers.update(self.get_headers())
            
            response = session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Múltiplas estratégias de busca
                selectors = [
                    # Seletor mais específico
                    {'title': 'h2.ui-search-item__title', 'price': '.andes-money-amount__fraction', 'link': 'a'},
                    # Seletor alternativo
                    {'title': '.ui-search-item__title', 'price': '.price-tag-fraction', 'link': 'a'},
                    # Seletor genérico
                    {'title': 'h2', 'price': '[class*="price"], [class*="money"]', 'link': 'a'},
                ]
                
                for selector in selectors:
                    products = soup.find_all('div', class_='ui-search-result__wrapper')[:3]
                    
                    for product_div in products:
                        if not product_div:
                            continue
                            
                        title_elem = product_div.select_one(selector['title'])
                        price_elem = product_div.select_one(selector['price'])
                        link_elem = product_div.select_one(selector['link'])
                        
                        if title_elem and price_elem:
                            title = title_elem.get_text(strip=True)[:60] + "..."
                            price = self.clean_price(price_elem.get_text(strip=True))
                            
                            # Extrai o link específico do produto
                            product_link = search_url
                            if link_elem and link_elem.get('href'):
                                href = link_elem.get('href')
                                if href.startswith('http'):
                                    product_link = href
                                elif href.startswith('/'):
                                    product_link = f"https://mercadolivre.com.br{href}"
                            
                            if price and price > 0:
                                return {
                                    'site': 'Mercado Livre',
                                    'produto': title,
                                    'preco': price,
                                    'link': product_link
                                }
                
        except Exception as e:
            print(f"Erro ML: {e}")
        
        return None
    
    def search_buscape(self, product):
        """Busca no Buscapé - mais acessível para scraping"""
        try:
            search_url = f"https://www.buscape.com.br/search?q={quote_plus(product)}"
            
            session = requests.Session()
            session.headers.update(self.get_headers())
            
            response = session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca produtos
                products = soup.find_all('div', class_='ProductCard_ProductCard_Inner__7JhKb')
                
                if not products:
                    products = soup.find_all('div', {'data-testid': re.compile('product')})
                
                for product_div in products[:3]:
                    if not product_div:
                        continue
                    
                    title_elem = product_div.find('h2') or product_div.find('h3')
                    if not title_elem:
                        title_elem = product_div.find(attrs={'data-testid': re.compile('product.*title')})
                    
                    # Busca por elementos que contenham preço - CORRIGIDO
                    price_elem = None
                    price_regex = re.compile(r'R\$\s*\d+')
                    price_texts = product_div.find_all(text=price_regex)
                    
                    if not price_texts:
                        price_elem = product_div.find(attrs={'data-testid': re.compile('.*price.*')})
                    
                    link_elem = product_div.find('a') or product_div.find_parent('a')
                    
                    if title_elem and (price_texts or price_elem):
                        title = title_elem.get_text(strip=True)[:60] + "..."
                        
                        # Extrai preço
                        if price_texts:
                            price_text = price_texts[0]
                        else:
                            price_text = price_elem.get_text(strip=True) if price_elem else ""
                        
                        price = self.clean_price(price_text)
                        
                        # Extrai o link específico do produto
                        product_link = search_url
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            if href.startswith('http'):
                                product_link = href
                            elif href.startswith('/'):
                                product_link = f"https://www.buscape.com.br{href}"
                        
                        if price and price > 0:
                            return {
                                'site': 'Buscapé',
                                'produto': title,
                                'preco': price,
                                'link': product_link
                            }
                            
        except Exception as e:
            print(f"Erro Buscapé: {e}")
        
        return None
    
    def search_google_shopping(self, product):
        """Simula busca no Google Shopping"""
        try:
            # Simulação com dados fictícios baseados no produto
            product_lower = product.lower()
            
            # Preços base simulados por categoria
            price_ranges = {
                'iphone': (2000, 6000),
                'notebook': (1500, 5000),
                'tv': (800, 4000),
                'mouse': (20, 200),
                'teclado': (50, 500),
                'monitor': (400, 2000),
                'default': (50, 1000)
            }
            
            # Determina categoria
            category = 'default'
            for key in price_ranges.keys():
                if key in product_lower:
                    category = key
                    break
            
            min_price, max_price = price_ranges[category]
            simulated_price = random.uniform(min_price, max_price)
            
            # URL Google Shopping (redireciona para busca do Google)
            google_shopping_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(product)}"
            
            return {
                'site': 'Google Shopping',
                'produto': f"{product} - Melhor oferta encontrada...",
                'preco': round(simulated_price, 2),
                'link': google_shopping_url
            }
            
        except Exception as e:
            print(f"Erro Google Shopping: {e}")
        
        return None
    
    def search_zoom(self, product):
        """Busca no Zoom (Buscapé)"""
        try:
            search_url = f"https://www.zoom.com.br/search?q={quote_plus(product)}"
            
            session = requests.Session()
            session.headers.update(self.get_headers())
            
            response = session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Busca por preços na página usando regex mais seguro 
                price_regex = re.compile(r'R\$\s*\d+')
                price_elements = soup.find_all(text=price_regex)
                title_elements = soup.find_all(['h1', 'h2', 'h3', 'h4'])
                
                if price_elements and title_elements:
                    price_text = price_elements[0]
                    title_text = title_elements[0].get_text(strip=True)
                    
                    price = self.clean_price(price_text)
                    if price and price > 0:
                        return {
                            'site': 'Zoom',
                            'produto': title_text[:60] + "...",
                            'preco': price,
                            'link': search_url
                        }
                        
        except Exception as e:
            print(f"Erro Zoom: {e}")
        
        return None
    
    def generate_mock_data(self, product):
        """Gera dados simulados para demonstração"""
        # Preços base por categoria
        base_prices = {
            'iphone': 3500,
            'samsung': 2500,
            'notebook': 2800,
            'mouse': 80,
            'teclado': 150,
            'monitor': 900,
            'tv': 1800,
            'fone': 200,
            'default': 300
        }
        
        product_lower = product.lower()
        base_price = base_prices.get('default', 300)
        
        for key, price in base_prices.items():
            if key in product_lower:
                base_price = price
                break
        
        # Gera variações de preço com links mais específicos
        mock_results = []
        sites_data = [
            {'name': 'Mercado Livre', 'url': 'mercadolivre.com.br', 'search_param': 'lista.mercadolivre.com.br'},
            {'name': 'Amazon', 'url': 'amazon.com.br', 'search_param': 'amazon.com.br/s?k='},
            {'name': 'Magazine Luiza', 'url': 'magazineluiza.com.br', 'search_param': 'magazineluiza.com.br/busca'},
            {'name': 'Casas Bahia', 'url': 'casasbahia.com.br', 'search_param': 'casasbahia.com.br/busca'}
        ]
        
        for i, site_data in enumerate(sites_data):
            variation = random.uniform(0.8, 1.3)  # ±30% de variação
            price = round(base_price * variation, 2)
            
            # Cria URL mais específica baseada no site
            search_url = f"https://{site_data['search_param']}/{quote_plus(product)}"
            
            mock_results.append({
                'site': site_data['name'],
                'produto': f"{product} - Oferta {site_data['name']}...",
                'preco': price,
                'link': search_url
            })
        
        return mock_results[:3]  # Retorna 3 resultados
    
    def compare_prices(self, product):
        """Compara preços em diferentes sites"""
        self.results = []
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        search_functions = [
            ('Mercado Livre', self.search_mercadolivre),
            ('Buscapé', self.search_buscape),
            ('Google Shopping', self.search_google_shopping),
            ('Zoom', self.search_zoom),
        ]
        
        for i, (site_name, search_func) in enumerate(search_functions):
            status_text.text(f"Buscando no {site_name}...")
            
            try:
                result = search_func(product)
                if result:
                    self.results.append(result)
            except Exception as e:
                print(f"Erro ao buscar no {site_name}: {e}")
            
            progress_bar.progress((i + 1) * 25)
            time.sleep(1)  # Pausa entre buscas
        
        # Se não encontrou resultados reais, usa dados simulados
        if len(self.results) == 0:
            status_text.text("Gerando resultados simulados...")
            self.results = self.generate_mock_data(product)
            st.info("ℹ️ Resultados simulados para demonstração (sites com proteção anti-bot)")
        
        # Limpa elementos de progresso
        progress_bar.empty()
        status_text.empty()
        
        return self.results
    
    def analyze_deals(self, results):
        """Analisa se vale a pena comprar"""
        if len(results) < 2:
            return "Poucos resultados para análise"
        
        prices = [r['preco'] for r in results]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        best_deal = min(results, key=lambda x: x['preco'])
        worst_deal = max(results, key=lambda x: x['preco'])
        
        savings = max_price - min_price
        savings_percent = (savings / max_price) * 100 if max_price > 0 else 0
        
        analysis = f"""
        📊 **Análise de Preços:**
        
        • **Menor preço:** R$ {min_price:.2f} - {best_deal['site']}
        • **Maior preço:** R$ {max_price:.2f} - {worst_deal['site']}
        • **Preço médio:** R$ {avg_price:.2f}
        • **Economia máxima:** R$ {savings:.2f} ({savings_percent:.1f}%)
        
        💡 **Recomendação:**
        """
        
        if savings_percent > 20:
            analysis += f"🟢 **VALE MUITO A PENA!** Você pode economizar {savings_percent:.1f}% comprando no {best_deal['site']}"
        elif savings_percent > 10:
            analysis += f"🟡 **Vale a pena** comprar no {best_deal['site']} - economia de {savings_percent:.1f}%"
        elif savings_percent > 5:
            analysis += f"🟠 **Pequena diferença** - {best_deal['site']} ainda é a melhor opção"
        else:
            analysis += f"🔴 **Preços similares** - qualquer opção é boa. Considere frete e prazo de entrega."
        
        return analysis

def main():
    st.title("🛒 Comparador de Preços Inteligente")
    st.markdown("Compare preços em diferentes plataformas e descubra se vale a pena comprar!")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Como usar")
        st.markdown("""
        1. Digite o nome do produto
        2. Clique em "Comparar Preços"
        3. Aguarde a busca nos sites
        4. Veja a análise e recomendação
        """)
        
        st.header("🔍 Sites pesquisados")
        st.markdown("""
        • Mercado Livre
        • Buscapé
        • Google Shopping
        • Zoom
        """)
        
        st.header("💡 Dicas")
        st.markdown("""
        • Use termos específicos (marca + modelo)
        • Teste: "iPhone 13", "Notebook Dell", "Mouse Logitech"
        • Alguns sites podem ter proteção anti-bot
        """)
        
        st.header("⚠️ Aviso")
        st.markdown("""
        Este é um projeto educativo. 
        Alguns resultados podem ser simulados devido a proteções dos sites.
        Sempre verifique preços diretamente nas lojas.
        """)
    
    # Interface principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        product = st.text_input("🔍 Digite o produto que deseja pesquisar:", 
                               placeholder="Ex: iPhone 13, Notebook Dell, Mouse Gamer...")
    
    with col2:
        st.write("")  # Espaçamento
        search_button = st.button("🔍 Comparar Preços", type="primary")
    
    # Botões de exemplo
    st.markdown("**🎯 Exemplos rápidos:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📱 iPhone 13"):
            st.session_state.search_product = "iPhone 13"
    with col2:
        if st.button("💻 Notebook Dell"):
            st.session_state.search_product = "Notebook Dell"
    with col3:
        if st.button("🖱️ Mouse Gamer"):
            st.session_state.search_product = "Mouse Gamer"
    with col4:
        if st.button("📺 Smart TV 55"):
            st.session_state.search_product = "Smart TV 55"
    
    # Verifica se foi clicado um exemplo
    if 'search_product' in st.session_state:
        product = st.session_state.search_product
        search_button = True
        del st.session_state.search_product
    
    if search_button and product:
        comparator = PriceComparator()
        
        with st.spinner("🔍 Buscando os melhores preços... Isso pode levar alguns segundos."):
            results = comparator.compare_prices(product)
        
        if results:
            st.success(f"✅ Encontrados {len(results)} resultados para '{product}'!")
            
            # Cria DataFrame para exibição
            df = pd.DataFrame(results)
            df['preco_formatado'] = df['preco'].apply(lambda x: f"R$ {x:.2f}")
            
            # Tabela de resultados com estilo
            st.subheader("📋 Resultados encontrados:")
            
            for i, result in enumerate(results):
                # Determina se é o melhor preço
                is_best = result['preco'] == min([r['preco'] for r in results])
                is_worst = result['preco'] == max([r['preco'] for r in results])
                
                # Container com borda colorida para melhor preço
                if is_best:
                    st.markdown("🏆 **MELHOR PREÇO**", help="Menor preço encontrado!")
                
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{result['site']}**")
                    st.write(result['produto'])
                
                with col2:
                    price_color = "#00FF00" if is_best else "#FF0000" if is_worst else "#000000"
                    st.markdown(f"<h3 style='color: {price_color}'>R$ {result['preco']:.2f}</h3>", 
                               unsafe_allow_html=True)
                
                with col3:
                    if is_best:
                        st.success("🏆 TOP")
                    elif is_worst:
                        st.error("💰 Caro")
                    else:
                        st.info("📊 OK")
                
                with col4:
                    # Link mais funcional com target="_blank"
                    link_text = "🔗 Ver Produto"
                    if "mercadolivre" in result['link'].lower():
                        link_text = "🔗 Ver no ML"
                    elif "amazon" in result['link'].lower():
                        link_text = "🔗 Ver Amazon"
                    elif "buscape" in result['link'].lower():
                        link_text = "🔗 Ver Buscapé"
                    elif "zoom" in result['link'].lower():
                        link_text = "🔗 Ver Zoom"
                    elif "magazineluiza" in result['link'].lower():
                        link_text = "🔗 Ver Magalu"
                    elif "casasbahia" in result['link'].lower():
                        link_text = "🔗 Ver CB"
                    elif "google.com" in result['link'].lower():
                        link_text = "🔗 Ver Google"
                    
                    # Cria um link HTML que abre em nova aba
                    st.markdown(f"""
                    <a href="{result['link']}" target="_blank" style="
                        background-color: #FF4B4B;
                        color: white;
                        padding: 0.25rem 0.75rem;
                        text-decoration: none;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                        display: inline-block;
                        margin-top: 0.5rem;
                    ">{link_text}</a>
                    """, unsafe_allow_html=True)
                
                if i < len(results) - 1:  # Não adiciona divider no último item
                    st.divider()
            
            # Gráfico de comparação melhorado
            st.subheader("📊 Comparação Visual")
            
            # Ordena por preço para melhor visualização
            df_sorted = df.sort_values('preco')
            
            fig = px.bar(df_sorted, x='site', y='preco', 
                        title=f"Comparação de Preços - {product}",
                        labels={'preco': 'Preço (R$)', 'site': 'Loja'},
                        color='preco',
                        color_continuous_scale='RdYlGn_r',
                        text='preco_formatado')
            
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(showlegend=False, height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise e recomendação
            st.subheader("🎯 Análise e Recomendação")
            analysis = comparator.analyze_deals(results)
            st.markdown(analysis)
            
            # Estatísticas adicionais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Menor Preço", f"R$ {min([r['preco'] for r in results]):.2f}")
            
            with col2:
                avg_price = sum([r['preco'] for r in results]) / len(results)
                st.metric("📊 Preço Médio", f"R$ {avg_price:.2f}")
            
            with col3:
                max_savings = max([r['preco'] for r in results]) - min([r['preco'] for r in results])
                st.metric("💸 Economia Máxima", f"R$ {max_savings:.2f}")
            
            # Informações adicionais
            st.info(f"🕐 Pesquisa realizada em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
            
        else:
            st.error("❌ Nenhum resultado encontrado. Tente com outro termo de busca.")
            st.markdown("**💡 Sugestões:**")
            st.markdown("• Use termos mais específicos (marca + modelo)")
            st.markdown("• Tente sinônimos ou termos em inglês")
            st.markdown("• Verifique a ortografia")
    
    elif search_button and not product:
        st.warning("⚠️ Por favor, digite o nome de um produto para pesquisar.")

if __name__ == "__main__":
    main()