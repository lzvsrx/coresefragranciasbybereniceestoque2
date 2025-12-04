import streamlit as st
from datetime import datetime
from datetime import date # Necessário para date_input
import os
import shutil
import base64 # Necessário para a função de download
import json # Necessário para debug ou manipulação de lotes no frontend

# ====================================================================
# CONFIGURAÇÃO DE IMPORTS E FUNÇÕES DE UTILS
# ====================================================================

# Ajuste para importar do arquivo database.py no mesmo diretório
try:
    from database import (
        get_user, hash_password, add_user, get_all_users, 
        add_produto, get_all_produtos, get_produto_by_id, 
        update_produto, delete_produto, mark_produto_as_sold, 
        MARCAS, ESTILOS, TIPOS, 
        generate_stock_pdf, ASSETS_DIR, 
        create_tables, get_binary_file_downloader_html, initialize_admin_user
    )
except ImportError as e:
    st.error(f"🚨 Erro: Não foi possível importar as funções do 'database.py'. Certifique-se de que o arquivo existe no mesmo diretório. Detalhes: {e}")
    st.stop()
    
# Inicializa o banco de dados e as tabelas, incluindo o usuário admin
create_tables()
initialize_admin_user() # Cria o usuário admin se não existir

# ====================================================================
# FUNÇÕES DE UTILIDADE DA UI
# ====================================================================

def load_css(file_name):
    """Carrega e aplica o CSS personalizado, forçando a codificação UTF-8."""
    # Note: O arquivo style.css precisaria ser criado separadamente,
    # caso contrário, a warning aparecerá.
    if not os.path.exists(file_name):
        st.warning(f"O arquivo CSS '{file_name}' não foi encontrado.")
        return
    with open(file_name, encoding='utf-8') as f: 
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ====================================================================
# CONFIGURAÇÃO DE PÁGINA E ESTADO DE SESSÃO
# ====================================================================

st.set_page_config(
    page_title="Cores e Fragrâncias by Berenice",
    layout="wide",
    initial_sidebar_state="expanded",
)
# load_css("style.css") # Comentei para evitar erro se você não tiver o arquivo

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
# Roteamento de páginas
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'login'
# ID do produto em edição
if 'edit_id' not in st.session_state:
    st.session_state['edit_id'] = None
# Estado temporário para gerenciar lotes no formulário
if 'lotes_data' not in st.session_state:
    st.session_state['lotes_data'] = []


# ====================================================================
# TELAS DA APLICAÇÃO
# ====================================================================

