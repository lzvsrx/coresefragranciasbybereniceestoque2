import sqlite3
import os
import hashlib
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime, date

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

# Listas de categorias atualizadas (usadas nos seus códigos de exemplo)
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
    "Desodorantes", "Perfumaria infantil", "Perfumaria vegana", "Familia olfativa",
    "Clareador de manchas", "Anti-idade", "Protetor solar facial", "Rosto",
    "Tratamento para o rosto", "Acne", "Limpeza", "Esfoliante", "Tônico facial",
    "Kits de tratamento", "Tratamento para cabelos", "Shampoo", "Condicionador",
    "Leave-in e Creme para Pentear", "Finalizador", "Modelador", "Acessórios",
    "Kits e looks", "Boca", "Olhos", "Pincéis", "Paleta", "Unhas", "Sobrancelhas",
    "Kits de tratamento", "Hidratante", "Cuidados pós-banho", "Cuidados para o banho",
    "Barba", "Óleo corporal", "Cuidados íntimos", "Unissex", "Bronzeamento",
    "Protetor solar", "Depilação", "Mãos", "Lábios", "Pés", "Pós sol",
    "Protetor solar corporal", "Colônias", "Estojo", "Sabonetes",
    "Creme hidratante para as mãos", "Creme hidratante para os pés", "Miniseries",
    "Kits de perfumes", "Antissinais", "Máscara", "Creme bisnaga",
    "Roll On Fragranciado", "Roll On On Duty", "Sabonete líquido",
    "Sabonete em barra", "Shampoo 2 em 1", "Spray corporal", "Booster de Tratamento",
    "Creme para Pentear", "Óleo de Tratamento", "Pré-shampoo",
    "Sérum de Tratamento", "Shampoo e Condicionador",
    "Garrafas", "Armazenamentos", "Micro-ondas", "Servir", "Preparo",
    "Infantil", "Lazer/Outdoor", "Presentes", "Outro"
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
# FUNÇÕES CRUD DE PRODUTOS
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

def get_all_produtos():
    """Retorna todos os produtos, ordenados por nome."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ordem por nome para facilitar visualização, pode mudar para ID/mais recente se preferir
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

def delete_produto(product_id):
    """Remove um produto e sua foto associada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Recupera o produto para apagar a foto
    produto = get_produto_by_id(product_id)
    if produto and produto.get('foto'):
        try:
            os.remove(os.path.join(ASSETS_DIR, produto['foto']))
        except FileNotFoundError:
            pass # Ignora se a foto já não existir

    # 2. Deleta do banco de dados
    cursor.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def mark_produto_as_sold(product_id, quantity_sold=1):
    """Atualiza a quantidade e registra a última venda."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usa ISO format para facilitar a conversão de volta
    cursor.execute(
        "UPDATE produtos SET quantidade = quantidade - ?, vendido = 1, data_ultima_venda = ? WHERE id = ?",
        (quantity_sold, datetime.now().isoformat(), product_id)
    )
    conn.commit()
    conn.close()

# ====================================================================
# FUNÇÕES DE USUÁRIOS (LOGIN/ADMIN)
# ====================================================================

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
        # Usuário já existe (campo username é UNIQUE)
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
        return
        
    fieldnames = list(produtos[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(produtos)

def import_produtos_from_csv(filepath):
    """Importa produtos de um arquivo CSV (apenas adiciona novos)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Tenta converter campos para o tipo correto, usa None/0 se falhar
            try:
                # Garante que os campos cruciais não sejam nulos ou inválidos
                nome = row.get('nome')
                if not nome: continue 
                
                preco = float(row.get('preco', 0))
                quantidade = int(row.get('quantidade', 0))
                vendido = int(row.get('vendido', 0))
            except ValueError:
                # Pula a linha se os campos numéricos estiverem inválidos
                continue 

            # Insere um NOVO produto (ID será AUTOINCREMENT)
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
                print(f"Erro ao inserir linha: {e}")
                
    conn.commit()
    conn.close()
    return count


