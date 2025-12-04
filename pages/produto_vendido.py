import streamlit as st
from utils.database import get_all_produtos, ASSETS_DIR # Mantendo a importação do ASSETS_DIR
import os
from datetime import datetime

# --- Funções Auxiliares de Formatação ---
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

def load_css(file_name):
    """Carrega e aplica o CSS personalizado, forçando a codificação UTF-8."""
    if not os.path.exists(file_name):
        # Apenas um aviso, pois o arquivo pode estar em outro lugar
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")
        
load_css("style.css")

st.set_page_config(page_title="Produtos Vendidos - Cores e Fragrâncias")

st.title("💰 Produtos Vendidos")
st.markdown("---")
st.info("Abaixo estão os produtos que foram marcados como vendidos e não possuem mais estoque (quantidade = 0).")

# 🔄 CHAMADA CRÍTICA: Obter dados mais recentes
todos_produtos = get_all_produtos(include_sold=True) # Inclui todos os dados para análise

# Filtra produtos que foram vendidos (vendido = 1) E que estão fora de estoque (quantidade = 0)
# NOTA: Este filtro pode não refletir o histórico total de vendas, apenas itens ZERADOS.
produtos_fora_estoque = [p for p in todos_produtos if p.get("vendido") == 1 and p.get("quantidade") == 0]

if not produtos_fora_estoque:
    st.info("Nenhum produto vendido e que saiu totalmente do estoque ainda.")
else:
    # Inicializa o total de preço dos itens zerados
    total_vendido = 0.0
    
    for p in produtos_fora_estoque:
        # TRATAMENTO DE ERRO para preço
        try:
            preco_float = float(p.get('preco'))
            preco_formatado = format_to_brl(preco_float)
            total_vendido += preco_float # Soma o preço para o cálculo total
            
            # Converte a data da última venda para formato BR
            data_venda = p.get('data_ultima_venda')
            if data_venda:
                data_venda_formatada = datetime.fromisoformat(data_venda).strftime('%d/%m/%Y às %H:%M:%S')
            else:
                data_venda_formatada = 'N/A'
                
        except (ValueError, TypeError):
            preco_formatado = "R$ N/A"
            data_venda_formatada = 'N/A'
            
        st.markdown(f"### **{p.get('nome')}**")
        st.write(f"**Preço de Venda (Último):** {preco_formatado}")
        st.write(f"**Data da Última Venda:** {data_venda_formatada}")
        st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
        
        # TRATAMENTO DE ERRO: Carregamento da foto
        if p.get("foto"):
            photo_path = os.path.join(ASSETS_DIR, p.get('foto'))
            if os.path.exists(photo_path):
                try:
                    st.image(photo_path, width=150)
                except Exception:
                    st.info("Erro ao carregar imagem.")
            else:
                st.info("Sem foto ou caminho inválido.")
                
        st.markdown("---")

    # Exibição do Valor Total Vendido (fora de estoque)
    st.success(f"📊 Valor Total Vendido (fora de estoque): **{format_to_brl(total_vendido)}**")
