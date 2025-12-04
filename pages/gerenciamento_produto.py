Com certeza! Para corrigir o erro ModuleNotFoundError e fornecer um código Streamlit funcional, eu preciso criar tanto o arquivo da página (gerenciamento_produto.py) quanto o arquivo do módulo que está faltando (database.py).

O módulo database.py será uma simulação que utiliza um arquivo JSON simples para armazenar os dados, em vez de um banco de dados real (como SQLite ou PostgreSQL), para manter a solução completa e funcional em um ambiente Streamlit isolado.

Aqui estão os dois arquivos necessários:

📂 1. Estrutura do Projeto
Para que a importação funcione, sua estrutura de pastas deve ser a seguinte:

.
├── gerenciamento_produto.py  <-- Este é o arquivo que você postou (agora é o Main App)
└── database.py               <-- **Módulo que estava faltando**
Nota: Eu movi o seu código original de pages/gerenciamento_produto.py para a raiz como gerenciamento_produto.py, pois a importação inicial (que não usa from .database) sugere que o database.py está no mesmo nível ou no PYTHONPATH. Para simplificar, vou tratar gerenciamento_produto.py como a sua aplicação principal.

💾 2. Código do Módulo database.py (Simulação)
Este arquivo simula todas as operações de banco de dados (CRUD, exportação, etc.) usando um arquivo JSON como persistência.

Python

# database.py

import json
import os
import pandas as pd
from datetime import datetime
from fpdf import FPDF # Biblioteca externa necessária (pip install fpdf)

# --- Configurações ---
DB_FILE = "produtos_db.json"
ASSETS_DIR = "assets"
DATA_DIR = "data"

# --- Dados de Exemplo (constantes) ---
MARCAS = ["Natura", "Boticário", "Mary Kay", "Eudora", "Outra"]
ESTILOS = ["Floral", "Amadeirado", "Cítrico", "Oriental", "Gourmand"]
TIPOS = ["Perfume", "Creme", "Maquiagem", "Acessório"]

# --- Funções de Ajuda (Gerenciamento de DB) ---

