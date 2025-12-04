import streamlit as st
import os
from utils.database import create_tables, check_user_login # Importa a função do DB

# Configurações Iniciais
st.set_page_config(
    page_title="Cores e Fragrâncias by Berenice",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa as tabelas do DB (garante que existem)
create_tables()

# Inicialização do estado de sessão para Login
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "role" not in st.session_state: st.session_state["role"] = "guest"

# Função para carregar CSS (assumindo que style.css existe)
def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
load_css()

# --- Conteúdo da Página Inicial ---
st.title("🌸 Cores e Fragrâncias by Berenice 🌸")
st.markdown("---")

st.markdown("""
Este é o aplicativo para **gerenciamento de estoque** da loja, construído com Streamlit e SQLite.

### 🧭 Navegação
Use o menu lateral (ícone das páginas do Streamlit) para acessar as diferentes áreas:
* **Gerenciar Produtos:** Cadastro, Edição, Remoção, Venda e Relatórios (Requer Login).
* **Estoque Completo:** Visualização geral do estoque.
* **Produtos Vendidos:** Histórico de itens vendidos.
* **Área Administrativa:** Login e Cadastro de novos usuários.
""")

# Mostra logo (verifique assets/logo.png)
try:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=250)
    else:
         st.info("Coloque a sua logo em assets/logo.png para exibir aqui.")
except Exception:
     pass

# Botão de Logout (mostrado no sidebar se estiver logado)
if st.session_state["logged_in"]:
    st.sidebar.success(f"Logado como: **{st.session_state['username']}** ({st.session_state['role']})")
    if st.sidebar.button("Sair"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = "guest"
        st.rerun()
