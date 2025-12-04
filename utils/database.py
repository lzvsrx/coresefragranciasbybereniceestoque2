import sqlite3
import os
import hashlib
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime

# ====================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E CONSTANTES
# ====================================================================

DATABASE_DIR = "data"
DATABASE = os.path.join(DATABASE_DIR, "estoque.db")
ASSETS_DIR = "assets"

# Assegura que os diretórios existam
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# Listas de categorias
MARCAS = [
    "Eudora", "O Boticário", "Jequiti", "Avon", "Mary Kay", "Natura",
    "Oui-Original-Unique-Individuel", "Pierre Alexander", "Tupperware", "Outra"
]

ESTILOS = [
    "Perfumaria", "Skincare", "Cabelo", "Corpo e Banho", "Make", "Masculinos", "Femininos Nina Secrets",
    "Marcas", "Infantil", "Casa", "Solar", "Maquiage", "Teen", "Kits e Presentes",
    "Cuidados com o Corpo", "Lançamentos",
    "Acessórios de Casa", "Outro"
]

TIPOS = [
    "Perfumaria masculina", "Perfumaria feminina", "Body splash", "Body spray", "Eau de parfum",
    "Desodorantes", "Perfumaria infantil", "Outro" # Lista encurtada para concisão
]


# ====================================================================
# FUNÇÕES DE UTILIDADE E CONEXÃO
# ====================================================================

def get_db_connection():
    """Retorna um objeto de conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE)
    # Define o row_factory para retornar linhas como dicionários (acessíveis por nome de coluna)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Gera o hash SHA256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return stored_hash == hash_password(provided_password)

def create_tables():
    """Cria as tabelas 'produtos' e 'users' se não existirem, e cria um usuário 'admin' padrão."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Cria a tabela 'produtos'
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
            data_validade TEXT,
            vendido INTEGER DEFAULT 0,
            data_ultima_venda TEXT
        );
    """)

    # 2. Cria a tabela 'users'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    """)
    
    # 3. Cria um usuário admin padrão se ele não existir
    try:
        # Senha padrão para admin: 123
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hash_password("123"), "admin"))
    except sqlite3.IntegrityError:
        # admin já existe
        pass 

    conn.commit()
    conn.close()

# Garante que as tabelas sejam criadas na inicialização
create_tables()


# ====================================================================
# FUNÇÕES DE PRODUTOS (CRUD)
# ====================================================================

def add_produto(nome, preco, quantidade, marca, estilo, tipo, foto=None, data_validade=None):
    """Adiciona um novo produto ao DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade)
    )
    conn.commit()
    conn.close()
    print(f"Produto '{nome}' adicionado com sucesso.")

def get_all_produtos():
    """Retorna todos os produtos, ordenados por nome."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY nome ASC") 
    produtos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return produtos

def get_produto_by_id(product_id):
    """Busca um produto pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (product_id,))
    produto = cursor.fetchone()
    conn.close()
    return dict(produto) if produto else None

def update_produto(product_id, nome, preco, quantidade, marca, estilo, tipo, foto, data_validade):
    """Atualiza um produto existente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE produtos SET nome=?, preco=?, quantidade=?, marca=?, estilo=?, tipo=?, foto=?, data_validade=?
        WHERE id=?
        """,
        (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade, product_id)
    )
    conn.commit()
    conn.close()
    print(f"Produto ID {product_id} atualizado com sucesso.")

def delete_produto(product_id):
    """Remove um produto e sua foto associada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Recupera o produto para apagar a foto
    produto = get_produto_by_id(product_id)
    if produto and produto.get('foto'):
        photo_path = os.path.join(ASSETS_DIR, produto['foto'])
        try:
            os.remove(photo_path)
            print(f"Foto '{produto['foto']}' removida.")
        except FileNotFoundError:
            print(f"Aviso: Foto '{produto['foto']}' não encontrada no sistema de arquivos.")
        except OSError as e:
            print(f"Erro ao remover foto: {e}")

    # 2. Deleta do banco de dados
    cursor.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    print(f"Produto ID {product_id} deletado com sucesso.")

def mark_produto_as_sold(product_id, quantity_sold=1):
    """Atualiza a quantidade e registra a última venda."""
    produto = get_produto_by_id(product_id)
    if not produto:
        print(f"Erro: Produto ID {product_id} não encontrado.")
        return False
        
    current_quantity = produto['quantidade']
    if current_quantity < quantity_sold:
        print(f"Erro: Venda de {quantity_sold} não realizada. Apenas {current_quantity} em estoque.")
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usa ISO format para facilitar a conversão de volta
    cursor.execute(
        "UPDATE produtos SET quantidade = quantidade - ?, vendido = 1, data_ultima_venda = ? WHERE id = ?",
        (quantity_sold, datetime.now().isoformat(), product_id)
    )
    conn.commit()
    conn.close()
    print(f"Venda de {quantity_sold} unidade(s) do produto '{produto['nome']}' registrada.")
    return True

