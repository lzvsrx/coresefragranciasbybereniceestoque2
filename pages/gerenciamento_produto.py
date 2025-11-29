import streamlit as st
import os
from datetime import datetime, date
from utils.database import (
    add_produto, get_all_produtos, update_produto, delete_produto, get_produto_by_id,
    export_produtos_to_csv, import_produtos_from_csv, generate_stock_pdf,
    mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, ASSETS_DIR
)

# --- Configurações Iniciais e CSS ---
def load_css(file_name):
    if not os.path.exists(file_name):
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

load_css("style.css")

st.set_page_config(page_title="Gerenciar Produtos - Cores e Fragrâncias")

# Inicialização de estado
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'edit_mode' not in st.session_state: st.session_state['edit_mode'] = False
if 'edit_product_id' not in st.session_state: st.session_state['edit_product_id'] = None

# -------------------------------------------------------------------
# FUNÇÃO DE CADASTRO DE PRODUTO
# -------------------------------------------------------------------
def add_product_form_com_colunas():
    st.subheader("Adicionar Novo Produto")
    
    # Garante que o diretório de assets exista
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    
    with st.form("add_product_form", clear_on_submit=True):
        nome = st.text_input("Nome do Produto", max_chars=150)
        
        col1, col2 = st.columns([3, 1]) 

        with col1:
            st.markdown("##### Detalhes Principais")
            # Adicionei a opção 'Selecionar' para forçar a escolha
            marca = st.selectbox("📝 Marca do Produto", options=['Selecionar'] + MARCAS, key="add_input_marca")
            tipo = st.selectbox("🏷️ Tipo de Produto", options=['Selecionar'] + TIPOS, key="add_input_tipo")
            estilo = st.selectbox("Estilo", ['Selecionar'] + ESTILOS, key="add_input_estilo")
            
            # VALIDAÇÃO: min_value 0.01 para garantir preço positivo
            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", step=1.0)
            quantidade = st.number_input("Quantidade", min_value=0, step=1, value=1)
            
        with col2:
            st.markdown("##### Foto e Validade")
            foto = st.file_uploader("🖼️ Foto do Produto", type=['png', 'jpg', 'jpeg'], key="add_input_foto")
            data_validade = st.date_input(
                "🗓️ Data de Validade", 
                value=date.today(), 
                key="add_input_validade"
            )

        submitted = st.form_submit_button("Adicionar Produto")

        if submitted:
            # TRATAMENTO DE ERRO: Validação de campos obrigatórios
            if not nome or preco <= 0 or quantidade < 0 or marca == 'Selecionar' or tipo == 'Selecionar':
                st.error("Nome, Preço (positivo), Quantidade (não negativa), Marca e Tipo são obrigatórios.")
                return
            
            photo_name = None
            if foto:
                # TRATAMENTO DE ERRO: Salvando a foto
                try:
                    photo_name = f"{int(datetime.now().timestamp())}_{foto.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(foto.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a foto: {e}. Tente novamente.")
                    return
            
            try:
                # Chamada do DB
                add_produto(
                    nome, preco, quantidade, marca, estilo, tipo, 
                    photo_name, data_validade.isoformat()
                )
                st.success(f"Produto '{nome}' adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar produto no banco de dados: {e}")


# -------------------------------------------------------------------
# FUNÇÕES DE EDIÇÃO E LISTAGEM
# -------------------------------------------------------------------

