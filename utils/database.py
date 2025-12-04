Você forneceu essencialmente dois conjuntos de código que tentam resolver o mesmo problema (gerenciamento de estoque SQLite), mas usam estruturas de banco de dados e bibliotecas diferentes (um usa reportlab, o outro usa fpdf, pandas e um esquema de DB com lotes e transações).

Para criar um código completo e funcional, vou unificar e refinar o segundo código que você forneceu (que é mais moderno e usa fpdf, pandas, lotes e transações, resolvendo o problema de ter dois códigos separados).

Atenção: Para que este código funcione, você deve instalar as bibliotecas necessárias.

⚠️ Instalação Necessária
Bash

pip install sqlite3 pandas fpdf
📄 Arquivo Único: database_estoque_completo.py
Este script contém todas as funções de utilidade, conexão, CRUD, gestão de lotes, transações e exportação (CSV, Excel, PDF), em um único arquivo, garantindo que não haja erros de ImportError ou sqlite3 de um módulo para outro.

Python

import sqlite3
import os
import hashlib
import json
from datetime import datetime
import pandas as pd
from fpdf import FPDF # Usaremos fpdf para a geração de PDF (melhor suporte a utf-8)

# ====================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E CONSTANTES
# ====================================================================

DATABASE_DIR = "data"
DB_NAME = "estoque.db"
DATABASE = os.path.join(DATABASE_DIR, DB_NAME)
ASSETS_DIR = "assets"

# Assegura que os diretórios existam
if not os.path.exists(DATABASE_DIR): 
    os.makedirs(DATABASE_DIR)
if not os.path.exists(ASSETS_DIR): 
    os.makedirs(ASSETS_DIR)

# Constantes de Categoria
MARCAS = [
    "Eudora", "O Boticário", "Jequiti", "Avon", "Mary Kay", "Natura",
    "Oui-Original-Unique-Individuel", "Pierre Alexander", "Tupperware", "Outra"
]

ESTILOS = [
    "Perfumaria", "Skincare", "Cabelo", "Corpo e Banho", "Make", "Masculinos", 
    "Femininos Nina Secrets", "Marcas", "Infantil", "Casa", "Solar", 
    "Maquiage", "Teen", "Kits e Presentes", "Cuidados com o Corpo", 
    "Lançamentos", "Acessórios de Casa", "Outro"
]

TIPOS = [
    "Perfumaria masculina", "Perfumaria feminina", "Body splash", "Body spray", 
    "Eau de parfum", "Desodorantes", "Perfumaria infantil", "Perfumaria vegana", 
    "Rosto", "Tratamento para o rosto", "Acne", "Limpeza", "Esfoliante", 
    "Tônico facial", "Tratamento para cabelos", "Shampoo", "Condicionador", 
    "Hidratante", "Sabonetes", "Protetor solar", "Outro" # Lista reduzida para clareza
]


# ====================================================================
# FUNÇÕES DE UTILIDADE E CONEXÃO
# ====================================================================

def create_connection():
    """Cria e retorna a conexão com o banco de dados SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        # Define o row_factory para retornar linhas como dicionários (acessíveis por nome de coluna)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao SQLite: {e}")
    return conn

def hash_password(password):
    """Gera o hash SHA256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    """Cria as tabelas 'produtos', 'users' e 'transacoes' se não existirem."""
    conn = create_connection()
    if not conn: return

    cursor = conn.cursor()

    # 1. Tabela de Produtos (com Lotes em JSON)
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
            lotes TEXT -- Armazena a lista de lotes como string JSON
        )
    """)

    # 2. Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    # 3. Tabela de Transações (Histórico de Movimentação)
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
    
    # 4. Cria um usuário admin padrão se ele não existir
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hash_password("123"), "admin"))
    except sqlite3.IntegrityError:
        pass # admin já existe

    conn.commit()
    conn.close()

# Garante que as tabelas sejam criadas na inicialização
create_tables()


# ====================================================================
# FUNÇÕES CRUD E DE TRANSAÇÕES
# ====================================================================

def get_product_from_row(row):
    """Converte uma linha do DB em dicionário e parseia o JSON de lotes."""
    product = dict(row)
    # Tenta converter a string JSON de lotes de volta para lista/dicionário Python
    try:
        product['lotes'] = json.loads(product.get('lotes', '[]'))
    except (json.JSONDecodeError, TypeError):
        product['lotes'] = []
    return product

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
    """Busca todos os produtos e anexa o histórico de transações (parcial)."""
    conn = create_connection()
    produtos = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos ORDER BY nome ASC")
            
            for row in cursor.fetchall():
                produto = get_product_from_row(row)
                
                # Anexa o histórico para exportação/relatórios
                transacoes = get_transacoes_by_produto_id(produto['id'])
                produto['historico_adicao'] = [t['data'] for t in transacoes if t['tipo'] == 'ADICAO']
                produto['historico_venda'] = [t['data'] for t in transacoes if t['tipo'] == 'VENDA']
                
                produtos.append(produto)
                
        except sqlite3.Error as e:
            print(f"Erro ao buscar todos os produtos: {e}")
        finally:
            conn.close()
    return produtos

def get_produto_by_id(product_id):
    """Busca um produto pelo ID."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (product_id,))
    produto = cursor.fetchone()
    conn.close()
    
    if produto:
        return get_product_from_row(produto)
    return None

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

