import streamlit as st
import os
from datetime import datetime, date
from utils.database import (
    add_produto, get_all_produtos, update_produto, delete_produto, get_produto_by_id,
    export_produtos_to_csv_content, import_produtos_from_csv_buffer, generate_stock_pdf_bytes,
    mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, ASSETS_DIR
)

# --- FUNÇÃO CSS ADICIONADA ---
def load_css(file_name="style.css"):
    """Carrega e aplica o CSS personalizado, forçando a codificação UTF-8."""
    if os.path.exists(file_name):
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Chama o CSS para esta página
load_css()
# -----------------------------

# --- Verificação de Login ---
if not st.session_state.get("logged_in"):
    st.error("🔒 **Acesso Restrito.** Por favor, faça login na Área Administrativa.")
    st.stop()
    
# Inicialização de estado para Edição
if 'edit_mode' not in st.session_state: st.session_state['edit_mode'] = False
if 'edit_product_id' not in st.session_state: st.session_state['edit_product_id'] = None

# --- Helpers ---
def format_to_brl(value):
    """Formata um float para string no formato R$ 1.234,56."""
    try:
        # Troca ponto por X, vírgula por ponto, X por vírgula (solução para o float)
        return f"R$ {float(value):_.2f}".replace('.', 'X').replace('_', '.').replace('X', ',')
    except (ValueError, TypeError):
        return "R$ N/A"

# -------------------------------------------------------------------
# FUNÇÃO DE CADASTRO DE PRODUTO
# -------------------------------------------------------------------
def add_product_form():
    st.subheader("➕ Adicionar Novo Produto")
    
    with st.form("add_product_form", clear_on_submit=True):
        nome = st.text_input("Nome do Produto", max_chars=150)
        
        col1, col2 = st.columns([3, 1]) 

        with col1:
            st.markdown("##### Detalhes")
            # Marca, Estilo e Tipo são obrigatórios e forçam a escolha
            marca = st.selectbox("📝 Marca", options=['Selecionar'] + MARCAS, key="add_input_marca")
            estilo = st.selectbox("Estilo", ['Selecionar'] + ESTILOS, key="add_input_estilo")
            tipo = st.selectbox("🏷️ Tipo", options=['Selecionar'] + TIPOS, key="add_input_tipo")

            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", step=1.0)
            quantidade = st.number_input("Quantidade em Estoque", min_value=1, step=1, value=1)
            
            data_validade = st.date_input("🗓️ Data de Validade (Opcional)", 
                                           value=None, 
                                           min_value=date.today(), 
                                           key="add_input_validade_lote")
            
        with col2:
            st.markdown("##### Foto do Produto")
            foto = st.file_uploader("🖼️ Foto", type=['png', 'jpg', 'jpeg'], key="add_input_foto")
            

        submitted = st.form_submit_button("Cadastrar Produto")

        if submitted:
            # Validação de campos obrigatórios
            if not nome or preco <= 0 or quantidade <= 0 or marca == 'Selecionar' or tipo == 'Selecionar':
                st.error("Nome, Preço (>0), Quantidade (>0), Marca e Tipo são obrigatórios.")
                return
            
            photo_name = None
            if foto:
                try:
                    # Cria um nome único baseado no timestamp
                    photo_name = f"{int(datetime.now().timestamp())}_{foto.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(foto.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a foto: {e}. Tente novamente.")
                    return
            
            try:
                validade_iso = data_validade.isoformat() if data_validade else None
                add_produto(
                    nome, preco, quantidade, marca, estilo, tipo, 
                    photo_name, validade_iso
                )
                st.success(f"Produto '{nome}' ({quantidade} unidades) adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar produto no banco de dados: {e}")