def show_edit_form():
    """Exibe o formulário de edição para o produto selecionado."""
    produto_id = st.session_state.get('edit_product_id')
    produto = get_produto_by_id(produto_id)
    
    if not produto:
        st.error("Produto não encontrado ou ID inválido.")
        st.session_state["edit_mode"] = False
        st.session_state["edit_product_id"] = None
        return

    st.subheader(f"Editar Produto: {produto.get('nome')}")

    # TRATAMENTO DE ERRO: Conversão de data para o date_input
    default_date = None
    if produto.get("data_validade"):
        try:
            default_date = datetime.fromisoformat(produto.get("data_validade")).date()
        except (ValueError, TypeError):
            default_date = date.today() # Usa a data atual se a data armazenada for inválida
            
    # Garantir valores numéricos para o number_input
    default_preco = float(produto.get("preco", 0.01))
    default_quantidade = int(produto.get("quantidade", 0))

    with st.form("edit_product_form", clear_on_submit=False):
        nome = st.text_input("Nome", value=produto.get("nome"))
        
        col1, col2 = st.columns(2)
        with col1:
            preco = st.number_input("Preço (R$)", value=default_preco, format="%.2f", min_value=0.01)
        with col2:
            quantidade = st.number_input("Quantidade", value=default_quantidade, step=1, min_value=0)
            
        # Determina o índice de seleção atual (TRATAMENTO DE ERRO: Lida com valores inexistentes)
        marca_index = MARCAS.index(produto.get("marca")) if produto.get("marca") in MARCAS else 0
        estilo_index = ESTILOS.index(produto.get("estilo")) if produto.get("estilo") in ESTILOS else 0
        tipo_index = TIPOS.index(produto.get("tipo")) if produto.get("tipo") in TIPOS else 0

        marca = st.selectbox("Marca", MARCAS, index=marca_index)
        estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index)
        tipo = st.selectbox("Tipo", TIPOS, index=tipo_index)
        
        data_validade = st.date_input("Data de Validade", value=default_date or date.today())
        uploaded = st.file_uploader("Alterar Foto", type=["jpg","png","jpeg"])
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("Salvar Alterações")
        with col_btn2:
            cancel = st.form_submit_button("Cancelar Edição")

        if save:
            if not nome or preco <= 0 or quantidade < 0:
                st.error("Nome, Preço (positivo) e Quantidade (não negativa) são obrigatórios.")
                return

            photo_name = produto.get("foto")
            if uploaded:
                # Remove foto antiga se existir
                if photo_name and os.path.exists(os.path.join(ASSETS_DIR, photo_name)):
                    try: 
                        os.remove(os.path.join(ASSETS_DIR, photo_name))
                    except Exception: 
                        st.warning("Não foi possível remover a foto antiga, mas a nova será salva.")
                
                # Salva nova foto (TRATAMENTO DE ERRO: Salvando a foto)
                try:
                    photo_name = f"{int(datetime.now().timestamp())}_{uploaded.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(uploaded.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a nova foto: {e}")
                    return
            
            validade_iso = data_validade.isoformat() if data_validade else None

            try:
                update_produto(produto_id, nome, preco, quantidade, marca, estilo, tipo, photo_name, validade_iso)
                st.success(f"Produto '{nome}' atualizado com sucesso!")
                st.session_state["edit_mode"] = False
                st.session_state["edit_product_id"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar produto no banco de dados: {e}")
                
        if cancel:
            st.session_state["edit_mode"] = False
            st.session_state["edit_product_id"] = None
            st.rerun()

def manage_products_list():
    st.subheader("Lista de Produtos")
    produtos = get_all_produtos()
    
    # --- Ações de Arquivo (Import/Export/PDF) ---
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        # TRATAMENTO DE ERRO: Exportação CSV
        if st.button('Exportar CSV', key='btn_export_csv'):
            csv_path = os.path.join('data','produtos_export.csv')
            if not os.path.exists('data'): os.makedirs('data')
            try:
                export_produtos_to_csv(csv_path)
                st.success('Exportação CSV concluída (Simulação).')
                # A função download_button do Streamlit precisa de dados reais (não simulação)
                # Para uma simulação, é necessário gerar o conteúdo real do CSV no ambiente real
            except Exception as e:
                st.error('Erro ao exportar CSV: ' + str(e))
                
    with col_b:
        # TRATAMENTO DE ERRO: Importação CSV
        uploaded_csv = st.file_uploader('Importar CSV', type=['csv'], key='import_csv')
        if uploaded_csv is not None and st.button('Processar Importação', key='btn_import'):
            # Simulação: Em um DB real, aqui você processaria o uploaded_csv.getbuffer()
            try:
                # O Simulado fará uma adição fictícia, mas em um DB real processaria o arquivo
                import_produtos_from_csv('simulacao_path') 
                st.success('Produtos importados com sucesso (Simulação).')
                st.rerun()
            except Exception as e:
                st.error('Erro ao importar CSV: ' + str(e))
                
    with col_c:
        # TRATAMENTO DE ERRO: Geração de PDF
        if st.button('Gerar Relatório PDF', key='btn_pdf'):
            pdf_path = os.path.join('data','relatorio_estoque.pdf')
            if not os.path.exists('data'): os.makedirs('data')
            try:
                generate_stock_pdf(pdf_path)
                st.success('PDF gerado (Simulação).')
            except Exception as e:
                st.error('Erro ao gerar PDF: ' + str(e))
    
    st.markdown("---")

    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return
        
    for p in produtos:
        produto_id = p.get("id")
        with st.container(border=True):
            cols = st.columns([3,1,1])
            with cols[0]:
                st.markdown(f"### {p.get('nome')} <small style='color:gray'>ID: {produto_id}</small>", unsafe_allow_html=True)
                
                # TRATAMENTO DE ERRO: Exibição segura de preço/quantidade
                try:
                    preco_exibicao = f"R$ {float(p.get('preco')):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except (ValueError, TypeError):
                    preco_exibicao = "R$ N/A"

                st.write(f"**Preço:** {preco_exibicao} • **Quantidade:** {p.get('quantidade', 0)}")
                st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
                
                # TRATAMENTO DE ERRO: Exibição de Data de Validade
                data_validade_str = p.get('data_validade')
                if data_validade_str:
                    try:
                        validade_formatada = datetime.fromisoformat(data_validade_str).strftime('%d/%m/%Y')
                    except (ValueError, TypeError):
                        validade_formatada = 'Data Inválida'
                else:
                    validade_formatada = 'Sem Validade'
                        
                st.write(f"**Validade:** {validade_formatada}")
                
                # Botão de venda
                quantidade_atual = int(p.get("quantidade", 0))
                if quantidade_atual > 0:
                    if st.button("Vender 1 Unidade", key=f'sell_{produto_id}'):
                        try:
                            mark_produto_as_sold(produto_id, 1)
                            st.success(f"1 unidade de '{p.get('nome')}' foi vendida.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao marcar venda: {e}")
                else:
                    st.info("Fora de estoque.")

            with cols[1]:
                # TRATAMENTO DE ERRO: Exibição da foto
                photo_path = os.path.join(ASSETS_DIR, p.get('foto')) if p.get('foto') else None
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, width=120)
                else:
                    st.info('Sem foto')
                    
            with cols[2]:
                role = st.session_state.get('role','staff')
                if st.button('Editar', key=f'mod_{produto_id}'):
                    st.session_state['edit_product_id'] = produto_id
                    st.session_state['edit_mode'] = True
                    st.rerun() # Entra no modo de edição

                # Botão de remover (apenas para Admin)
                if role == 'admin':
                    if st.button('Remover', key=f'rem_{produto_id}'):
                        try:
                            delete_produto(produto_id) # A função já tenta remover a foto no simulado
                            st.warning(f"Produto '{p.get('nome')}' removido.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover produto: {e}")
                else:
                    st.caption('Remover (admin)')
                    
            st.markdown("---")