def delete_produto(product_id):
    """Remove um produto, sua foto e suas transações associadas."""
    conn = create_connection()
    if not conn: return
    
    produto = get_produto_by_id(product_id)
    cursor = conn.cursor()
    
    # 1. Apaga a foto
    if produto and produto.get('foto'):
        photo_path = os.path.join(ASSETS_DIR, produto['foto'])
        if os.path.exists(photo_path):
            os.remove(photo_path)
            
    # 2. Deleta o produto e as transações
    cursor.execute("DELETE FROM produtos WHERE id=?", (product_id,))
    cursor.execute("DELETE FROM transacoes WHERE produto_id=?", (product_id,))
    conn.commit()
    conn.close()

def mark_produto_as_sold(produto_id, quantidade_vendida=1):
    """Atualiza a quantidade e registra a transação de venda."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Verifica e atualiza a quantidade no estoque
            cursor.execute("SELECT quantidade FROM produtos WHERE id=?", (produto_id,))
            produto_row = cursor.fetchone()
            if not produto_row:
                raise ValueError("Produto não encontrado.")
                
            estoque_atual = produto_row['quantidade']
            
            if estoque_atual < quantidade_vendida:
                raise ValueError(f"Estoque insuficiente. Disponível: {estoque_atual}.")

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

# ====================================================================
# FUNÇÕES DE LOGIN E USUÁRIOS
# ====================================================================

def add_user(username, password, role="staff"):
    """Adiciona um novo usuário ao banco de dados."""
    hashed_pass = hash_password(password)
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pass, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    """Busca um usuário pelo nome de usuário."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    """Retorna todos os usuários cadastrados (sem senhas)."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users ORDER BY role DESC, username ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

# ====================================================================
# FUNÇÕES DE EXPORTAÇÃO (CSV, EXCEL, PDF)
# ====================================================================

def export_produtos_to_dataframe():
    """Busca todos os produtos e retorna um DataFrame do Pandas."""
    produtos = get_all_produtos()
    
    # Prepara os dados para o DataFrame
    data_for_df = []
    for p in produtos:
        lotes_info = []
        # Garante que 'lotes' está formatado antes de exportar
        if isinstance(p['lotes'], list):
            for lote in p['lotes']:
                try:
                    validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%Y')
                    lotes_info.append(f"Qtd: {lote['quantidade']} (V: {validade})")
                except:
                    lotes_info.append(f"Qtd: {lote['quantidade']} (V: Inválida)")
        
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
    """Cria um arquivo Excel (XLSX) no caminho especificado. Requer openpyxl."""
    # Instale: pip install openpyxl
    df = export_produtos_to_dataframe()
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"Excel exportado para: {filepath}")