def show_login():
    """Exibe a tela de Login."""
    st.title("🔐 Login - Cores e Fragrâncias")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1.form("login_form"):
        st.subheader("Acesso ao Sistema")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            user = get_user(username)
            if user and user['password'] == hash_password(password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = user['role']
                st.session_state['current_page'] = 'list_products'
                st.success(f"Bem-vindo(a), {username}!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    
    with col2:
        st.subheader("Informações")
        st.info("Para acesso de administrador use: **Usuário: admin | Senha: 123**")
        st.markdown("""
        Este sistema permite gerenciar o estoque, vendas e validades dos produtos.
        Acesso de administrador é necessário para adicionar/editar produtos.
        """)

def show_product_form(product=None):
    """Exibe o formulário de Adição/Edição de Produto."""
    is_editing = product is not None
    st.header(f"✏️ {('Editar' if is_editing else 'Adicionar')} Produto")
    
    # 1. Inicializa o estado de lotes para o formulário
    if not is_editing:
        if st.session_state['edit_id'] is not None:
             # Se está em modo de adição, mas edit_id está setado de uma edição anterior, zera.
             st.session_state['edit_id'] = None
        # Novo produto, garante que lotes_data está vazio
        if 'lotes_data' in st.session_state:
             st.session_state['lotes_data'] = []
    
    if is_editing and product.get('lotes') and st.session_state.get('edit_id') != product['id']:
        # Copia os lotes para edição APENAS na primeira vez que abre o formulário de edição
        st.session_state['lotes_data'] = product['lotes']
        st.session_state['edit_id'] = product['id'] # Marca o ID para saber qual está editando
    
    if 'lotes_data' not in st.session_state:
          st.session_state['lotes_data'] = []

    
    with st.form("product_form", clear_on_submit=False):
        st.subheader("Dados Principais")
        col1, col2 = st.columns(2)
        
        # 1. Campos principais
        with col1:
            nome = st.text_input("Nome do Produto", value=product.get('nome', ""))
            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", value=float(product.get('preco', 0.01)))
            
            # Ajuste de index para Selectbox
            try:
                marca_index = MARCAS.index(product['marca']) if is_editing and product['marca'] in MARCAS else 0
            except ValueError:
                marca_index = 0
            marca = st.selectbox("Marca", MARCAS, index=marca_index)
        
        with col2:
            try:
                estilo_index = ESTILOS.index(product['estilo']) if is_editing and product['estilo'] in ESTILOS else 0
            except ValueError:
                estilo_index = 0
            estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index)
            
            try:
                tipo_index = TIPOS.index(product['tipo']) if is_editing and product['tipo'] in TIPOS else 0
            except ValueError:
                tipo_index = 0
            tipo = st.selectbox("Tipo", TIPOS, index=tipo_index)
            
            uploaded_file = st.file_uploader("Upload de Foto (Opcional)", type=["jpg", "png", "jpeg"])
            
            current_photo = product.get('foto') if is_editing else None
            if current_photo:
                 photo_path_display = os.path.join(ASSETS_DIR, current_photo)
                 if os.path.exists(photo_path_display):
                    st.image(photo_path_display, caption="Foto Atual", width=100)
                 else:
                    st.info("Foto salva não encontrada no diretório 'assets'.")
        
        st.markdown("---")
        st.subheader("📦 Gestão de Lotes por Validade")
        
        # 2. Exibe e gerencia lotes existentes
        st.markdown("##### Lotes Atuais (Clique em Remover para Excluir)")
        
        lotes_para_manter = []
        
        # Cria uma cópia para iterar enquanto o estado é modificado
        if st.session_state.get('lotes_data'):
            
            # Garante que os lotes sejam editáveis, mas que a exclusão funcione no rerun
            for i, lote in enumerate(st.session_state['lotes_data']):
                col_i1, col_i2, col_i3 = st.columns([0.4, 0.4, 0.2])
                
                # Formata a validade para o widget
                try:
                    lote_validade_dt = datetime.fromisoformat(lote['validade']).date()
                except (ValueError, TypeError):
                    lote_validade_dt = date.today()

                
                nova_validade = col_i1.date_input(f"Validade Lote {i+1}", value=lote_validade_dt, key=f"validade_{i}_{st.session_state['edit_id']}")
                nova_quantidade = col_i2.number_input(f"Quantidade Lote {i+1}", min_value=0, value=lote['quantidade'], key=f"quantidade_{i}_{st.session_state['edit_id']}")
                
                if col_i3.button("Remover Lote", key=f"remover_{i}_{st.session_state['edit_id']}"):
                    # Remove o lote e recarrega a página
                    st.session_state['lotes_data'].pop(i)
                    st.rerun()
                
                # Se não foi removido, adiciona à lista final (com possíveis edições de valor)
                lotes_para_manter.append({
                    'validade': nova_validade.isoformat() if nova_validade else None,
                    'quantidade': nova_quantidade
                })
            
            # Atualiza o estado da sessão com os lotes mantidos/modificados
            st.session_state['lotes_data'] = lotes_para_manter


        # 3. Adicionar novo lote
        st.markdown("##### Adicionar Novo Lote")
        col_new1, col_new2 = st.columns(2)
        new_validade = col_new1.date_input("Validade do Novo Lote", value=date.today(), key="new_validade_lote")
        new_quantidade = col_new2.number_input("Quantidade do Novo Lote", min_value=0, value=0, key="new_quantidade_lote")

        
        if st.form_submit_button(f"✅ {'Atualizar' if is_editing else 'Salvar'} Produto"):
            
            final_lotes = st.session_state['lotes_data'].copy()
            
            # Adiciona o lote novo se tiver quantidade > 0
            if new_quantidade > 0:
                final_lotes.append({
                    'validade': new_validade.isoformat(),
                    'quantidade': new_quantidade
                })

            # Recalcula a quantidade total de todos os lotes
            total_quantidade = sum(lote['quantidade'] for lote in final_lotes)

            if not nome or preco <= 0 or total_quantidade < 0:
                st.error("🚨 Atenção: Preencha o Nome, o Preço e verifique se a Quantidade Total é positiva ou zero (para esgotados).")
            else:
                # 4. Gerencia a foto
                photo_name = current_photo
                if uploaded_file:
                    # Cria a pasta ASSETS_DIR se não existir
                    if not os.path.exists(ASSETS_DIR):
                        os.makedirs(ASSETS_DIR)

                    # Remove a foto antiga se estiver editando e houver upload de uma nova
                    if is_editing and current_photo and os.path.exists(os.path.join(ASSETS_DIR, current_photo)):
                        os.remove(os.path.join(ASSETS_DIR, current_photo))
                        
                    extension = uploaded_file.name.split('.')[-1]
                    # Cria um nome de arquivo único
                    photo_name = f"{nome.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
                    file_path = os.path.join(ASSETS_DIR, photo_name)
                    
                    # Salva o arquivo
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                # 5. Chama a função de DB
                if is_editing:
                    update_produto(
                        product['id'], nome, preco, total_quantidade, marca, estilo, tipo, photo_name, final_lotes
                    )
                    st.success(f"🎉 Produto '{nome}' atualizado com sucesso!")
                else:
                    add_produto(
                        nome, preco, total_quantidade, marca, estilo, tipo, photo_name, final_lotes
                    )
                    st.success(f"🎉 Produto '{nome}' adicionado com sucesso!")
                
                # 6. Limpa e redireciona
                st.session_state['current_page'] = 'list_products'
                st.session_state['edit_id'] = None
                if 'lotes_data' in st.session_state:
                    del st.session_state['lotes_data']
                st.rerun()


def show_list_products():
    """Exibe a lista de produtos com ações de CRUD e Venda."""
    st.header("📦 Estoque Atual e Vendas")

    # ----------------------------------------------------
    # FILTROS E PESQUISA
    # ----------------------------------------------------
    col_search, col_filter_brand, col_filter_style, col_filter_type = st.columns([3, 1, 1, 1])

    search_term = col_search.text_input("Buscar por Nome/Descrição", "")
    filter_brand = col_filter_brand.selectbox("Filtrar por Marca", ["Todos"] + MARCAS)
    filter_style = col_filter_style.selectbox("Filtrar por Estilo", ["Todos"] + ESTILOS)
    filter_type = col_filter_type.selectbox("Filtrar por Tipo", ["Todos"] + TIPOS)
    
    st.markdown("---")

    # ----------------------------------------------------
    # BOTÃO DE EXPORTAR PDF
    # ----------------------------------------------------
    if st.session_state['role'] == 'admin':
        st.subheader("Relatórios")
        
        if st.button('Gerar e Baixar Relatório PDF (Lotes) 📥'):
            PDF_FILE_PATH = os.path.join(os.getcwd(), "Relatorio_Estoque.pdf")
            try:
                generate_stock_pdf(PDF_FILE_PATH)
                download_link_html = get_binary_file_downloader_html(PDF_FILE_PATH, 'Baixar Relatório PDF')
                st.markdown(download_link_html, unsafe_allow_html=True)
                st.success("Relatório de Lotes gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar o PDF: Certifique-se de que a biblioteca ReportLab está instalada (`pip install reportlab`). Detalhes: {e}")
        
        st.markdown("---")


    produtos = get_all_produtos()
    
    if not produtos:
        st.info("Nenhum produto cadastrado no estoque.")
        return

    # Aplicar filtros
    filtered_produtos = [p for p in produtos if 
                         search_term.lower() in p['nome'].lower() and
                         (filter_brand == "Todos" or p['marca'] == filter_brand) and
                         (filter_style == "Todos" or p['estilo'] == filter_style) and
                         (filter_type == "Todos" or p['tipo'] == filter_type)
                        ]
    
    if not filtered_produtos:
        st.warning("Nenhum produto encontrado com os filtros aplicados.")
        return

    # ----------------------------------------------------
    # LISTAGEM DE PRODUTOS
    # ----------------------------------------------------
    for p in filtered_produtos:
        # Título do expander: Nome | Qtd Total | Preço
        expander_title = f"**{p['nome']}** | Qtd Total: **{p['quantidade']}** | R$ {p['preco']:.2f}"
        
        # Formatação para produtos zerados
        if p['quantidade'] == 0:
            expander_title = f"🗑️ {expander_title} (ESGOTADO)"

        with st.expander(expander_title):
            col_list_1, col_list_2, col_list_3 = st.columns([1, 2, 3])
            
            # Coluna da Foto
            photo_path = os.path.join(ASSETS_DIR, p.get('foto')) if p.get('foto') else None
            if photo_path and os.path.exists(photo_path):
                 col_list_1.image(photo_path, caption=p['marca'], width=80)
            else:
                 col_list_1.info("Sem Foto")

            # Coluna de Detalhes
            col_list_2.markdown(f"""
            - **Marca:** {p['marca']}
            - **Estilo:** {p['estilo']}
            - **Tipo:** {p['tipo']}
            - **Adicionado:** {datetime.fromisoformat(p['data_adicao']).strftime('%d/%m/%Y')}
            - **Vendidos:** {p['vendido']}
            """)

            # Coluna de Lotes e Venda
            with col_list_3:
                st.markdown("##### 🛒 Venda por Lote")
                
                # Cria a lista de opções de venda
                lote_options = {}
                # Garantindo que 'lotes' é uma lista
                lotes_data = p.get('lotes', [])
                if isinstance(lotes_data, str):
                    try:
                        lotes_data = json.loads(lotes_data)
                    except json.JSONDecodeError:
                        lotes_data = []

                for lote in lotes_data:
                    if lote['quantidade'] > 0:
                        validade_str = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%Y')
                        # Chave (para a função de venda): 'YYYY-MM-DD', Valor no Select: 'Qtd: X (Vence em DD/MM/AAAA)'
                        lote_options[lote['validade']] = f"Qtd: {lote['quantidade']} (Vence em {validade_str})"

                if lote_options:
                    # Selectbox com as opções de lote disponíveis
                    selected_lote_id = st.selectbox(
                        "Selecione o Lote (Validade):",
                        options=list(lote_options.keys()),
                        format_func=lambda x: lote_options[x],
                        key=f"lote_select_{p['id']}"
                    )
                    
                    # Quantidade a vender
                    max_qty = next((l['quantidade'] for l in lotes_data if l['validade'] == selected_lote_id), 1)
                    qty_sold = st.number_input(
                        "Quantidade a Vender:", 
                        min_value=1, 
                        max_value=max_qty, 
                        value=1, 
                        key=f"qty_sold_{p['id']}"
                    )
                    
                    if st.button(f"Vender {qty_sold}x 💰", key=f"sell_{p['id']}"):
                        try:
                            mark_produto_as_sold(p['id'], qty_sold, selected_lote_id)
                            st.success(f"Venda de {qty_sold} unidades de **{p['nome']}** (lote {selected_lote_id}) registrada!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(f"Erro na Venda: {str(ve)}")
                else:
                    st.warning("Produto sem estoque para venda no momento.")
                
            st.markdown("---")
            
            # Ações de Administrador (Editar/Excluir)
            if st.session_state['role'] == 'admin':
                col_actions_1, col_actions_2, _ = st.columns([1, 1, 4])
                
                if col_actions_1.button("Editar 📝", key=f"edit_{p['id']}"):
                    st.session_state['edit_id'] = p['id']
                    st.session_state['current_page'] = 'add_edit_product'
                    st.rerun()
                    
                if col_actions_2.button("Excluir 🗑️", key=f"delete_{p['id']}"):
                    delete_produto(p['id'])
                    st.warning(f"Produto '{p['nome']}' excluído.")
                    st.rerun()


# ====================================================================
# LAYOUT E ROTEAMENTO PRINCIPAL
# ====================================================================

def main_app():
    
    st.title("🌸 Cores e Fragrâncias by Berenice 🌸")
    
    # ------------------
    # Sidebar
    # ------------------
    st.sidebar.title("Gerenciamento de Estoque")
    
    # Botão de Login/Logout
    if not st.session_state['logged_in']:
        if st.sidebar.button("🔐 Acessar Área Restrita"):
            st.session_state['current_page'] = 'login'
    else:
        st.sidebar.header(f"Olá, {st.session_state['username']} ({st.session_state['role'].capitalize()})")
        
        # Navegação
        if st.sidebar.button("📦 Estoque e Vendas"):
            st.session_state['current_page'] = 'list_products'
            st.session_state['edit_id'] = None
            st.session_state['lotes_data'] = [] # Limpa o estado de lotes ao sair do form
        
        if st.session_state['role'] == 'admin':
            if st.sidebar.button("➕ Adicionar Produto"):
                st.session_state['current_page'] = 'add_edit_product'
                st.session_state['edit_id'] = None
                st.session_state['lotes_data'] = [] # Limpa o estado de lotes para o novo form
        
        st.sidebar.markdown("---")
        
        if st.sidebar.button("Sair 🚪"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['role'] = None
            st.session_state['current_page'] = 'login'
            st.rerun()
            
    # Mostra logo
    try:
        if os.path.exists("assets/logo.png"):
             st.sidebar.image("assets/logo.png", width=150)
        else:
             st.sidebar.info("Coloque a sua logo em assets/logo.png para exibir.")
    except Exception:
        pass

    
    # ------------------
    # Roteamento de Páginas
    # ------------------
    if st.session_state['current_page'] == 'login':
        show_login()
    elif st.session_state['current_page'] == 'list_products' and st.session_state['logged_in']:
        show_list_products()
    elif st.session_state['current_page'] == 'add_edit_product' and st.session_state['role'] == 'admin':
        if st.session_state['edit_id']:
            product_to_edit = get_produto_by_id(st.session_state['edit_id'])
            if product_to_edit:
                show_product_form(product_to_edit)
            else:
                st.error("Produto não encontrado.")
                st.session_state['current_page'] = 'list_products'
                st.rerun()
        else:
            show_product_form()
    else:
        # Redireciona para login se tentar acessar algo sem permissão
        if not st.session_state['logged_in']:
              show_login()
        elif st.session_state['logged_in']:
             # Se logado mas sem página definida, mostra o estoque
             st.session_state['current_page'] = 'list_products'
             st.rerun()
        else:
             st.info("Página inicial. Use o menu lateral para navegar.")
             
# Inicia a aplicação
if __name__ == '__main__':
    # Cria o diretório de assets se não existir
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    
    main_app()