# --- FLUXO PRINCIPAL DA PÁGINA ---

if not st.session_state.get("logged_in"):
    st.error("Acesso negado. Faça login na área administrativa para gerenciar produtos.")
    st.info("Vá para a página 'Área Administrativa' para entrar ou criar um admin.")
else:
    st.sidebar.markdown(f"**Olá, {st.session_state.get('username')} ({st.session_state.get('role','staff')})**")
    
    # Se estiver no modo de edição, forçamos a exibição do formulário
    if st.session_state.get('edit_mode'):
        show_edit_form()
    else:
        # Caso contrário, mostra o fluxo normal
        action = st.sidebar.selectbox("Ação", ["Visualizar / Modificar / Remover Produtos", "Adicionar Produto"],key='main_action_selector')
        
        if action == "Adicionar Produto":
            add_product_form_com_colunas()
        else:
            manage_products_list()
import os
from datetime import datetime, date
from utils.database import (
    add_produto, get_all_produtos, update_produto, delete_produto, get_produto_by_id,
    export_produtos_to_csv, import_produtos_from_csv, generate_stock_pdf,
    mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, ASSETS_DIR
)

# --- Configurações Iniciais e CSS ---
def load_css(file_name):
    if not os.path.exists(file_name):
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

load_css("style.css")

