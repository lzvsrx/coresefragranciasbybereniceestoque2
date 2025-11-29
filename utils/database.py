import sqlite3
import pandas as pd
import json
from datetime import datetime
import os
from fpdf import FPDF # Usaremos fpdf para a geração de PDF

# --- Configurações ---
DB_NAME = 'database.db'
ASSETS_DIR = 'assets'
if not os.path.exists(ASSETS_DIR): os.makedirs(ASSETS_DIR)
if not os.path.exists('data'): os.makedirs('data')

MARCAS = ['Marca A', 'Marca B', 'Marca C', 'Outra']
ESTILOS = ['Doce', 'Cítrico', 'Amadeirado', 'Floral', 'Fresco', 'Outro']
TIPOS = ['Perfume', 'Creme', 'Sabonete', 'Body Splash', 'Óleo']

# --- Conexão e Inicialização do Banco de Dados ---
def create_connection():
    """Cria uma conexão com o banco de dados SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao SQLite: {e}")
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL,
                    quantidade INTEGER NOT NULL,
                    marca TEXT,
                    estilo TEXT,
                    tipo TEXT,
                    foto TEXT,
                    lotes TEXT -- JSON string para armazenar [{validade: data, quantidade: 10}]
                )
            """)
            # Tabela para histórico de transações (Adição ou Venda)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    tipo TEXT NOT NULL, -- 'ADICAO' ou 'VENDA'
                    FOREIGN KEY (produto_id) REFERENCES produtos(id)
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao inicializar o banco de dados: {e}")
        finally:
            conn.close()

# Inicializa o DB ao carregar o módulo
init_db()

# --- Funções CRUD e de Gestão de Lotes ---

def add_produto(nome, preco, quantidade, marca, estilo, tipo, foto, lotes_data):
    """Adiciona um novo produto e registra a transação de adição inicial."""
    conn = create_connection()
    if conn:
        try:
            lotes_json = json.dumps(lotes_data)
            cursor = conn.cursor()
            
            # 1. Insere o produto
            cursor.execute("""
                INSERT INTO produtos (nome, preco, quantidade, marca, estilo, tipo, foto, lotes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, preco, quantidade, marca, estilo, tipo, foto, lotes_json))
            
            produto_id = cursor.lastrowid
            
            # 2. Registra a transação de adição inicial
            data_atual = datetime.now().isoformat()
            if quantidade > 0:
                cursor.execute("""
                    INSERT INTO transacoes (produto_id, data, quantidade, tipo)
                    VALUES (?, ?, ?, ?)
                """, (produto_id, data_atual, quantidade, 'ADICAO'))
            
            conn.commit()
            return produto_id
        except sqlite3.Error as e:
            print(f"Erro ao adicionar produto: {e}")
        finally:
            conn.close()

def update_produto(id, nome, preco, quantidade, marca, estilo, tipo, foto, lotes_data):
    """Atualiza um produto existente."""
    conn = create_connection()
    if conn:
        try:
            lotes_json = json.dumps(lotes_data)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE produtos SET nome=?, preco=?, quantidade=?, marca=?, estilo=?, tipo=?, foto=?, lotes=?
                WHERE id=?
            """, (nome, preco, quantidade, marca, estilo, tipo, foto, lotes_json, id))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao atualizar produto: {e}")
        finally:
            conn.close()