def generate_stock_pdf(filepath):
    """Gera um relatório PDF com a lista de produtos, listando por lote de validade."""
    # Garante que os lotes são carregados corretamente
    produtos = get_all_produtos() 
    
    # Cria uma lista plana de "linhas de relatório" (uma para cada lote)
    linhas_relatorio = []
    for p in produtos:
        lotes = p.get('lotes', [])
        # Se não houver lotes (produto sem validade), usa a quantidade total
        if not lotes and p.get('quantidade', 0) > 0:
             linhas_relatorio.append({
                'nome': p.get('nome'), 
                'marca': p.get('marca'), 
                'estilo': p.get('estilo'), 
                'tipo': p.get('tipo'), 
                'quantidade': p.get('quantidade'), 
                'preco': p.get('preco'), 
                'validade': 'Sem Validade',
                'data_adicao': p.get('data_adicao')
            })
        else:
            for lote in lotes:
                if lote.get('quantidade', 0) > 0:
                    linhas_relatorio.append({
                        'nome': p.get('nome'), 
                        'marca': p.get('marca'), 
                        'estilo': p.get('estilo'), 
                        'tipo': p.get('tipo'), 
                        'quantidade': lote.get('quantidade', 0), 
                        'preco': p.get('preco'), 
                        'validade': lote.get('validade'), # Formato ISO
                        'data_adicao': p.get('data_adicao')
                    })


    if not linhas_relatorio:
        # ... (código para arquivo vazio) ...
        c = canvas.Canvas(filepath, pagesize=A4)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(cm, A4[1] - 50, 'Relatório de Estoque - Vazio')
        c.drawString(cm, A4[1] - 70, 'Nenhum produto em estoque para gerar o relatório.')
        c.save()
        return

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    y_position = height - 50
    
    # Título e Data de Geração (permanecem)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(cm, y_position, 'Relatório de Estoque Detalhado por Lote')
    y_position -= 20
    
    c.setFont('Helvetica', 10)
    c.drawString(cm, y_position, f'Data de Geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    y_position -= 20
    
    # Cabeçalho da tabela - Adicionando Data de Adição
    c.setFont('Helvetica-Bold', 8)
    # Reajustando colunas para caber a Data de Adição
    col_x = [cm*0.5, cm*4.5, cm*8.5, cm*12.5, cm*14.5, cm*16.5, cm*19] 
    col_names = ['Nome', 'Marca/Estilo', 'Tipo', 'Preço', 'Qtd', 'Validade', 'Adição']
    
    for i, name in enumerate(col_names):
        c.drawString(col_x[i], y_position, name)
        
    y_position -= 5
    c.line(cm*0.5, y_position, width - cm*0.5, y_position) # Linha mais larga
    y_position -= 10
    
    # Conteúdo da tabela (Iterando sobre as linhas_relatorio)
    c.setFont('Helvetica', 8)
    for p in linhas_relatorio:
        if y_position < 30: # Nova página antes do final
            c.showPage() 
            y_position = height - 50
            # Repete o cabeçalho
            c.setFont('Helvetica-Bold', 8)
            for i, name in enumerate(col_names):
                c.drawString(col_x[i], y_position, name)
            y_position -= 5
            c.line(cm*0.5, y_position, width - cm*0.5, y_position)
            y_position -= 10
            c.setFont('Helvetica', 8)

        # Formatação de Datas
        validade = p.get('validade')
        validade_formatada = 'S/V'
        if validade and validade != 'Sem Validade':
            try:
                validade_formatada = datetime.fromisoformat(validade).strftime('%d/%m/%Y')
            except ValueError:
                validade_formatada = 'Inválida'
        
        data_adicao = p.get('data_adicao')
        adicao_formatada = ''
        if data_adicao:
             try:
                # Exibe apenas a data (ou data/hora reduzida)
                adicao_formatada = datetime.fromisoformat(data_adicao).strftime('%d/%m/%y')
             except ValueError:
                 adicao_formatada = 'Inválida'
                 
        # Garante que os campos não sejam None
        nome = p.get('nome', '-')
        marca = p.get('marca', '-')
        estilo = p.get('estilo', '-')
        tipo = p.get('tipo', '-')
        quantidade = p.get('quantidade', 0)
        preco = p.get('preco', 0.0)

        # Desenha as linhas
        c.drawString(col_x[0], y_position, nome[:25]) # Limita o tamanho do nome
        c.drawString(col_x[1], y_position, f"{marca[:10]}/{estilo[:10]}") # Limita o tamanho
        c.drawString(col_x[2], y_position, tipo[:15])
        c.drawString(col_x[3], y_position, f"R$ {float(preco):.2f}")
        c.drawString(col_x[4], y_position, str(quantidade))
        c.drawString(col_x[5], y_position, validade_formatada)
        c.drawString(col_x[6], y_position, adicao_formatada)
        
        y_position -= 10 # Reduz o espaçamento entre linhas
        
    c.save()