st.set_page_config(page_title="Gerenciar Produtos - Cores e Fragrâncias")

# Inicialização de estado
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'edit_mode' not in st.session_state: st.session_state['edit_mode'] = False
if 'edit_product_id' not in st.session_state: st.session_state['edit_product_id'] = None

# -------------------------------------------------------------------
# FUNÇÃO DE CADASTRO DE PRODUTO
# -------------------------------------------------------------------
def add_product_form_com_colunas():
    st.subheader("Adicionar Novo Produto")
    
    # Garante que o diretório de assets exista
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    
    with st.form("add_product_form", clear_on_submit=True):
        nome = st.text_input("Nome do Produto", max_chars=150)
        
        col1, col2 = st.columns([3, 1]) 

        with col1:
            st.markdown("##### Detalhes Principais")
            # Adicionei a opção 'Selecionar' para forçar a escolha
            marca = st.selectbox("📝 Marca do Produto", options=['Selecionar'] + MARCAS, key="add_input_marca")
            tipo = st.selectbox("🏷️ Tipo de Produto", options=['Selecionar'] + TIPOS, key="add_input_tipo")
            estilo = st.selectbox("Estilo", ['Selecionar'] + ESTILOS, key="add_input_estilo")
            
            # VALIDAÇÃO: min_value 0.01 para garantir preço positivo
            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", step=1.0)
            quantidade = st.number_input("Quantidade", min_value=0, step=1, value=1)
            
        with col2:
            st.markdown("##### Foto e Validade")
            foto = st.file_uploader("🖼️ Foto do Produto", type=['png', 'jpg', 'jpeg'], key="add_input_foto")
            data_validade = st.date_input(
                "🗓️ Data de Validade", 
                value=date.today(), 
                key="add_input_validade"
            )

        submitted = st.form_submit_button("Adicionar Produto")

        if submitted:
            # TRATAMENTO DE ERRO: Validação de campos obrigatórios
            if not nome or preco <= 0 or quantidade < 0 or marca == 'Selecionar' or tipo == 'Selecionar':
                st.error("Nome, Preço (positivo), Quantidade (não negativa), Marca e Tipo são obrigatórios.")
                return
            
            photo_name = None
            if foto:
                # TRATAMENTO DE ERRO: Salvando a foto
                try:
                    photo_name = f"{int(datetime.now().timestamp())}_{foto.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(foto.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a foto: {e}. Tente novamente.")
                    return
            
            try:
                # Chamada do DB
                add_produto(
                    nome, preco, quantidade, marca, estilo, tipo, 
                    photo_name, data_validade.isoformat()
                )
                st.success(f"Produto '{nome}' adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar produto no banco de dados: {e}")


# -------------------------------------------------------------------
# FUNÇÕES DE EDIÇÃO E LISTAGEM
# -------------------------------------------------------------------