def _load_data():
    """Carrega dados do arquivo JSON (DB simulado)."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _save_data(data):
    """Salva dados no arquivo JSON (DB simulado)."""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")

def _get_next_id(data):
    """Gera o próximo ID sequencial."""
    return max([p['id'] for p in data]) + 1 if data else 1

# --- Funções de CRUD (Expostas para o Streamlit) ---

def add_produto(nome, preco, quantidade, marca, estilo, tipo, foto_nome, lotes_data):
    """Adiciona um novo produto ao DB."""
    data = _load_data()
    next_id = _get_next_id(data)
    
    # Converte lotes para string JSON para persistência
    lotes_json = json.dumps(lotes_data, ensure_ascii=False)
    
    new_produto = {
        "id": next_id,
        "nome": nome,
        "preco": float(preco),
        "quantidade": int(quantidade),
        "marca": marca,
        "estilo": estilo,
        "tipo": tipo,
        "foto": foto_nome,
        "lotes": lotes_json
    }
    data.append(new_produto)
    _save_data(data)

def get_all_produtos():
    """Retorna a lista completa de produtos."""
    return _load_data()

def get_produto_by_id(produto_id):
    """Retorna um produto específico pelo ID."""
    data = _load_data()
    return next((p for p in data if p['id'] == produto_id), None)

def update_produto(produto_id, nome, preco, quantidade, marca, estilo, tipo, foto_nome, final_lotes):
    """Atualiza um produto existente."""
    data = _load_data()
    
    # Converte lotes para string JSON para persistência
    lotes_json = json.dumps(final_lotes, ensure_ascii=False)
    
    for produto in data:
        if produto['id'] == produto_id:
            produto.update({
                "nome": nome,
                "preco": float(preco),
                "quantidade": int(quantidade),
                "marca": marca,
                "estilo": estilo,
                "tipo": tipo,
                "foto": foto_nome,
                "lotes": lotes_json
            })
            _save_data(data)
            return True
    return False

def delete_produto(produto_id):
    """Deleta um produto pelo ID."""
    data = _load_data()
    initial_len = len(data)
    # Remove também a foto, se existir
    produto_to_delete = get_produto_by_id(produto_id)
    if produto_to_delete and produto_to_delete.get('foto'):
        try:
            photo_path = os.path.join(ASSETS_DIR, produto_to_delete['foto'])
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception:
            pass # Ignora erro na remoção da foto
            
    data[:] = [p for p in data if p['id'] != produto_id]
    if len(data) < initial_len:
        _save_data(data)
        return True
    return False
    
def mark_produto_as_sold(produto_id, quantidade_vendida=1):
    """Reduz a quantidade em estoque, afetando o lote mais antigo primeiro."""
    data = _load_data()
    for produto in data:
        if produto['id'] == produto_id:
            if produto['quantidade'] < quantidade_vendida:
                raise ValueError("Quantidade em estoque insuficiente para a venda.")
            
            # 1. Reduz a quantidade total
            produto['quantidade'] -= quantidade_vendida
            
            # 2. Atualiza a lista de lotes (priorizando os mais antigos/vencidos primeiro)
            try:
                lotes = json.loads(produto['lotes'])
            except:
                lotes = []
                
            lotes_sorted = sorted(lotes, key=lambda x: datetime.fromisoformat(x['validade']))
            
            remaining_to_sell = quantidade_vendida
            new_lotes = []

            for lote in lotes_sorted:
                if remaining_to_sell > 0:
                    sold_from_lote = min(lote['quantidade'], remaining_to_sell)
                    lote['quantidade'] -= sold_from_lote
                    remaining_to_sell -= sold_from_lote
                
                if lote['quantidade'] > 0:
                    new_lotes.append(lote)
                    
            if remaining_to_sell > 0:
                # Isso só deve acontecer se a contagem total estiver dessincronizada
                raise Exception("Erro na lógica de lote. Venda incompleta.")
            
            produto['lotes'] = json.dumps(new_lotes, ensure_ascii=False)
            _save_data(data)
            return True
    return False

# --- Funções de Exportação/Relatório ---

def export_produtos_to_csv(filepath):
    """Exporta todos os produtos para um arquivo CSV."""
    df = pd.DataFrame(get_all_produtos())
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    df.to_csv(filepath, index=False, encoding='utf-8')
    return True

def export_produtos_to_excel(filepath):
    """Exporta todos os produtos para um arquivo XLSX."""
    df = pd.DataFrame(get_all_produtos())
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    # Requer 'openpyxl' (pip install openpyxl)
    df.to_excel(filepath, index=False, engine='openpyxl') 
    return True

def import_produtos_from_csv(file_buffer):
    """Importa produtos de um arquivo CSV, assumindo um novo ID."""
    # Neste ambiente simulado, vamos ler o buffer passado pelo Streamlit
    try:
        # Lê o CSV do buffer e usa o encoding correto
        df = pd.read_csv(file_buffer, encoding='utf-8')
        
        produtos_existentes = _load_data()
        
        for _, row in df.iterrows():
            # Cria um novo ID para cada item importado
            next_id = _get_next_id(produtos_existentes)
            
            # Simplesmente pega os campos necessários, ajustando tipos
            # Nota: O campo 'lotes' precisaria de lógica mais complexa na importação real
            produto = {
                "id": next_id,
                "nome": row['nome'],
                "preco": float(row['preco']),
                "quantidade": int(row['quantidade']),
                "marca": row['marca'],
                "estilo": row.get('estilo', 'Desconhecido'),
                "tipo": row.get('tipo', 'Outro'),
                "foto": row.get('foto'),
                # Simulação básica de lote para a importação
                "lotes": json.dumps([
                    {'validade': datetime.now().strftime('%Y-%m-%d'), 'quantidade': int(row['quantidade'])}
                ])
            }
            produtos_existentes.append(produto)
            
        _save_data(produtos_existentes)
        return len(df)
        
    except Exception as e:
        raise Exception(f"Erro ao processar o CSV: {e}")

class PDF(FPDF):
    """Classe para gerar o PDF de Relatório de Estoque."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatório de Estoque - Cores e Fragrâncias', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

