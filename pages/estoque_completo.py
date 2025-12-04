import streamlit as st
from utils.database import get_all_produtos, ASSETS_DIR # Importado ASSETS_DIR para fotos
from datetime import datetime
import os

# --- Funções Auxiliares ---

def format_to_brl(value):
    """Formata um float para string no formato R$ 1.234.567,89."""
    try:
        # 1. Converte para float (se já não for)
        num = float(value)
        # 2. Formata com underscore (_) como separador de milhar e ponto (.) como decimal
        formatted = f"{num:_.2f}" 
        # 3. Substitui o ponto (decimal) por vírgula (,)
        formatted = formatted.replace('.', ',') 
        # 4. Substitui o underscore (milhar) por ponto (.) e adiciona o prefixo R$
        return "R$ " + formatted.replace('_', '.') 
    except (ValueError, TypeError):
        return "R$ N/A"

def load_css(file_name="style.css"):
    if not os.path.exists(file_name):
        # Apenas um aviso, pois o arquivo pode estar em outro lugar
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")

# --- Configuração e Carga Inicial ---

load_css("style.css") # Aplica o CSS
st.set_page_config(page_title="Estoque - Cores e Fragrâncias")

st.title("📦 Estoque Completo")

# 🔄 CHAMADA CRÍTICA: Obter dados mais recentes
produtos = get_all_produtos()

if not produtos:
    st.info("Nenhum produto cadastrado no estoque.")
else:
    # Coleta de categorias únicas para os filtros
    marcas = sorted(list({p.get("marca") for p in produtos if p.get("marca")}))
    estilos = sorted(list({p.get("estilo") for p in produtos if p.get("estilo")}))
    tipos = sorted(list({p.get("tipo") for p in produtos if p.get("tipo")}))

    # Filtros em colunas
    col1, col2, col3 = st.columns(3)
    with col1:
        marca_filtro = st.selectbox("Filtrar por Marca", ["Todas"] + marcas)
    with col2:
        estilo_filtro = st.selectbox("Filtrar por Estilo", ["Todos"] + estilos)
    with col3:
        tipo_filtro = st.selectbox("Filtrar por Tipo", ["Todos"] + tipos)

    # Aplicação dos filtros
    produtos_filtrados = produtos
    if marca_filtro != "Todas":
        produtos_filtrados = [p for p in produtos_filtrados if p.get("marca") == marca_filtro]
    if estilo_filtro != "Todos": 
        produtos_filtrados = [p for p in produtos_filtrados if p.get("estilo") == estilo_filtro]
    if tipo_filtro != "Todos":
        produtos_filtrados = [p for p in produtos_filtrados if p.get("tipo") == tipo_filtro]

    st.markdown("---")
    st.subheader(f"{len(produtos_filtrados)} produtos encontrados")
    
    # Inicializa o cálculo total
    total_estoque = 0.0

    # Exibição dos produtos filtrados
    for p in produtos_filtrados:
        
        # TRATAMENTO DE ERRO: Preço e Quantidade (para cálculo e exibição)
        try:
            preco_float = float(p.get('preco'))
            quantidade_int = int(p.get('quantidade', 0))
            
            # Cálculo e adição ao total
            valor_produto = preco_float * quantidade_int
            total_estoque += valor_produto
            
            # Formatação para exibição
            preco_formatado = format_to_brl(preco_float)
            valor_produto_formatado = format_to_brl(valor_produto)
            
        except (ValueError, TypeError):
            preco_formatado = "R$ N/A"
            quantidade_int = "N/A"
            valor_produto_formatado = "R$ N/A"

        st.markdown(f"### **{p.get('nome')}**")
        
        st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
        st.write(f"**Preço Unitário:** {preco_formatado} • **Quantidade em Estoque:** {quantidade_int}")
        st.write(f"**Valor Total deste Item:** **{valor_produto_formatado}**")
        st.write(f"**Validade:** {p.get('data_validade') or 'N/A'}")
        
        # TRATAMENTO DE ERRO: Carregamento da foto
        if p.get("foto"):
            photo_path = os.path.join(ASSETS_DIR, p.get('foto')) # Usando ASSETS_DIR
            if os.path.exists(photo_path):
                try:
                    st.image(photo_path, width=180)
                except Exception:
                    st.info("Erro ao carregar imagem.")
            else:
                st.info("Sem foto ou caminho inválido.")
                
        st.markdown("---")

    # Exibição do Valor Total em Estoque (filtrado) - AGORA COM FORMATO BRL CORRETO
    st.success(f"💰 Valor Total em Estoque (filtrado): **{format_to_brl(total_estoque)}**")