def generate_stock_pdf(filepath):
    """Gera um relatório de estoque em PDF usando FPDF."""
    produtos = get_all_produtos()
    
    if not produtos:
        print("Nenhum produto para gerar relatório.")
        return

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Relatório de Estoque e Movimentação', 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 5, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'R')
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
        pdf.cell(0, 7, f"Produto: {produto['nome']} ({produto['marca']})", 1, 1, 'L', 1)
        
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(col_widths[0], 5, 'Detalhe', 1, 0, 'C')
        pdf.cell(col_widths[1], 5, 'Qtd', 1, 0, 'C')
        pdf.cell(col_widths[2], 5, 'Preço', 1, 0, 'C')
        pdf.cell(col_widths[3], 5, 'Lotes (V: Validade)', 1, 0, 'C')
        pdf.cell(col_widths[4], 5, 'Histórico (Adição | Venda)', 1, 1, 'C')

        pdf.set_font('Arial', '', 8)
        
        # Detalhes e Formatação
        preco_formatado = f"R$ {produto['preco']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        adicoes = [datetime.fromisoformat(d).strftime('%d/%m/%y') for d in produto.get('historico_adicao', [])]
        vendas = [datetime.fromisoformat(d).strftime('%d/%m/%y') for d in produto.get('historico_venda', [])]
        
        historico_resumo = f"Add: {len(adicoes)} ({', '.join(adicoes[:2])})"
        historico_resumo += f" | Vnd: {len(vendas)} ({', '.join(vendas[:2])})"

        lotes_info = []
        if isinstance(produto['lotes'], list):
             for lote in produto['lotes']:
                try:
                    validade = datetime.fromisoformat(lote['validade']).strftime('%d/%m/%y')
                    lotes_info.append(f"Q:{lote['quantidade']} V:{validade}")
                except:
                    lotes_info.append("Erro")

        # 1ª Linha de Dados
        pdf.cell(col_widths[0], 5, f"Estilo: {produto['estilo']} | Tipo: {produto['tipo']}", 1, 0, 'L')
        pdf.cell(col_widths[1], 5, str(produto['quantidade']), 1, 0, 'C')
        pdf.cell(col_widths[2], 5, preco_formatado, 1, 0, 'R')
        pdf.cell(col_widths[3], 5, ' / '.join(lotes_info[:2]), 1, 0, 'L')
        pdf.cell(col_widths[4], 5, historico_resumo, 1, 1, 'L')
        
        pdf.ln(3) # Espaçamento entre produtos

    pdf.output(filepath, 'F')
    print(f"PDF gerado e salvo em: {filepath}")

# ====================================================================
# EXEMPLO DE USO (Para Teste)
# ====================================================================

def run_example():
    """Executa um exemplo de CRUD e exportação."""
    print("--- 🛠️ INICIANDO TESTE DO SISTEMA DE ESTOQUE COMPLETO 🛠️ ---")
    
    # 1. Adicionar Produtos
    lotes_perfume = [
        {'validade': '2025-12-31', 'quantidade': 10},
        {'validade': '2026-06-30', 'quantidade': 5}
    ]
    
    add_produto("Perfume Flor de Algodão", 129.90, 15, "Natura", "Perfumaria", "Perfumaria feminina", "foto_flor.png", lotes_perfume)
    print("Produto 1 adicionado.")

    lotes_creme = [
        {'validade': '2024-10-15', 'quantidade': 8} # Lote com validade próxima!
    ]
    add_produto("Creme Mãos de Seda", 35.50, 8, "Mary Kay", "Skincare", "Hidratante", "foto_creme.png", lotes_creme)
    print("Produto 2 adicionado.")
    
    # 2. Listar Produtos
    produtos = get_all_produtos()
    print(f"\n✅ Produtos no Estoque (Total: {len(produtos)}):")
    for p in produtos:
        print(f"  - ID: {p['id']}, Nome: {p['nome']}, Qtd: {p['quantidade']}, Preço: R${p['preco']:.2f}")

    # 3. Registrar Venda
    if produtos:
        primeiro_id = produtos[0]['id']
        try:
            mark_produto_as_sold(primeiro_id, 2)
            print(f"\n✅ Venda de 2 unidades do produto ID {primeiro_id} registrada.")
        except Exception as e:
            print(f"\n❌ Erro na venda: {e}")

    # 4. Exportar Dados
    csv_path = os.path.join(DATABASE_DIR, "relatorio_estoque.csv")
    excel_path = os.path.join(DATABASE_DIR, "relatorio_estoque.xlsx")
    pdf_path = os.path.join(DATABASE_DIR, "relatorio_estoque.pdf")
    
    export_produtos_to_csv(csv_path)
    # export_produtos_to_excel(excel_path) # Descomente se tiver openpyxl instalado
    generate_stock_pdf(pdf_path)

    print("\n--- ✅ TESTE CONCLUÍDO. ARQUIVOS DE RELATÓRIO GERADOS. ---")

if __name__ == '__main__':
    run_example()