def generate_stock_pdf(filepath, produtos):
    """Gera um relatório de estoque em formato PDF."""
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', '', 10)

    # Tabela
    col_widths = [10, 60, 20, 30, 70]
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
    pdf.cell(col_widths[1], 7, 'Nome', 1, 0, 'L', 1)
    pdf.cell(col_widths[2], 7, 'Qtd', 1, 0, 'C', 1)
    pdf.cell(col_widths[3], 7, 'Preço (R$)', 1, 0, 'R', 1)
    pdf.cell(col_widths[4], 7, 'Lotes (Validade/Qtd)', 1, 1, 'L', 1)
    
    pdf.set_font('Arial', '', 9)
    total_estoque = 0
    
    for produto in produtos:
        # Prepara a info dos lotes
        lotes_info = "N/A"
        try:
            lotes = json.loads(produto.get('lotes', '[]'))
            lotes_info = ", ".join([
                f"{datetime.fromisoformat(lote['validade']).strftime('%d/%m/%y')}: {lote['quantidade']}"
                for lote in lotes if lote['quantidade'] > 0
            ])
            if not lotes_info:
                lotes_info = "Sem Lotes Ativos"
        except Exception:
            lotes_info = "Erro ao ler lotes"

        # Prepara o preço em formato brasileiro
        try:
            preco_formatado = f"{float(produto['preco']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            preco_formatado = "N/A"

        # Tenta a linha 1 (Nome e Lotes)
        pdf.cell(col_widths[0], 6, str(produto['id']), 1, 0, 'C')
        pdf.cell(col_widths[1], 6, produto['nome'], 1, 0, 'L')
        pdf.cell(col_widths[2], 6, str(produto['quantidade']), 1, 0, 'C')
        pdf.cell(col_widths[3], 6, preco_formatado, 1, 0, 'R')
        pdf.cell(col_widths[4], 6, lotes_info, 1, 1, 'L')
        
        total_estoque += int(produto['quantidade'])
        
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, f"Total Geral de Itens em Estoque: {total_estoque}", 0, 1, 'R')

    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    pdf.output(filepath, 'F')
    return True

# --- Código Adicional (Login/Permissões) ---
# Simulação de login, já que seu código principal usa st.session_state['logged_in']

def authenticate_user(username, password):
    """Simula a autenticação de usuário."""
    if username == "admin" and password == "123":
        return {"logged_in": True, "role": "admin", "username": "admin"}
    elif username == "user" and password == "123":
        return {"logged_in": True, "role": "staff", "username": "user"}
    return {"logged_in": False, "role": "none", "username": None}
💻 3. Código do Arquivo gerenciamento_produto.py
Este é o seu código original com apenas algumas pequenas correções lógicas e a mudança na importação (que não foi necessária, pois colocamos database.py no mesmo diretório).

O problema de ModuleNotFoundError foi resolvido criando o arquivo database.py e suas funções.

Python

# gerenciamento_produto.py
# (Se este arquivo fosse em pages/, a importação seria: from ..database import (...))
# Mantemos a importação original pois database.py está no mesmo diretório.

import streamlit as st
import os
import json
from datetime import datetime, date
# A linha abaixo agora funciona pois 'database.py' existe no mesmo diretório (ou está no PYTHONPATH)
from database import ( 
    add_produto, get_all_produtos, update_produto, delete_produto, get_produto_by_id,
    export_produtos_to_csv, import_produtos_from_csv, 
    export_produtos_to_excel, 
    generate_stock_pdf,
    mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS, ASSETS_DIR # Importamos as constantes
)