def show_edit_form():
    """Exibe o formulário de edição para o produto selecionado."""
    produto_id = st.session_state.get('edit_product_id')
    produto = get_produto_by_id(produto_id)
    
    if not produto:
        st.error("Produto não encontrado ou ID inválido.")
        st.session_state["edit_mode"] = False
        st.session_state["edit_product_id"] = None
        return

    st.subheader(f"Editar Produto: {produto.get('nome')}")

    # TRATAMENTO DE ERRO: Conversão de data para o date_input
    default_date = None
    if produto.get("data_validade"):
        try:
            default_date = datetime.fromisoformat(produto.get("data_validade")).date()
        except (ValueError, TypeError):
            default_date = date.today() # Usa a data atual se a data armazenada for inválida
            
    # Garantir valores numéricos para o number_input
    default_preco = float(produto.get("preco", 0.01))
    default_quantidade = int(produto.get("quantidade", 0))

    with st.form(key=f"edit_product_form_{produto_id}", clear_on_submit=False):
        nome = st.text_input("Nome", value=produto.get("nome"))
        
        col1, col2 = st.columns(2)
        with col1:
            preco = st.number_input("Preço (R$)", value=default_preco, format="%.2f", min_value=0.01)
        with col2:
            quantidade = st.number_input("Quantidade", value=default_quantidade, step=1, min_value=0)
            
        # Determina o índice de seleção atual (TRATAMENTO DE ERRO: Lida com valores inexistentes)
        marca_index = MARCAS.index(produto.get("marca")) if produto.get("marca") in MARCAS else 0
        estilo_index = ESTILOS.index(produto.get("estilo")) if produto.get("estilo") in ESTILOS else 0
        tipo_index = TIPOS.index(produto.get("tipo")) if produto.get("tipo") in TIPOS else 0

        marca = st.selectbox("Marca", MARCAS, index=marca_index)
        estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index)
        tipo = st.selectbox("Tipo", TIPOS, index=tipo_index)
        
        data_validade = st.date_input("Data de Validade", value=default_date or date.today())
        uploaded = st.file_uploader("Alterar Foto", type=["jpg","png","jpeg"])
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("Salvar Alterações")
        with col_btn2:
            cancel = st.form_submit_button("Cancelar Edição")

        if save:
            if not nome or preco <= 0 or quantidade < 0:
                st.error("Nome, Preço (positivo) e Quantidade (não negativa) são obrigatórios.")
                return

            photo_name = produto.get("foto")
            if uploaded:
                # Remove foto antiga se existir
                if photo_name and os.path.exists(os.path.join(ASSETS_DIR, photo_name)):
                    try: 
                        os.remove(os.path.join(ASSETS_DIR, photo_name))
                    except Exception: 
                        st.warning("Não foi possível remover a foto antiga, mas a nova será salva.")
                
                # Salva nova foto (TRATAMENTO DE ERRO: Salvando a foto)
                try:
                    photo_name = f"{int(datetime.now().timestamp())}_{uploaded.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(uploaded.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a nova foto: {e}")
                    return
            
            validade_iso = data_validade.isoformat() if data_validade else None

            try:
                update_produto(produto_id, nome, preco, quantidade, marca, estilo, tipo, photo_name, validade_iso)
                st.success(f"Produto '{nome}' atualizado com sucesso!")
                st.session_state["edit_mode"] = False
                st.session_state["edit_product_id"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar produto no banco de dados: {e}")
                
        if cancel:
            st.session_state["edit_mode"] = False
            st.session_state["edit_product_id"] = None
            st.rerun()

def manage_products_list():
    st.subheader("Lista de Produtos")
    produtos = get_all_produtos()
    
    # --- Ações de Arquivo (Import/Export/PDF) ---
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        # TRATAMENTO DE ERRO: Exportação CSV
        if st.button('Exportar CSV', key='btn_export_csv'):
            csv_path = os.path.join('data','produtos_export.csv')
            if not os.path.exists('data'): os.makedirs('data')
            try:
                export_produtos_to_csv(csv_path)
                st.success('Exportação CSV concluída (Simulação).')
                # A função download_button do Streamlit precisa de dados reais (não simulação)
                # Para uma simulação, é necessário gerar o conteúdo real do CSV no ambiente real
            except Exception as e:
                st.error('Erro ao exportar CSV: ' + str(e))
                
    with col_b:
        # TRATAMENTO DE ERRO: Importação CSV
        uploaded_csv = st.file_uploader('Importar CSV', type=['csv'], key='import_csv')
        if uploaded_csv is not None and st.button('Processar Importação', key='btn_import'):
            # Simulação: Em um DB real, aqui você processaria o uploaded_csv.getbuffer()
            try:
                # O Simulado fará uma adição fictícia, mas em um DB real processaria o arquivo
                import_produtos_from_csv('simulacao_path') 
                st.success('Produtos importados com sucesso (Simulação).')
                st.rerun()
            except Exception as e:
                st.error('Erro ao importar CSV: ' + str(e))
                
    with col_c:
        # TRATAMENTO DE ERRO: Geração de PDF
        if st.button('Gerar Relatório PDF', key='btn_pdf'):
            pdf_path = os.path.join('data','relatorio_estoque.pdf')
            if not os.path.exists('data'): os.makedirs('data')
            try:
                generate_stock_pdf(pdf_path)
                st.success('PDF gerado (Simulação).')
            except Exception as e:
                st.error('Erro ao gerar PDF: ' + str(e))
    
    st.markdown("---")

    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return
        
    for p in produtos:
        produto_id = p.get("id")
        with st.container(border=True):
            cols = st.columns([3,1,1])
            with cols[0]:
                st.markdown(f"### {p.get('nome')} <small style='color:gray'>ID: {produto_id}</small>", unsafe_allow_html=True)
                
                # TRATAMENTO DE ERRO: Exibição segura de preço/quantidade
                try:
                    preco_exibicao = f"R$ {float(p.get('preco')):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except (ValueError, TypeError):
                    preco_exibicao = "R$ N/A"

                st.write(f"**Preço:** {preco_exibicao} • **Quantidade:** {p.get('quantidade', 0)}")
                st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
                
                # TRATAMENTO DE ERRO: Exibição de Data de Validade
                data_validade_str = p.get('data_validade')
                if data_validade_str:
                    try:
                        validade_formatada = datetime.fromisoformat(data_validade_str).strftime('%d/%m/%Y')
                    except (ValueError, TypeError):
                        validade_formatada = 'Data Inválida'
                else:
                    validade_formatada = 'Sem Validade'
                        
                st.write(f"**Validade:** {validade_formatada}")
                
                # Botão de venda
                quantidade_atual = int(p.get("quantidade", 0))
                if quantidade_atual > 0:
                    if st.button("Vender 1 Unidade", key=f'sell_{produto_id}'):
                        try:
                            mark_produto_as_sold(produto_id, 1)
                            st.success(f"1 unidade de '{p.get('nome')}' foi vendida.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao marcar venda: {e}")
                else:
                    st.info("Fora de estoque.")

            with cols[1]:
                # TRATAMENTO DE ERRO: Exibição da foto
                photo_path = os.path.join(ASSETS_DIR, p.get('foto')) if p.get('foto') else None
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, width=120)
                else:
                    st.info('Sem foto')
                    
            with cols[2]:
                role = st.session_state.get('role','staff')
                if st.button('Editar', key=f'mod_{produto_id}'):
                    st.session_state['edit_product_id'] = produto_id
                    st.session_state['edit_mode'] = True
                    st.rerun() # Entra no modo de edição

                # Botão de remover (apenas para Admin)
                if role == 'admin':
                    if st.button('Remover', key=f'rem_{produto_id}'):
                        try:
                            delete_produto(produto_id) # A função já tenta remover a foto no simulado
                            st.warning(f"Produto '{p.get('nome')}' removido.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover produto: {e}")
                else:
                    st.caption('Remover (admin)')
                    
            st.markdown("---")