# ====================================================================
# FUNÇÕES DE USUÁRIOS (LOGIN/ADMIN)
# ====================================================================

def login_user(username, password):
    """Autentica um usuário e retorna seu papel ('admin'/'staff') se o login for bem-sucedido."""
    user = get_user(username)
    if user and verify_password(user['password'], password):
        return user['role']
    return None

def add_user(username, password, role="staff"):
    """Adiciona um novo usuário (admin ou staff) ao banco de dados."""
    hashed_pass = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pass, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Erro: Usuário '{username}' já existe.")
        return False
    finally:
        conn.close()

def get_user(username):
    """Busca um usuário pelo nome de usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    """Retorna todos os usuários cadastrados (sem senhas)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users ORDER BY role DESC, username ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

# ====================================================================
# FUNÇÕES DE EXPORTAÇÃO/IMPORTAÇÃO (CSV/PDF)
# ====================================================================

def export_produtos_to_csv(filepath):
    """Exporta todos os produtos para um arquivo CSV."""
    produtos = get_all_produtos()
    if not produtos:
        print("Nenhum produto para exportar.")
        return
        
    fieldnames = list(produtos[0].keys())
    # O encoding 'utf-8-sig' ajuda o Excel a reconhecer caracteres especiais corretamente.
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # Ignora campos extras que possam ter sido adicionados/alterados
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(produtos)
        print(f"Exportação CSV concluída para: {filepath}")
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")

