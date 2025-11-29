import streamlit as st
import os
from utils.database import create_tables
import base64
from utils.database import generate_stock_pdf


# Inicializa o banco de dados e as tabelas
create_tables()
def load_css(file_name):
    """Carrega e aplica o CSS personalizado, forçando a codificação UTF-8."""
    if not os.path.exists(file_name):
        st.warning(f"O arquivo CSS '{file_name}' não foi encontrado.")
        return
    # Adicione encoding='utf-8' para resolver o problema de decodificação.
    with open(file_name, encoding='utf-8') as f: 
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css("style.css")

st.set_page_config(
    page_title="Cores e Fragrâncias by Berenice",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌸 Cores e Fragrâncias by Berenice 🌸")

st.markdown("""
Este é o aplicativo para **gerenciamento de estoque** da loja.

Use o menu lateral (ícone das páginas do Streamlit) para navegar entre:
- 📦 Estoque Completo
- 💰 Produtos Vendidos
- 🔐 Área Administrativa (login / cadastro)
- 🛠️ Gerenciar Produtos (somente após login)
- 🤖 Chatbot de Estoque
""")

# Mostra logo (verifique assets/logo.png)
try:
    st.image("assets/logo.png", width=250)
except Exception:
    st.info("Coloque a sua logo em assets/logo.png para exibir aqui.")

# Botão de Logout (mostrado no sidebar se estiver logado)
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    if st.sidebar.button("Sair"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()
