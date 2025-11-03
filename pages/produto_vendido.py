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

st.set_page_config(page_title="Produtos Vendidos - Cores e Fragrâncias")

st.title("💰 Produtos Vendidos")

# 🔄 CHAMADA CRÍTICA: Obter dados mais recentes
todos_produtos = get_all_produtos()

# Filtra produtos que foram vendidos (vendido = 1) E que estão fora de estoque (quantidade = 0)
produtos_fora_estoque = [p for p in todos_produtos if p.get("vendido") == 1 and p.get("quantidade") == 0]

if not produtos_fora_estoque:
    st.info("Nenhum produto vendido e que saiu totalmente do estoque ainda.")
else:
    for p in produtos_fora_estoque:
        # TRATAMENTO DE ERRO para preço
        try:
            preco_formatado = f"R$ {float(p.get('preco')):.2f}"
        except (ValueError, TypeError):
            preco_formatado = "R$ N/A"
            
        st.markdown(f"### **{p.get('nome')}**")
        st.write(f"**Preço de Venda (Último):** {preco_formatado}")
        st.write(f"**Data da Última Venda:** {p.get('data_ultima_venda') or 'N/A'}")
        st.write(f"**Marca:** {p.get('marca')}")
        st.write(f"**Estilo:** {p.get('estilo')}")
        st.write(f"**Tipo:** {p.get('tipo')}")
        st.markdown("---")

# Cálculo do valor total (robusto contra dados nulos)
total_vendido = sum(float(p.get("preco", 0)) for p in produtos_fora_estoque)

st.success(f"📊 Valor Total Vendido (fora de estoque): R$ {total_vendido:,.2f}")