# -------------------------------------------------------------------
# FUNÇÃO DE EDIÇÃO 
# -------------------------------------------------------------------
def show_edit_form():
    """Exibe o formulário de edição para o produto selecionado."""
    produto_id = st.session_state.get('edit_product_id')
    produto = get_produto_by_id(produto_id)

    if not produto:
        st.error("Produto não encontrado.")
        st.session_state["edit_mode"] = False
        st.session_state["edit_product_id"] = None
        return

    st.subheader(f"✏️ Editar Produto: {produto.get('nome')} (ID {produto_id})")

    default_preco = float(produto.get("preco", 0.01))
    default_quantidade = int(produto.get("quantidade", 1))
    
    # Converte data de ISO para objeto date para o date_input
    default_validade = None
    if produto.get('data_validade'):
        try:
            default_validade = datetime.fromisoformat(produto['data_validade']).date()
        except (ValueError, TypeError):
            pass

    with st.form(key=f"edit_product_form_{produto_id}", clear_on_submit=False):
        # Campos principais
        nome = st.text_input("Nome", value=produto.get("nome"))
        preco = st.number_input("Preço (R$)", value=default_preco, format="%.2f", min_value=0.01)
        quantidade = st.number_input("Quantidade em Estoque", value=default_quantidade, min_value=0, step=1)
        
        # Selectbox para atributos (usa index para preencher o valor atual)
        marca_index = MARCAS.index(produto.get("marca")) if produto.get("marca") in MARCAS else 0
        estilo_index = ESTILOS.index(produto.get("estilo")) if produto.get("estilo") in ESTILOS else 0
        tipo_index = TIPOS.index(produto.get("tipo")) if produto.get("tipo") in TIPOS else 0

        marca = st.selectbox("Marca", MARCAS, index=marca_index)
        estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index)
        tipo = st.selectbox("Tipo", TIPOS, index=tipo_index)
        
        data_validade = st.date_input("🗓️ Data de Validade (Opcional)", 
                                       value=default_validade, 
                                       key="edit_validade")
                                       
        uploaded = st.file_uploader("Alterar Foto", type=["jpg","png","jpeg"])
        st.caption(f"Foto atual: {produto.get('foto') or 'Nenhuma'}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("Salvar Alterações")
        with col_btn2:
            cancel = st.form_submit_button("Cancelar Edição")

        if save:
            if not nome or preco <= 0 or quantidade < 0:
                st.error("Nome, Preço (>0) e Quantidade (>=0) são obrigatórios.")
                return

            photo_name = produto.get("foto")
            if uploaded:
                # Lógica para remover e salvar nova foto...
                if photo_name and os.path.exists(os.path.join(ASSETS_DIR, photo_name)):
                    try: os.remove(os.path.join(ASSETS_DIR, photo_name))
                    except Exception: st.warning("Não foi possível remover a foto antiga.")
                
                try:
                    photo_name = f"{int(datetime.now().timestamp())}_{uploaded.name}"
                    with open(os.path.join(ASSETS_DIR, photo_name), "wb") as f:
                        f.write(uploaded.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a nova foto: {e}")
                    return
            
            try:
                validade_iso = data_validade.isoformat() if data_validade else None
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

# -------------------------------------------------------------------
# FUNÇÃO DE LISTAGEM, AÇÕES E DOWNLOADS
# -------------------------------------------------------------------
def manage_products_list_actions():
    st.title("🛠️ Gerenciar Produtos e Relatórios")
    
    # --- Ações de Arquivo (Download/Upload) ---
    st.subheader("Ferramentas de Arquivo e Relatórios")
    col_a, col_b, col_c = st.columns(3)
    
    # 1. Exportar CSV
    csv_content = export_produtos_to_csv_content() 
    with col_a:
        st.download_button(
            label='⬇️ Baixar CSV Completo',
            data=csv_content.encode('utf-8'),
            file_name=f'estoque_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            key='btn_download_csv'
        )

    # 2. Importação CSV
    with col_b:
        uploaded_csv = st.file_uploader('⬆️ Importar CSV (Adiciona Novos Produtos)', type=['csv'], key='import_csv')
        if uploaded_csv is not None and st.button('Processar Importação', key='btn_import'):
            try:
                count = import_produtos_from_csv_buffer(uploaded_csv)
                st.success(f'{count} produtos importados com sucesso! (Novos itens adicionados).')
                st.rerun()
            except Exception as e:
                st.error('Erro ao importar CSV: ' + str(e))
                
    # 3. Gerar PDF
    with col_c:
        if st.button('⬇️ Gerar Relatório PDF (Estoque Ativo)', key='btn_pdf_gen'):
            try:
                pdf_bytes = generate_stock_pdf_bytes() 
                st.download_button(
                    label='Baixar PDF',
                    data=pdf_bytes,
                    file_name=f'relatorio_estoque_ativo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    mime='application/pdf',
                    key='btn_download_pdf'
                )
                st.success('PDF gerado. Use o botão logo abaixo para baixar.')
            except Exception as e:
                st.error('Erro ao gerar PDF: ' + str(e))
    
    st.markdown("---")
    st.subheader("Visualizar / Ações (Edição/Remoção/Venda)")
    
    produtos = get_all_produtos()
    if not produtos:
        st.info("Nenhum produto cadastrado no estoque.")
        return
        
    total_valor_estoque = 0.0 
        
    for p in produtos:
        produto_id = p.get("id")
        
        try:
            preco_float = float(p.get('preco', 0.00))
            quantidade_int = int(p.get('quantidade', 0))
            
            # Formatação BRL
            preco_exibicao = format_to_brl(preco_float)
            
            valor_total_produto = preco_float * quantidade_int
            total_valor_estoque += valor_total_produto
            
            valor_total_produto_exibicao = format_to_brl(valor_total_produto)
            
        except (ValueError, TypeError):
            preco_exibicao = "R$ N/A"
            valor_total_produto_exibicao = "R$ N/A"
            
        # Formatação de Data de Validade
        validade_exibicao = p.get('data_validade') or '-'
        if validade_exibicao != '-':
             try:
                validade_exibicao = datetime.fromisoformat(validade_exibicao).strftime('%d/%m/%Y')
             except (ValueError, TypeError):
                pass
        
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"### {p.get('nome')} <small style='color:gray'>ID: {produto_id}</small>", unsafe_allow_html=True)
                
                st.write(f"**Preço Unitário:** {preco_exibicao} • **Quantidade em Estoque:** **{quantidade_int}**")
                st.write(f"**VALOR TOTAL DESTE PRODUTO:** **{valor_total_produto_exibicao}**")
                st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
                st.write(f"**Validade:** {validade_exibicao}")
                
                # Ações de Venda e Outras
                if quantidade_int > 0:
                    st.markdown("---")
                    col_venda, _ = st.columns([0.3, 0.7])
                    with col_venda:
                        if st.button("💰 Vender 1 Unidade", key=f'sell_{produto_id}'):
                            try:
                                mark_produto_as_sold(produto_id, 1) 
                                st.success(f"1 unidade de '{p.get('nome')}' foi vendida.")
                                st.rerun()
                            except ValueError as e: # Captura a exceção de estoque insuficiente
                                st.error(f"Erro: {e}")
                            except Exception as e:
                                st.error(f"Erro ao marcar venda: {e}")
                else:
                    st.info("Produto fora de estoque.")

            with cols[1]:
                # Exibição da foto
                photo_path = os.path.join(ASSETS_DIR, p.get('foto')) if p.get('foto') else None
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, width=120)
                else:
                    st.info('Sem foto')
                    
            with cols[2]:
                role = st.session_state.get('role','staff')
                if st.button('✏️ Editar', key=f'mod_{produto_id}'):
                    st.session_state['edit_product_id'] = produto_id
                    st.session_state['edit_mode'] = True
                    st.rerun() 

                # Apenas admin pode remover
                if role == 'admin':
                    if st.button('🗑️ Remover', key=f'rem_{produto_id}'):
                        try:
                            delete_produto(produto_id)
                            st.warning(f"Produto '{p.get('nome')}' removido.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover produto: {e}")
                else:
                    st.caption('Remover (admin)')
                    
    st.markdown("---")
    st.markdown(f"## 💰 **Valor Total do Estoque: {format_to_brl(total_valor_estoque)}**")


# --- FLUXO PRINCIPAL DA PÁGINA ---

if st.session_state.get('edit_mode'):
    show_edit_form()
else:
    # Opções na barra lateral para navegação entre as ações principais
    action = st.sidebar.selectbox("Ações de Gerenciamento", ["Visualizar / Ações", "Adicionar Produto"])
    
    if action == "Adicionar Produto":
        add_product_form()
    else:
        manage_products_list_actions()