def delete_produto(id):
    """Deleta um produto e suas transações associadas."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produtos WHERE id=?", (id,))
            cursor.execute("DELETE FROM transacoes WHERE produto_id=?", (id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao deletar produto: {e}")
        finally:
            conn.close()

def get_produto_by_id(id):
    """Busca um produto pelo ID."""
    conn = create_connection()
    produto = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE id=?", (id,))
            produto = cursor.fetchone()
            if produto:
                return dict(produto)
        except sqlite3.Error as e:
            print(f"Erro ao buscar produto: {e}")
        finally:
            conn.close()
    return produto
    
def get_transacoes_by_produto_id(produto_id):
    """Busca o histórico de transações de um produto."""
    conn = create_connection()
    transacoes = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT data, quantidade, tipo FROM transacoes WHERE produto_id=? ORDER BY data DESC", (produto_id,))
            transacoes = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro ao buscar transações: {e}")
        finally:
            conn.close()
    return transacoes

def get_all_produtos():
    """Busca todos os produtos e anexa o histórico de transações."""
    conn = create_connection()
    produtos = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos ORDER BY nome ASC")
            
            for row in cursor.fetchall():
                produto = dict(row)
                
                # Anexa o histórico de transações
                transacoes = get_transacoes_by_produto_id(produto['id'])
                
                produto['historico_adicao'] = [t['data'] for t in transacoes if t['tipo'] == 'ADICAO']
                produto['historico_venda'] = [t['data'] for t in transacoes if t['tipo'] == 'VENDA']
                
                produtos.append(produto)
                
        except sqlite3.Error as e:
            print(f"Erro ao buscar todos os produtos: {e}")
        finally:
            conn.close()
    return produtos

def mark_produto_as_sold(produto_id, quantidade_vendida=1):
    """Marca uma unidade do produto como vendida e registra a transação."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Verifica e atualiza a quantidade no estoque
            cursor.execute("SELECT quantidade FROM produtos WHERE id=?", (produto_id,))
            estoque_atual = cursor.fetchone()['quantidade']
            
            if estoque_atual < quantidade_vendida:
                raise ValueError("Estoque insuficiente para a venda.")

            nova_quantidade = estoque_atual - quantidade_vendida
            
            cursor.execute("UPDATE produtos SET quantidade=? WHERE id=?", (nova_quantidade, produto_id))
            
            # 2. Registra a transação de venda
            data_atual = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO transacoes (produto_id, data, quantidade, tipo)
                VALUES (?, ?, ?, ?)
            """, (produto_id, data_atual, quantidade_vendida, 'VENDA'))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao marcar produto como vendido: {e}")
        except ValueError as e:
             raise e
        finally:
            conn.close()
    return False

# --- Funções de Importação/Exportação (CSV, Excel, PDF) ---

def import_produtos_from_csv(filepath):
    """Simulação de importação de CSV (requer lógica para lidar com lotes e transações)."""
    # Esta é uma simulação simples. Importação real precisa de lógica robusta.
    print(f"Importando dados do arquivo: {filepath} (Simulação)")
    # df = pd.read_csv(filepath)
    # for index, row in df.iterrows():
    #     add_produto(...)
    pass

def export_produtos_to_dataframe():
    """Busca todos os produtos e retorna um DataFrame do Pandas."""
    produtos = get_all_produtos()
    
    # Prepara os dados para o DataFrame, desmembrando o JSON de lotes e histórico
    data_for_df = []
    for p in produtos:
        lotes_str = p.get('lotes', '[]')
        lotes_info = []
        try:
            lotes = json.loads(lotes_str)
            for lote in lotes:
                validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%Y')
                lotes_info.append(f"Qtd: {lote['quantidade']} (V: {validade})")
        except (json.JSONDecodeError, ValueError, TypeError):
            lotes_info.append("Erro/Inválido")
            
        # Formata o histórico
        adicoes = [datetime.fromisoformat(d).strftime('%d/%m/%Y %H:%M') for d in p.get('historico_adicao', [])]
        vendas = [datetime.fromisoformat(d).strftime('%d/%m/%Y %H:%M') for d in p.get('historico_venda', [])]
        
        data_for_df.append({
            'ID': p['id'],
            'Nome': p['nome'],
            'Preço (R$)': p['preco'],
            'Qtd Total': p['quantidade'],
            'Marca': p['marca'],
            'Estilo': p['estilo'],
            'Tipo': p['tipo'],
            'Lotes': "; ".join(lotes_info),
            'Histórico de Adição': " | ".join(adicoes),
            'Histórico de Venda': " | ".join(vendas),
            'Foto Filename': p.get('foto', '')
        })
        
    return pd.DataFrame(data_for_df)

def export_produtos_to_csv(filepath):
    """Cria um arquivo CSV no caminho especificado."""
    df = export_produtos_to_dataframe()
    # Usa o separador ';' para compatibilidade com o Excel no Brasil
    df.to_csv(filepath, index=False, sep=';', encoding='utf-8-sig')
    print(f"CSV exportado para: {filepath}")

def export_produtos_to_excel(filepath):
    """Cria um arquivo Excel (XLSX) no caminho especificado."""
    df = export_produtos_to_dataframe()
    # Requer a biblioteca openpyxl
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"Excel exportado para: {filepath}")

def generate_stock_pdf(filepath, produtos):
    """
    Gera um relatório de estoque em PDF.
    
    Argumentos:
        filepath (str): Caminho onde o PDF será salvo.
        produtos (list): Lista de produtos, incluindo o histórico (retorno de get_all_produtos).
    """
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Relatório de Estoque e Movimentação', 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 5, f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'R')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF('P', 'mm', 'A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', '', 10)
    
    # Larguras das colunas
    col_widths = [50, 15, 20, 30, 70] # Nome, Qtd, Preço, Validades, Histórico
    
    for produto in produtos:
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, f"{produto['nome']} (ID: {produto['id']})", 1, 1, 'L', 1)
        
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(col_widths[0], 5, 'Detalhe', 1, 0, 'C')
        pdf.cell(col_widths[1], 5, 'Qtd', 1, 0, 'C')
        pdf.cell(col_widths[2], 5, 'Preço', 1, 0, 'C')
        pdf.cell(col_widths[3], 5, 'Lotes/Validade', 1, 0, 'C')
        pdf.cell(col_widths[4], 5, 'Histórico (Adição | Venda)', 1, 1, 'C')

        pdf.set_font('Arial', '', 8)
        
        # Detalhes do produto
        preco_formatado = f"R$ {produto['preco']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        # Preparar Histórico (para caber na célula)
        adicoes = [datetime.fromisoformat(d).strftime('%d/%m/%y') for d in produto.get('historico_adicao', [])]
        vendas = [datetime.fromisoformat(d).strftime('%d/%m/%y') for d in produto.get('historico_venda', [])]
        
        historico_resumo = f"Add: {len(adicoes)} ({', '.join(adicoes[:2])})"
        historico_resumo += f" | Vnd: {len(vendas)} ({', '.join(vendas[:2])})"

        # Preparar Lotes (para caber na célula)
        lotes_info = []
        try:
            lotes = json.loads(produto.get('lotes', '[]'))
            for lote in lotes:
                validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%y')
                lotes_info.append(f"Q:{lote['quantidade']} V:{validade}")
        except:
            lotes_info = ["Erro"]

        # 1ª Linha de Dados
        pdf.cell(col_widths[0], 5, f"Marca: {produto['marca']}", 1, 0, 'L')
        pdf.cell(col_widths[1], 5, str(produto['quantidade']), 1, 0, 'C')
        pdf.cell(col_widths[2], 5, preco_formatado, 1, 0, 'R')
        pdf.cell(col_widths[3], 5, ' / '.join(lotes_info[:2]), 1, 0, 'L')
        pdf.cell(col_widths[4], 5, historico_resumo, 1, 1, 'L')
        
        # 2ª Linha de Dados (Tipo/Estilo)
        pdf.cell(col_widths[0], 5, f"Tipo: {produto['tipo']} | Estilo: {produto['estilo']}", 1, 1, 'L')
        
        pdf.ln(3) # Espaçamento entre produtos

    pdf.output(filepath, 'F')
    print(f"PDF gerado e salvo em: {filepath}")

# --- Funções de Dummy (não necessitam de corpo no utils/database.py, mas estão aqui para completude) ---
# import_produtos_from_csv já foi definido acima como uma simulação