# --- FLUXO PRINCIPAL DA PÁGINA ---

if not st.session_state.get("logged_in"):
    st.error("Acesso negado. Faça login na área administrativa para gerenciar produtos.")
    st.info("Vá para a página 'Área Administrativa' para entrar ou criar um admin.")
else:
    st.sidebar.markdown(f"**Olá, {st.session_state.get('username')} ({st.session_state.get('role','staff')})**")
    
    # Se estiver no modo de edição, forçamos a exibição do formulário
    if st.session_state.get('edit_mode'):
        show_edit_form()
    else:
        # Caso contrário, mostra o fluxo normal
        action = st.sidebar.selectbox("Ação", ["Visualizar / Modificar / Remover Produtos", "Adicionar Produto"])
        
        if action == "Adicionar Produto":
            add_product_form_com_colunas()
        else:

            manage_products_list()
def update_produto(product_id, nome, preco, quantidade_total, marca, estilo, tipo, foto, lotes_data):
    """
    Atualiza um produto existente, incluindo a nova estrutura de lotes.
    'lotes_data' é uma lista de dicionários [{'validade': 'YYYY-MM-DD', 'quantidade': X}].
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Serializa a lista de lotes para JSON string
    lotes_json = json.dumps(lotes_data)
    
    cursor.execute(
        """
        UPDATE produtos SET 
            nome=?, 
            preco=?, 
            quantidade=?, 
            marca=?, 
            estilo=?, 
            tipo=?, 
            foto=?, 
            lotes=?
            -- data_adicao não é atualizada, permanece a original
        WHERE id=?
        """,
        (nome, preco, quantidade_total, marca, estilo, tipo, foto, lotes_json, product_id)
    )
    conn.commit()
    conn.close()
