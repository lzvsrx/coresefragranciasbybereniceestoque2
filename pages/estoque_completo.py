import streamlit as st
from utils.database import get_all_produtos
import os

# --- Funções Auxiliares ---
def load_css(file_name):
    if not os.path.exists(file_name):
        st.warning(f"O arquivo CSS '{file_name}' não foi encontrado.")
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")

load_css("style.css")

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

    # Exibição dos produtos filtrados
    for p in produtos_filtrados:
        st.markdown(f"### **{p.get('nome')}**")
        
        # TRATAMENTO DE ERRO: Preço e Quantidade
        try:
            preco_formatado = f"R$ {float(p.get('preco')):.2f}"
            quantidade_int = int(p.get('quantidade', 0))
        except (ValueError, TypeError):
            preco_formatado = "R$ N/A"
            quantidade_int = "N/A"

        st.write(f"**Preço:** {preco_formatado}")
        st.write(f"**Quantidade:** {quantidade_int}")
        st.write(f"**Marca:** {p.get('marca')}")
        st.write(f"**Estilo:** {p.get('estilo')}")
        st.write(f"**Tipo:** {p.get('tipo')}")
        st.write(f"**Validade:** {p.get('data_validade') or 'N/A'}")
        
        # TRATAMENTO DE ERRO: Carregamento da foto
        if p.get("foto"):
            photo_path = os.path.join("assets", p.get('foto'))
            if os.path.exists(photo_path):
                try:
                    st.image(photo_path, width=180)
                except Exception:
                    st.info("Erro ao carregar imagem.")
            else:
                st.info("Sem foto ou caminho inválido.")
                
        st.markdown("---")

    # Cálculo do valor total em estoque (filtrado) - Robusto
    total_estoque = sum(
        (float(p.get("preco", 0)) if p.get("preco") else 0) * (int(p.get("quantidade", 0)) if p.get("quantidade") else 0)
        for p in produtos_filtrados
    )
    

    st.success(f"💰 Valor Total em Estoque (filtrado): R$ {total_estoque:.,2f}")