def import_produtos_from_csv(filepath):
    """Importa produtos de um arquivo CSV (apenas adiciona novos)."""
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo CSV não encontrado em {filepath}")
        return 0
        
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    # O encoding 'utf-8-sig' lê corretamente CSVs exportados pelo Excel no Brasil
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 1. Tenta converter campos para o tipo correto
                try:
                    nome = row.get('nome')
                    if not nome: continue 
                    
                    # Substitui vírgula por ponto para garantir que o float funcione
                    preco_str = str(row.get('preco', '0')).replace(',', '.')
                    preco = float(preco_str)
                    
                    quantidade = int(row.get('quantidade', 0))
                    vendido = int(row.get('vendido', 0))
                except ValueError as ve:
                    print(f"Aviso: Pulando linha com dados numéricos inválidos: {row}. Erro: {ve}")
                    continue 

                # 2. Insere um NOVO produto
                try:
                    cursor.execute(
                        """
                        INSERT INTO produtos (nome, preco, quantidade, marca, estilo, tipo, foto, data_validade, vendido, data_ultima_venda)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            nome, preco, quantidade, row.get('marca'), row.get('estilo'), 
                            row.get('tipo'), row.get('foto'), row.get('data_validade'), vendido, 
                            row.get('data_ultima_venda')
                        )
                    )
                    count += 1
                except Exception as e:
                    # Em caso de erro de DB, apenas registra e continua
                    print(f"Erro ao inserir linha para '{nome}': {e}")
                    
        conn.commit()
        print(f"Importação concluída. {count} produtos adicionados.")
        return count
    except Exception as e:
        print(f"Erro inesperado durante a importação: {e}")
        return 0
    finally:
        conn.close()


def generate_stock_pdf(filepath):
    """Gera um relatório PDF com a lista de produtos (usando reportlab)."""
    produtos = get_all_produtos()
    
    try:
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        y_position = height - 50
        
        # Título
        c.setFont('Helvetica-Bold', 16)
        c.drawString(cm, y_position, 'Relatório de Estoque - Produtos')
        y_position -= 20
        
        # Data de Geração
        c.setFont('Helvetica', 10)
        c.drawString(cm, y_position, f'Data de Geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        y_position -= 20
        
        # Se não houver produtos
        if not produtos:
            c.drawString(cm, y_position, 'Nenhum produto em estoque para gerar o relatório.')
            c.save()
            print(f"PDF de relatório vazio gerado em: {filepath}")
            return
            
        # Cabeçalho da tabela
        c.setFont('Helvetica-Bold', 10)
        col_x = [cm, cm*5, cm*10, cm*13, cm*15, cm*17.5] # Posições X das colunas
        c.drawString(col_x[0], y_position, 'Nome')
        c.drawString(col_x[1], y_position, 'Marca/Estilo')
        c.drawString(col_x[2], y_position, 'Tipo')
        c.drawString(col_x[3], y_position, 'Qtd')
        c.drawString(col_x[4], y_position, 'Preço')
        c.drawString(col_x[5], y_position, 'Validade')
        y_position -= 5
        c.line(cm, y_position, width - cm, y_position)
        y_position -= 15
        
        # Conteúdo da tabela
        c.setFont('Helvetica', 9)
        for p in produtos:
            if y_position < 40: # Quebra de página
                c.showPage() 
                y_position = height - 50
                # Repete o cabeçalho
                c.setFont('Helvetica-Bold', 10)
                c.drawString(col_x[0], y_position, 'Nome')
                c.drawString(col_x[1], y_position, 'Marca/Estilo')
                c.drawString(col_x[2], y_position, 'Tipo')
                c.drawString(col_x[3], y_position, 'Qtd')
                c.drawString(col_x[4], y_position, 'Preço')
                c.drawString(col_x[5], y_position, 'Validade')
                y_position -= 5
                c.line(cm, y_position, width - cm, y_position)
                y_position -= 15
                c.setFont('Helvetica', 9)

            # Formatação de Data de Validade
            validade = p.get('data_validade') or '-'
            if validade != '-':
                try:
                    # Converte ISO format para DD/MM/AAAA
                    validade = datetime.fromisoformat(validade).strftime('%d/%m/%Y')
                except ValueError:
                    pass
                    
            # Garante que os campos não sejam None
            nome = p.get('nome') or '-'
            marca = p.get('marca') or '-'
            estilo = p.get('estilo') or '-'
            tipo = p.get('tipo') or '-'
            quantidade = p.get('quantidade') or 0
            preco = p.get('preco') or 0.0

            # Desenha as linhas
            c.drawString(col_x[0], y_position, nome[:35]) 
            c.drawString(col_x[1], y_position, f"{marca}/{estilo}")
            c.drawString(col_x[2], y_position, tipo[:25])
            c.drawString(col_x[3], y_position, str(quantidade))
            c.drawString(col_x[4], y_position, f"R$ {float(preco):.2f}")
            c.drawString(col_x[5], y_position, validade)
            
            y_position -= 15
            
        c.save()
        print(f"Relatório PDF gerado e salvo em: {filepath}")
    except Exception as e:
        print(f"Erro ao gerar o PDF: Verifique se a biblioteca 'reportlab' está instalada. Erro: {e}")

# ====================================================================
# EXEMPLO DE USO (DEMONSTRAÇÃO)
# ====================================================================

if __name__ == '__main__':
    print("--- Inicialização do Sistema de Estoque ---")
    create_tables() # Garante que as tabelas e o admin existam

    # 1. Teste de Login
    admin_login = login_user("admin", "123")
    print(f"\nLogin Admin (admin/123): {'Sucesso' if admin_login else 'Falha'}")
    
    # 2. Adicionar Produtos
    add_produto("Hidratante Corporal Framboesa", 45.90, 10, "O Boticário", "Corpo e Banho", "Hidratante", None, datetime(2026, 12, 31).isoformat())
    add_produto("Colônia Myriad", 120.00, 5, "Eudora", "Perfumaria", "Perfumaria feminina", None, None)
    add_produto("Shampoo Liso Absoluto", 35.00, 20, "Natura", "Cabelo", "Shampoo", None, None)
    
    # 3. Listar Produtos
    print("\n--- Produtos em Estoque ---")
    estoque = get_all_produtos()
    for p in estoque:
        print(f"ID: {p['id']}, Nome: {p['nome']}, Qtd: {p['quantidade']}, Preço: R${p['preco']:.2f}, Marca: {p['marca']}")
        
    # 4. Registrar Venda
    # Assumindo que o Hidratante Corporal Framboesa é o primeiro produto (ID 1 na maioria dos casos)
    if estoque:
        mark_produto_as_sold(estoque[0]['id'], 2)
        
    # 5. Exportar Relatórios
    csv_path = os.path.join(ASSETS_DIR, "estoque_produtos.csv")
    pdf_path = os.path.join(ASSETS_DIR, "relatorio_estoque.pdf")
    export_produtos_to_csv(csv_path)
    generate_stock_pdf(pdf_path)
    
    # 6. Exemplo de Importação (Crie um CSV manualmente e teste)
    # import_produtos_from_csv(csv_path) 
    
    print("\n--- FIM DA DEMONSTRAÇÃO ---")
