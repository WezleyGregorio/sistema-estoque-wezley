import sqlite3
import os

# Define o caminho do banco de dados
CAMINHO_DB = "database/loja.db"

def inicializar_banco():
    """Cria a tabela de produtos se ela não existir"""
    # Garante que a pasta existe
    os.makedirs("database", exist_ok=True)
    
    conn = sqlite3.connect(CAMINHO_DB)
    cursor = conn.cursor()
    
    # Criando a Tabela de Produtos (Sapatos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nome TEXT NOT NULL,
        marca TEXT,
        tamanho TEXT,
        preco_custo REAL,
        preco_venda REAL,
        estoque INTEGER
    )
    """)
    
    # Criando Tabela de Usuários (Para login real depois)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("Banco de dados atualizado com sucesso!")

def adicionar_produto(codigo, nome, marca, tamanho, p_custo, p_venda, estoque):
    conn = sqlite3.connect(CAMINHO_DB)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO produtos (codigo, nome, marca, tamanho, preco_custo, preco_venda, estoque)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (codigo, nome, marca, tamanho, p_custo, p_venda, estoque))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = sqlite3.connect(CAMINHO_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    itens = cursor.fetchall()
    conn.close()
    return itens

# Inicializa assim que o arquivo é importado
inicializar_banco()