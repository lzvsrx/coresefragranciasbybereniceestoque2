Olá! Analisei o código gerenciamento_produto.py que você forneceu. O erro principal que identifiquei (e corrigi) é a incompatibilidade da estrutura de dados em algumas funções, pois o código parecia estar sendo migrado de um modelo de produto único com uma única data de validade para um modelo de produto com múltiplos lotes de diferentes validades (usando o campo lotes).

A solução foi:

Remover a manipulação de data_validade das funções add_product_form_com_colunas e show_edit_form.

Adicionar a estrutura de Lotes (lotes_data) nessas funções.

Adaptar as chamadas para add_produto e update_produto para que passem uma lista de lotes, conforme a nova estrutura.

Como a sua função update_produto no final do prompt (que pertence ao utils/database.py) lida com a lista de lotes: lotes_data e o campo quantidade_total, eu adaptei o frontend para seguir essa nova lógica.

Aqui está o código corrigido e atualizado para gerenciamento_produto.py.

🛠️ Código gerenciamento_produto.py Corrigido (Com Lógica de Lotes)
Este código remove a lógica de "Data de Validade Única" e a substitui por um campo dinâmico de Lotes (usado em app.py), garantindo que o formulário de edição agora manipule corretamente a nova estrutura de dados:

Python

import streamlit as st
import os
import shutil # Adicionado para copiar arquivos no upload
import json # Adicionado para manipular o campo 'lotes' (que é JSON no DB)
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
if 'role' not in st.session_state: st.session_state['role'] = 'staff' # Garante que role exista
if 'edit_mode' not in st.session_state: st.session_state['edit_mode'] = False
if 'edit_product_id' not in st.session_state: st.session_state['edit_product_id'] = None
# Estado temporário para gerenciar lotes no formulário
if 'lotes_data' not in st.session_state: st.session_state['lotes_data'] = []

