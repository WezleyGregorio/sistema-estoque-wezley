import sqlite3
import csv
import io
import os
import sys
from flask import Flask, request, redirect, flash, get_flashed_messages, session, Response, render_template, url_for
from datetime import datetime

# --- CONFIGURAÇÃO DE PASTAS ---
if getattr(sys, 'frozen', False):
    pasta_base = os.path.dirname(sys.executable)
else:
    pasta_base = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(pasta_base, 'templates'),
            static_folder=os.path.join(pasta_base, 'static'))

app.secret_key = 'segredo_sistema_multi_lojas'

# --- BANCO DE DADOS ---
def conectar_banco():
    caminho_banco = os.path.join(pasta_base, 'estoque.db')
    return sqlite3.connect(caminho_banco)

def inicializar_banco():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    # 1. Tabela Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    
    # 2. Tabela Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_nome TEXT NOT NULL,
            valor REAL NOT NULL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. NOVA TABELA: USUÁRIOS (Logins das Lojas e Seu)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome_loja TEXT NOT NULL
        )
    ''')
    
    # --- CRIAÇÃO DOS USUÁRIOS PADRÃO (SE NÃO EXISTIREM) ---
    cursor.execute("SELECT count(*) FROM usuarios")
    qtd_users = cursor.fetchone()[0]
    
    if qtd_users == 0:
        print("Criando usuários padrão...")
        usuarios_iniciais = [
            # SEU LOGIN MESTRE (ADMIN)
            ('wezley', 'admin123', 'Sistema Admin Wezley'),
            # LOGIN DA LOJA LA PERSONA (CLIENTE)
            ('lapersona', 'guto123', 'La Persona Per Guto'),
            # EXEMPLO OUTRA LOJA
            ('congelata', 'marmita123', 'Congelata Gourmet')
        ]
        cursor.executemany("INSERT INTO usuarios (login, senha, nome_loja) VALUES (?, ?, ?)", usuarios_iniciais)
        conn.commit()

    conn.commit()
    conn.close()

# --- ROTA DE LOGIN (Agora verifica no Banco de Dados) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver logado, entra direto
    if session.get('usuario_logado'): return redirect('/')

    if request.method == 'POST':
        login_digitado = request.form['usuario'] # Pega o usuário digitado
        senha_digitada = request.form['senha']
        
        conn = conectar_banco()
        cursor = conn.cursor()
        
        # Procura no banco se existe esse par de Login + Senha
        cursor.execute("SELECT login, nome_loja FROM usuarios WHERE login = ? AND senha = ?", (login_digitado, senha_digitada))
        usuario_encontrado = cursor.fetchone()
        conn.close()
        
        if usuario_encontrado:
            # Login Sucesso!
            session['usuario_logado'] = True
            session['login_atual'] = usuario_encontrado[0]
            session['nome_loja'] = usuario_encontrado[1] # Salva o nome da loja na memória
            return redirect('/')
        else:
            # Login Errado
            flash('Login ou Senha incorretos!', 'erro')
            return redirect('/login')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- DASHBOARD (Adapta o nome da loja) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('usuario_logado'): return redirect('/login')

    conn = conectar_banco()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            preco = float(request.form['preco'])
            quantidade = int(request.form['quantidade'])
            cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome, preco, quantidade))
            conn.commit()
            flash(f'Produto cadastrado!', 'sucesso')
        except:
             flash('Erro nos dados.', 'erro')
        return redirect(url_for('index'))

    # Estatísticas
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(quantidade) FROM produtos")
    result = cursor.fetchone()[0]
    total_estoque = result if result else 0

    cursor.execute("SELECT SUM(valor), COUNT(*) FROM vendas")
    dados = cursor.fetchone()
    total_faturado = dados[0] if dados[0] else 0.0
    total_vendas = dados[1] if dados[1] else 0

    cursor.execute("SELECT id, produto_nome, data_hora, valor FROM vendas ORDER BY id DESC LIMIT 10")
    historico = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', 
                           nome_loja=session.get('nome_loja', 'Sistema'), # Envia o nome da loja pro HTML
                           total_produtos_cadastrados=total_produtos,
                           total_unidades_estoque=total_estoque,
                           total_faturado=total_faturado,
                           total_vendas_qtd=total_vendas,
                           historico=historico)

# --- OUTRAS ROTAS ---
@app.route('/estoque')
def estoque():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY id DESC")
    produtos = cursor.fetchall()
    conn.close()
    return render_template('estoque.html', produtos=produtos) # nome_loja já está na session

@app.route('/caixa')
def caixa():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE quantidade > 0 ORDER BY nome")
    produtos = cursor.fetchall()
    conn.close()
    return render_template('caixa.html', produtos=produtos)

# Rotas de Ação (Vender, Excluir, etc...)
@app.route('/vender_estoque/<int:id_produto>')
def vender_estoque(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, quantidade, preco FROM produtos WHERE id = ?", (id_produto,))
    prod = cursor.fetchone()
    if prod and prod[1] > 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE produtos SET quantidade = quantidade - 1 WHERE id = ?", (id_produto,))
        cursor.execute("INSERT INTO vendas (produto_nome, valor, data_hora) VALUES (?, ?, ?)", (prod[0], prod[2], now))
        conn.commit()
        flash(f'Venda de {prod[0]} realizada!', 'sucesso')
    else:
        flash('Erro: Sem estoque!', 'erro')
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/excluir/<int:id_produto>')
def excluir(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/limpar_caixa')
def limpar_caixa():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas")
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/baixar_relatorio')
def baixar_relatorio():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_hora, produto_nome, valor FROM vendas")
    rows = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Produto', 'Valor'])
    for r in rows: writer.writerow(r)
    output.seek(0)
    return Response('\ufeff' + output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=relatorio.csv"})

if __name__ == '__main__':
    inicializar_banco()
    if getattr(sys, 'frozen', False):
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)