# --- Configurações Iniciais e CSS ---
def load_css(file_name):
    """Carrega e aplica o CSS personalizado, se o arquivo existir."""
    # O arquivo 'style.css' não existe no pacote, então apenas ignoramos a exceção
    if not os.path.exists(file_name):
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

load_css("style.css")

st.set_page_config(page_title="Gerenciar Produtos - Cores e Fragrâncias", layout="wide")

# Inicialização de estado de sessão
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'role' not in st.session_state: st.session_state['role'] = 'staff'
if 'username' not in st.session_state: st.session_state['username'] = None
if 'edit_mode' not in st.session_state: st.session_state['edit_mode'] = False
if 'edit_product_id' not in st.session_state: st.session_state['edit_product_id'] = None
if 'lotes_data' not in st.session_state: st.session_state['lotes_data'] = []
if 'pdf_generated_path' not in st.session_state: st.session_state['pdf_generated_path'] = None 
if 'csv_generated_path' not in st.session_state: st.session_state['csv_generated_path'] = None 
if 'excel_generated_path' not in st.session_state: st.session_state['excel_generated_path'] = None 


# -------------------------------------------------------------------
## 📦 Cadastro de Novo Produto
# -------------------------------------------------------------------
def add_product_form_com_colunas():
    st.subheader("Adicionar Novo Produto")
    
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    
    # Limpa lotes ao iniciar o formulário de adição
    st.session_state['lotes_data'] = [] 
    
    with st.form("add_product_form", clear_on_submit=True): # Alterado para clear_on_submit=True
        
        st.markdown("##### Detalhes Principais")
        col1, col2 = st.columns(2) 
        
        with col1:
            nome = st.text_input("Nome do Produto", max_chars=150, key="add_input_nome")
            marca = st.selectbox("📝 Marca do Produto", options=['Selecionar'] + MARCAS, key="add_input_marca")
            tipo = st.selectbox("🏷️ Tipo de Produto", options=['Selecionar'] + TIPOS, key="add_input_tipo")
            
        with col2:
            estilo = st.selectbox("Estilo", ['Selecionar'] + ESTILOS, key="add_input_estilo")
            # Adicionado placeholder
            preco = st.number_input("Preço (R$)", min_value=0.01, format="%.2f", step=1.0, key="add_input_preco") 
            foto = st.file_uploader("🖼️ Foto do Produto", type=['png', 'jpg', 'jpeg'], key="add_input_foto")
        
        st.markdown("---")
        st.markdown("##### 📦 Lote e Quantidade (Obrigatório)")
        
        col_new1, col_new2 = st.columns(2)
        new_validade = col_new1.date_input("🗓️ Data de Validade", value=date.today(), key="new_validade_lote")
        new_quantidade = col_new2.number_input("Quantidade Inicial", min_value=0, step=1, value=1, key="new_quantidade_lote")
        
        submitted = st.form_submit_button("Adicionar Produto")

        if submitted:
            total_quantidade = new_quantidade
            
            if not nome or preco <= 0 or new_quantidade <= 0 or marca == 'Selecionar' or tipo == 'Selecionar':
                st.error("Nome, Preço (positivo), Quantidade (maior que zero), Marca e Tipo são obrigatórios.")
                return
            
            lotes_data = [{
                'validade': new_validade.isoformat(),
                'quantidade': new_quantidade
            }]
            
            photo_name = None
            if foto:
                try:
                    # Limita o nome do produto para evitar nomes de arquivo muito longos
                    clean_name = nome.replace(' ', '_').replace('/', '_')[:50] 
                    photo_name = f"{clean_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{foto.name.split('.')[-1]}"
                    file_path = os.path.join(ASSETS_DIR, photo_name)
                    with open(file_path, "wb") as f:
                        f.write(foto.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a foto: {e}. Tente novamente.")
                    return
                
            try:
                add_produto(
                    nome, preco, total_quantidade, marca, estilo, tipo, 
                    photo_name, lotes_data
                )
                st.success(f"Produto '{nome}' adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar produto no banco de dados: {e}")


# -------------------------------------------------------------------
## 📝 Edição de Produto 
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

    # Inicialização ou Carga dos Lotes
    if st.session_state.get('edit_id') != produto_id or 'lotes_data' not in st.session_state:
        produto_lotes = []
        try:
            produto_lotes = json.loads(produto.get('lotes', '[]'))
        except (json.JSONDecodeError, TypeError):
             st.warning("Erro ao carregar lotes do banco de dados. Iniciando com lotes vazios.")
             produto_lotes = []
             
        # Garante que os lotes do produto atual sejam carregados UMA VEZ
        st.session_state['lotes_data'] = produto_lotes
        st.session_state['edit_id'] = produto_id
        
    
    default_preco = float(produto.get("preco", 0.01))

    with st.form(key=f"edit_product_form_{produto_id}", clear_on_submit=False):
        
        st.markdown("##### Detalhes Principais")
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome", value=produto.get("nome"), key="edit_nome")
            preco = st.number_input("Preço (R$)", value=default_preco, format="%.2f", min_value=0.01, key="edit_preco")
        
        with col2:
            try:
                marca_index = MARCAS.index(produto.get("marca"))
            except ValueError:
                marca_index = 0
            
            try:
                estilo_index = ESTILOS.index(produto.get("estilo"))
            except ValueError:
                estilo_index = 0
                
            try:
                tipo_index = TIPOS.index(produto.get("tipo"))
            except ValueError:
                tipo_index = 0


            marca = st.selectbox("Marca", MARCAS, index=marca_index, key="edit_marca")
            estilo = st.selectbox("Estilo", ESTILOS, index=estilo_index, key="edit_estilo")
            tipo = st.selectbox("Tipo", TIPOS, index=tipo_index, key="edit_tipo")
            
        uploaded = st.file_uploader("Alterar Foto", type=["jpg","png","jpeg"], key="edit_uploaded_photo")

        st.markdown("---")
        st.markdown("##### 📦 Gestão de Lotes por Validade")

        total_quantidade_calculada = 0
        lotes_para_manter = []
        
        # 2. Exibe e gerencia lotes existentes
        if st.session_state.get('lotes_data'):
            for i, lote in enumerate(st.session_state['lotes_data']):
                col_i1, col_i2, col_i3 = st.columns([0.4, 0.4, 0.2])
                
                try:
                    lote_validade_dt = datetime.fromisoformat(lote['validade']).date()
                except (ValueError, TypeError, KeyError):
                    lote_validade_dt = date.today()

                
                # As keys são únicas por índice
                nova_validade = col_i1.date_input(f"Validade Lote {i+1}", value=lote_validade_dt, key=f"edit_validade_{i}")
                nova_quantidade = col_i2.number_input(f"Quantidade Lote {i+1}", min_value=0, value=lote['quantidade'], key=f"edit_quantidade_{i}")
                
                # Botão para remover precisa de um callback ou um rerun imediato
                if col_i3.button("Remover Lote", key=f"edit_remover_{i}"):
                    # Remove o lote do estado de sessão e força o rerun
                    st.session_state['lotes_data'].pop(i)
                    st.rerun() 
                
                lotes_para_manter.append({
                    'validade': nova_validade.isoformat() if nova_validade else None,
                    'quantidade': nova_quantidade
                })
                total_quantidade_calculada += nova_quantidade
                # Retirado o divisor para não quebrar a formatação da coluna
            
            st.session_state['lotes_data'] = lotes_para_manter # Atualiza o estado
            st.markdown("---")


        # 3. Adicionar novo lote
        st.markdown("##### Adicionar Novo Lote")
        col_new1, col_new2 = st.columns(2)
        # Atenção aos keys para evitar conflito com o form de adicionar produto
        new_validade = col_new1.date_input("Validade do Novo Lote", value=date.today(), key="edit_new_validade_lote")
        new_quantidade = col_new2.number_input("Quantidade do Novo Lote", min_value=0, value=0, key="edit_new_quantidade_lote")
        
        final_quantidade_total = total_quantidade_calculada + new_quantidade
        st.warning(f"Quantidade Total em Estoque (calculada): **{final_quantidade_total}**")
        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("Salvar Alterações")
        with col_btn2:
            cancel = st.form_submit_button("Cancelar Edição")

        if save:
            
            final_lotes = [l for l in st.session_state['lotes_data'] if l['quantidade'] > 0].copy()
            
            if new_quantidade > 0:
                final_lotes.append({
                    'validade': new_validade.isoformat(),
                    'quantidade': new_quantidade
                })
                
            final_quantidade_total = sum(lote['quantidade'] for lote in final_lotes)
            
            if not nome or preco <= 0 or final_quantidade_total < 0:
                st.error("Nome, Preço (positivo) e Quantidade Total (não negativa) são obrigatórios.")
                return

            photo_name = produto.get("foto")
            if uploaded:
                # 1. Tenta remover a foto antiga
                if photo_name and os.path.exists(os.path.join(ASSETS_DIR, photo_name)):
                    try: 
                        os.remove(os.path.join(ASSETS_DIR, photo_name))
                    except Exception: 
                        st.warning("Não foi possível remover a foto antiga, mas a nova será salva.")
                
                # 2. Salva a nova foto
                try:
                    extension = uploaded.name.split('.')[-1]
                    clean_name = nome.replace(' ', '_').replace('/', '_')[:50]
                    photo_name = f"{clean_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
                    file_path = os.path.join(ASSETS_DIR, photo_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                except Exception as e:
                    st.error(f"Erro ao salvar a nova foto: {e}")
                    return
                
            try:
                update_produto(
                    produto_id, nome, preco, final_quantidade_total, marca, 
                    estilo, tipo, photo_name, final_lotes
                )
                st.success(f"Produto '{nome}' atualizado com sucesso!")
                st.session_state["edit_mode"] = False
                st.session_state["edit_product_id"] = None
                st.session_state["edit_id"] = None
                if 'lotes_data' in st.session_state:
                    del st.session_state['lotes_data']
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar produto no banco de dados: {e}")
                
        if cancel:
            st.session_state["edit_mode"] = False
            st.session_state["edit_product_id"] = None
            st.session_state["edit_id"] = None
            if 'lotes_data' in st.session_state:
                del st.session_state['lotes_data']
            st.rerun()

# -------------------------------------------------------------------
## 📋 Lista e Gerenciamento de Produtos
# -------------------------------------------------------------------

def manage_products_list():
    st.subheader("Lista de Produtos")
    produtos = get_all_produtos()
    
    # --- Configurações de Caminho ---
    DATA_DIR = 'data'
    if not os.path.exists(DATA_DIR): 
        os.makedirs(DATA_DIR)
        
    csv_path = os.path.join(DATA_DIR, 'relatorio_estoque.csv')
    excel_path = os.path.join(DATA_DIR, 'relatorio_estoque.xlsx')
    pdf_path = os.path.join(DATA_DIR, 'relatorio_estoque.pdf')
    
    # --- Ações de Arquivo (Import/Export/PDF) ---
    st.markdown("##### 📥 Exportação de Dados e Relatórios")
    col_a, col_b, col_c, col_d = st.columns([1,1,1,1])
    
    # --- CSV Download ---
    with col_a:
        if st.button('Gerar CSV', key='btn_csv'):
            try:
                export_produtos_to_csv(csv_path)
                st.session_state['csv_generated_path'] = csv_path
                st.toast('Arquivo CSV gerado com sucesso!')
                st.rerun()
            except Exception as e:
                st.error(f'Erro ao gerar CSV: {e}')
                st.session_state['csv_generated_path'] = None
        
        if st.session_state.get('csv_generated_path') and os.path.exists(st.session_state['csv_generated_path']):
            try:
                with open(st.session_state['csv_generated_path'], "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar CSV",
                        data=file.read(),
                        file_name="relatorio_estoque.csv",
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Erro ao preparar o download do CSV: {e}")

    # --- Excel Download ---
    with col_b:
        if st.button('Gerar Excel (XLSX)', key='btn_excel'):
            try:
                export_produtos_to_excel(excel_path) 
                st.session_state['excel_generated_path'] = excel_path
                st.toast('Arquivo Excel gerado com sucesso!')
                st.rerun()
            except Exception as e:
                st.error(f'Erro ao gerar Excel: {e}. Certifique-se de que a biblioteca "openpyxl" está instalada (`pip install openpyxl`).')
                st.session_state['excel_generated_path'] = None
        
        if st.session_state.get('excel_generated_path') and os.path.exists(st.session_state['excel_generated_path']):
            try:
                with open(st.session_state['excel_generated_path'], "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar Excel",
                        data=file.read(),
                        file_name="relatorio_estoque.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"Erro ao preparar o download do Excel: {e}")

    # --- PDF Download ---
    with col_c:
        if st.button('Gerar Relatório PDF', key='btn_pdf'):
            try:
                # Função corrigida para aceitar 2 argumentos (filepath, produtos)
                generate_stock_pdf(pdf_path, produtos) 
                st.session_state['pdf_generated_path'] = pdf_path
                st.toast('Relatório PDF gerado com sucesso!')
                st.rerun() 
            except Exception as e:
                st.error(f'Erro ao gerar PDF: {e}. Certifique-se de que a biblioteca "fpdf" está instalada (`pip install fpdf`).')
                st.session_state['pdf_generated_path'] = None
                
        caminho_pdf_gerado = st.session_state.get('pdf_generated_path')
        if caminho_pdf_gerado and os.path.exists(caminho_pdf_gerado):
            try:
                with open(caminho_pdf_gerado, "rb") as file:
                    st.download_button(
                        label="⬇️ Baixar PDF",
                        data=file.read(),
                        file_name="relatorio_estoque.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Erro ao preparar o download do PDF: {e}")
                st.session_state['pdf_generated_path'] = None 

    # --- Importar CSV ---
    with col_d:
        uploaded_csv = st.file_uploader('Importar CSV', type=['csv'], key='import_csv')
        if uploaded_csv is not None and st.button('Processar Importação', key='btn_import'):
            try:
                count = import_produtos_from_csv(uploaded_csv) 
                st.success(f'{count} produtos importados com sucesso!')
                st.rerun()
            except Exception as e:
                st.error('Erro ao importar CSV: ' + str(e))
            
    st.markdown("---")

    if not produtos:
        st.info("Nenhum produto cadastrado.")
        return
        
    for p in produtos:
        produto_id = p.get("id")
        with st.container(border=True):
            cols = st.columns([3,1,1])
            with cols[0]:
                st.markdown(f"### {p.get('nome')} <small style='color:gray; font-size: 14px;'>ID: {produto_id}</small>", unsafe_allow_html=True)
                
                try:
                    # Formatação brasileira: Ponto para milhar e vírgula para decimal (ex: R$ 1.234,56)
                    preco_exibicao = f"R$ {float(p.get('preco', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except (ValueError, TypeError):
                    preco_exibicao = "R$ N/A"

                st.write(f"**Preço:** {preco_exibicao} • **Quantidade Total:** {p.get('quantidade', 0)}")
                st.write(f"**Marca:** {p.get('marca')} • **Estilo:** {p.get('estilo')} • **Tipo:** {p.get('tipo')}")
                
                if p.get('lotes'):
                    lotes_info = []
                    try:
                        # O campo 'lotes' é uma string JSON, precisa ser carregado
                        lotes = json.loads(p['lotes']) 
                        for lote in lotes:
                            # Filtra apenas lotes com quantidade > 0
                            if lote.get('quantidade', 0) > 0: 
                                validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%Y')
                                lotes_info.append(f"Qtd: {lote['quantidade']} (Vence em {validade})")
                        if lotes_info:
                             st.caption("Lotes Ativos: " + " | ".join(lotes_info))
                        else:
                             st.caption("Lotes Ativos: Nenhum lote com estoque.")
                    except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                        st.caption("Lotes Ativos: Estrutura de lote inválida no DB")
                
                
                quantidade_atual = int(p.get("quantidade", 0))
                if quantidade_atual > 0:
                    if st.button("Vender 1 Unidade", key=f'sell_{produto_id}'):
                        try:
                            mark_produto_as_sold(produto_id, 1)
                            st.success(f"1 unidade de '{p.get('nome')}' foi vendida. Estoque atualizado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao marcar venda: {e}")
                else:
                    st.info("Fora de estoque.")

            with cols[1]:
                photo_path = os.path.join(ASSETS_DIR, p.get('foto')) if p.get('foto') else None
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, width=120)
                else:
                    st.info('Sem foto')
                    
            with cols[2]:
                role = st.session_state.get('role','staff')
                if st.button('Editar', key=f'mod_{produto_id}'):
                    # Limpa o estado de download ao entrar no modo de edição
                    st.session_state['pdf_generated_path'] = None 
                    st.session_state['csv_generated_path'] = None 
                    st.session_state['excel_generated_path'] = None 
                    st.session_state['edit_product_id'] = produto_id
                    st.session_state['edit_mode'] = True
                    st.rerun()

                if role == 'admin':
                    if st.button('Remover', key=f'rem_{produto_id}'):
                        try:
                            delete_produto(produto_id)
                            st.warning(f"Produto '{p.get('nome')}' removido.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao remover produto: {e}")
                else:
                    st.caption('Remover (admin)')
                    
            st.markdown("---")


# -------------------------------------------------------------------
## 🔒 Área de Login (Simulação)
# -------------------------------------------------------------------

def show_login():
    st.title("🔒 Área Administrativa")
    st.info("Use **admin/123** para acesso total ou **user/123** para acesso de staff.")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            from database import authenticate_user
            auth_result = authenticate_user(username, password)
            if auth_result["logged_in"]:
                st.session_state['logged_in'] = True
                st.session_state['role'] = auth_result["role"]
                st.session_state['username'] = auth_result["username"]
                st.success(f"Bem-vindo, {auth_result['username'].capitalize()}!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# --- FLUXO PRINCIPAL DA PÁGINA ---

# Adicionado um controle de navegação simulado, já que o código é uma página
page_selector = st.sidebar.selectbox(
    "Navegação",
    ["Login", "Gerenciamento de Produtos"],
    index=1 if st.session_state.get('logged_in') else 0
)

if page_selector == "Login":
    if st.session_state.get("logged_in"):
        st.sidebar.success(f"Logado como **{st.session_state.get('role').capitalize()}**")
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['role'] = 'staff'
            st.session_state['username'] = None
            st.rerun()
    else:
        show_login()
elif page_selector == "Gerenciamento de Produtos":
    if not st.session_state.get("logged_in"):
        st.error("Acesso negado. Faça login na área administrativa para gerenciar produtos.")
        st.info("Selecione 'Login' no menu lateral para entrar.")
    else:
        st.sidebar.markdown(f"**Olá, {st.session_state.get('username')} ({st.session_state.get('role','staff').capitalize()})**")
        
        if st.session_state.get('edit_mode'):
            show_edit_form()
        else:
            action = st.sidebar.selectbox(
                "Ação", 
                ["Visualizar / Modificar / Remover Produtos", "Adicionar Produto"],
                key='main_action_selector'
            )
            
            if action == "Adicionar Produto":
                add_product_form_com_colunas()
            else:
                manage_products_list()