# -------------------------------------------------------------------
# FUNÇÃO DE CADASTRO DE PRODUTO
# -------------------------------------------------------------------
def add_product_form_com_colunas():
    st.subheader("Adicionar Novo Produto")
    
    # Garante que o diretório de assets exista
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    
    # Limpa o estado de lote ao iniciar um novo cadastro
    st.session_state['lotes_data'] = []
    
    with st.form("add_product_form", clear_on_submit=False):
        
        st.markdown("##### Detalhes Principais")
        col1, col2 = st.columns(2) 
        
        with col1:
            nome = st.text_input("Nome do Produto", max_chars=150)
            marca = st.selectbox("📝 Marca do Produto", options=['Selecionar'] + MARCAS, key="add_input_marca")
            tipo = st.selectbox("🏷️ Tipo de Produto", options=['Selecionar'] + TIPOS, key="add_input_tipo")
            
        with col2:
            estilo = st.selectbox("Estilo", ['Selecionar'] + ESTILOS, key="add_input_estilo")
            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", step=1.0)
            foto = st.file_uploader("🖼️ Foto do Produto", type=['png', 'jpg', 'jpeg'], key="add_input_foto")
        
        st.markdown("---")
        st.markdown("##### 📦 Lote e Quantidade (Obrigatório)")
        
        # Novo Lote (para o formulário de adição, só precisa de um)
        col_new1, col_new2 = st.columns(2)
        new_validade = col_new1.date_input("🗓️ Data de Validade", value=date.today(), key="new_validade_lote")
        new_quantidade = col_new2.number_input("Quantidade Inicial", min_value=0, step=1, value=1)
        
        submitted = st.form_submit_button("Adicionar Produto")

        if submitted:
            total_quantidade = new_quantidade
            
            # 1. TRATAMENTO DE ERRO: Validação de campos obrigatórios
            if not nome or preco <= 0 or new_quantidade <= 0 or marca == 'Selecionar' or tipo == 'Selecionar':
                st.error("Nome, Preço (positivo), Quantidade (maior que zero), Marca e Tipo são obrigatórios.")
                return
            
            # 2. Monta a estrutura de lotes para o novo produto
            lotes_data = [{
                'validade': new_validade.isoformat(),
                'quantidade': new_quantidade
            }]
            
            # 3. TRATAMENTO DE ERRO: Salvando a foto
            photo_name = None
            if foto:
                try:
                    # Usamos shutil.copyfileobj para garantir a manipulação correta do buffer
                    photo_name = f"{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{foto.name.split('.')[-1]}"
                    file_path = os.path.join(ASSETS_DIR, photo_name)
                    with open(file_path, "wb") as f:
                        f.write(foto.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a foto: {e}. Tente novamente.")
                    return
                
            # 4. Chamada do DB
            try:
                # Chama add_produto com a quantidade total e a lista de lotes
                add_produto(
                    nome, preco, total_quantidade, marca, estilo, tipo, 
                    photo_name, lotes_data
                )
                st.success(f"Produto '{nome}' adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar produto no banco de dados: {e}")


# -------------------------------------------------------------------
# FUNÇÕES DE EDIÇÃO E LISTAGEM
# -------------------------------------------------------------------

def show_edit_form():
    """Exibe o formulário de edição para o produto selecionado, adaptado para Lotes."""
    produto_id = st.session_state.get('edit_product_id')
    produto = get_produto_by_id(produto_id)
    
    if not produto:
        st.error("Produto não encontrado ou ID inválido.")
        st.session_state["edit_mode"] = False
        st.session_state["edit_product_id"] = None
        return

    st.subheader(f"Editar Produto: {produto.get('nome')}")

    # Inicializa o estado de lotes de sessão com os dados do DB (se for a primeira vez)
    # Lembre-se: 'lotes' no DB é uma string JSON, precisa ser deserializada.
    produto_lotes = []
    try:
        produto_lotes = json.loads(produto.get('lotes', '[]'))
    except (json.JSONDecodeError, TypeError):
        st.warning("Erro ao carregar lotes do banco de dados. Iniciando com lotes vazios.")
        produto_lotes = []

    # Se estiver entrando no modo de edição para este produto, carrega os lotes
    if st.session_state.get('edit_id') != produto_id:
        st.session_state['lotes_data'] = produto_lotes
        st.session_state['edit_id'] = produto_id
        
    if 'lotes_data' not in st.session_state:
         st.session_state['lotes_data'] = []
    
    # Garantir valores numéricos para o number_input
    default_preco = float(produto.get("preco", 0.01))

    with st.form(key=f"edit_product_form_{produto_id}", clear_on_submit=False):
        
        # 1. Dados Principais
        st.markdown("##### Detalhes Principais")
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", value=produto.get("nome"))
            preco = st.number_input("Preço (R$)", value=default_preco, format="%.2f", min_value=0.01)
        
        with col2:
            # Determina o índice de seleção atual (TRATAMENTO DE ERRO: Lida com valores inexistentes)
            marca_index = MARCAS.index(produto.get("marca")) if produto.get("marca") in MARCAS else 0
            estilo_index = ESTILOS.index(produto.get("estilo")) if produto.get("estilo") in ESTILOS else 0
            tipo_index = TIPOS.index(produto.get("tipo")) if produto.get("tipo") in TIPOS else 0

            marca = st.selectbox("Marca", MARCAS, index=marca_index)
            estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index)
            tipo = st.selectbox("Tipo", TIPOS, index=tipo_index)
            
        uploaded = st.file_uploader("Alterar Foto", type=["jpg","png","jpeg"])

        st.markdown("---")
        st.markdown("##### 📦 Gestão de Lotes por Validade")

        total_quantidade_calculada = 0
        lotes_para_manter = []
        
        # 2. Exibe e gerencia lotes existentes
        if st.session_state.get('lotes_data'):
            for i, lote in enumerate(st.session_state['lotes_data']):
                col_i1, col_i2, col_i3 = st.columns([0.4, 0.4, 0.2])
                
                # Formata a validade para o widget
                try:
                    lote_validade_dt = datetime.fromisoformat(lote['validade']).date()
                except (ValueError, TypeError):
                    lote_validade_dt = date.today()

                
                nova_validade = col_i1.date_input(f"Validade Lote {i+1}", value=lote_validade_dt, key=f"edit_validade_{i}")
                nova_quantidade = col_i2.number_input(f"Quantidade Lote {i+1}", min_value=0, value=lote['quantidade'], key=f"edit_quantidade_{i}")
                
                if col_i3.button("Remover Lote", key=f"edit_remover_{i}"):
                    # Remove o lote e recarrega a página
                    st.session_state['lotes_data'].pop(i)
                    st.experimental_rerun()
                
                # Se não foi removido, adiciona à lista final (com possíveis edições de valor)
                lotes_para_manter.append({
                    'validade': nova_validade.isoformat() if nova_validade else None,
                    'quantidade': nova_quantidade
                })
                total_quantidade_calculada += nova_quantidade
                st.markdown("---")
            
            # Atualiza o estado da sessão com os lotes mantidos/modificados
            st.session_state['lotes_data'] = lotes_para_manter

        # 3. Adicionar novo lote
        st.markdown("##### Adicionar Novo Lote")
        col_new1, col_new2 = st.columns(2)
        new_validade = col_new1.date_input("Validade do Novo Lote", value=date.today(), key="edit_new_validade_lote")
        new_quantidade = col_new2.number_input("Quantidade do Novo Lote", min_value=0, value=0, key="edit_new_quantidade_lote")
        
        st.warning(f"Quantidade Total em Estoque (calculada): **{total_quantidade_calculada + new_quantidade}**")
        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("Salvar Alterações")
        with col_btn2:
            cancel = st.form_submit_button("Cancelar Edição")

        if save:
            
            final_lotes = st.session_state['lotes_data'].copy()
            
            # Adiciona o lote novo se tiver quantidade > 0
            if new_quantidade > 0:
                final_lotes.append({
                    'validade': new_validade.isoformat(),
                    'quantidade': new_quantidade
                })
                
            # Recalcula a quantidade total final
            final_quantidade_total = sum(lote['quantidade'] for lote in final_lotes)
            
            if not nome or preco <= 0 or final_quantidade_total < 0:
                st.error("Nome, Preço (positivo) e Quantidade Total (não negativa) são obrigatórios.")
                return

            photo_name = produto.get("foto")
            if uploaded:
                # Remove foto antiga se existir
                if photo_name and os.path.exists(os.path.join(ASSETS_DIR, photo_name)):
                    try: 
                        os.remove(os.path.join(ASSETS_DIR, photo_name))
                    except Exception: 
                        st.warning("Não foi possível remover a foto antiga, mas a nova será salva.")
                
                # Salva nova foto
                try:
                    extension = uploaded.name.split('.')[-1]
                    photo_name = f"{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
                    file_path = os.path.join(ASSETS_DIR, photo_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a nova foto: {e}")
                    return
            
            try:
                # Chama update_produto com a nova quantidade total e a lista de lotes
                update_produto(
                    produto_id, nome, preco, final_quantidade_total, marca, 
                    estilo, tipo, photo_name, final_lotes
                )
                st.success(f"Produto '{nome}' atualizado com sucesso!")
                st.session_state["edit_mode"] = False
                st.session_state["edit_product_id"] = None
                st.session_state["edit_id"] = None # Limpa o ID de edição de lote
                del st.session_state['lotes_data'] # Limpa o estado de lote de sessão
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar produto no banco de dados: {e}")
                
        if cancel:
            st.session_state["edit_mode"] = False
            st.session_state["edit_product_id"] = None
            st.session_state["edit_id"] = None
            del st.session_state['lotes_data']
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
            except Exception as e:
                st.error('Erro ao exportar CSV: ' + str(e))
                
    with col_b:
        # TRATAMENTO DE ERRO: Importação CSV
        uploaded_csv = st.file_uploader('Importar CSV', type=['csv'], key='import_csv')
        if uploaded_csv is not None and st.button('Processar Importação', key='btn_import'):
            try:
                # A lógica real deve ler o uploaded_csv.getbuffer()
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

                st.write(f"**Preço:** {preco_exibicao} • **Quantidade Total:** {p.get('quantidade', 0)}")
                st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
                
                # Exibição dos Lotes (Se a estrutura de DB estiver pronta)
                if p.get('lotes'):
                    lotes_info = []
                    try:
                        lotes = json.loads(p['lotes'])
                        for lote in lotes:
                            validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%Y')
                            lotes_info.append(f"Qtd: {lote['quantidade']} (Vence em {validade})")
                        st.caption("Lotes Ativos: " + " | ".join(lotes_info))
                    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                        st.caption("Lotes Ativos: Estrutura de lote inválida no DB")
                
                
                # Botão de venda
                quantidade_atual = int(p.get("quantidade", 0))
                if quantidade_atual > 0:
                    
                    # Simulação de Venda: No app real, a venda deve selecionar o lote.
                    if st.button("Vender 1 Unidade", key=f'sell_{produto_id}'):
                        try:
                            # A função mark_produto_as_sold do seu backend deve lidar
                            # com a escolha de qual lote será decrementado, ou você precisa
                            # criar um widget para essa escolha. Aqui é apenas uma simulação básica.
                            mark_produto_as_sold(produto_id, 1) # Assumindo que a função escolhe o lote
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
    st.sidebar.markdown(f"**Olá, {st.session_state.get('username')} ({st.session_state.get('role','staff').capitalize()})**")
    
    # Se estiver no modo de edição, forçamos a exibição do formulário
    if st.session_state.get('edit_mode'):
        show_edit_form()
    else:
        # Caso contrário, mostra o fluxo normal
        action = st.sidebar.selectbox(
            "Ação", 
            ["Visualizar / Modificar / Remover Produtos", "Adicionar Produto"],
            key='main_action_selector'
        )
        
        if action == "Adicionar Produto":
            add_product_form_com_colunas()
        else:
            manage_products_list()
