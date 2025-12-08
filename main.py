import sqlite3
import csv
import io
from flask import Flask, request, redirect, flash, get_flashed_messages, session, Response
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_la_persona'
SENHA_SISTEMA = '1234'

def conectar_banco():
    return sqlite3.connect('estoque.db')

def inicializar_banco():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_nome TEXT NOT NULL,
            valor REAL NOT NULL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- ROTA: LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == SENHA_SISTEMA:
            session['usuario_logado'] = True
            return redirect('/')
        else:
            flash('Senha Incorreta!', 'erro')
            return redirect('/login')
            
    mensagens_html = ""
    mensagens = get_flashed_messages(with_categories=True)
    if mensagens:
        for categoria, msg in mensagens:
             mensagens_html += f'<div style="color: #ff0055; margin-bottom: 10px;">{msg}</div>'

    return f"""
    <body style="background:#0f0f13; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <div style="background:#1e1e24; padding:40px; border-radius:15px; border:1px solid #333; text-align:center; box-shadow: 0 0 20px rgba(0,210,255,0.2);">
            <h2 style="color:#00d2ff; margin-bottom:30px;">🔒 Acesso Restrito</h2>
            {mensagens_html}
            <form method="POST">
                <input type="password" name="senha" placeholder="Digite a Senha" style="padding:15px; width:200px; border-radius:5px; border:none; margin-bottom:20px; text-align:center;" required>
                <br><button type="submit" style="padding:10px 30px; background:#00d2ff; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">ENTRAR</button>
            </form>
        </div>
    </body>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- ROTAS PROTEGIDAS ---

# 1. NOVO: BAIXAR RELATÓRIO (EXCEL/CSV)
@app.route('/baixar_relatorio')
def baixar_relatorio():
    if not session.get('usuario_logado'): return redirect('/login')

    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_hora, produto_nome, valor FROM vendas")
    vendas = cursor.fetchall()
    conn.close()

    # Cria o arquivo na memória
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escreve o cabeçalho
    writer.writerow(['ID Venda', 'Data e Hora', 'Produto', 'Valor (R$)'])
    
    # Escreve os dados
    for venda in vendas:
        writer.writerow(venda)
    
    # Prepara o download (Adiciona BOM para o Excel abrir acentos corretamente)
    output.seek(0)
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=relatorio_vendas.csv"}
    )

@app.route('/vender/<int:id_produto>')
def vender(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, quantidade, preco FROM produtos WHERE id = ?", (id_produto,))
    produto = cursor.fetchone()
    
    if produto:
        nome, qtd, preco = produto
        if qtd > 0:
            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE produtos SET quantidade = quantidade - 1 WHERE id = ?", (id_produto,))
            cursor.execute("INSERT INTO vendas (produto_nome, valor, data_hora) VALUES (?, ?, ?)", (nome, preco, agora))
            conn.commit()
            flash(f'Venda de "{nome}" registrada!', 'sucesso')
        else:
            flash(f'Erro: "{nome}" esgotado!', 'erro')
    conn.close()
    return redirect('/')

@app.route('/excluir/<int:id_produto>')
def excluir(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/limpar_caixa')
def limpar_caixa():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas") 
    conn.commit()
    conn.close()
    flash('Caixa zerado!', 'aviso')
    return redirect('/')

@app.route('/editar/<int:id_produto>', methods=['GET', 'POST'])
def editar(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        quantidade = request.form['quantidade']
        cursor.execute("UPDATE produtos SET nome=?, preco=?, quantidade=? WHERE id=?", (nome, preco, quantidade, id_produto))
        conn.commit()
        conn.close()
        return redirect('/')

    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id_produto,))
    produto = cursor.fetchone()
    conn.close()

    return f"""
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding:50px;">
        <div style="background:#1e1e1e; padding:30px; border-radius:15px; border:1px solid #333; display:inline-block;">
            <h2 style="color:#00d2ff;">Editar</h2>
            <form method="POST">
                <input style="padding:10px; margin:5px; width:90%;" type="text" name="nome" value="{produto[1]}" required><br>
                <input style="padding:10px; margin:5px; width:90%;" type="number" step="0.01" name="preco" value="{produto[2]}" required><br>
                <input style="padding:10px; margin:5px; width:90%;" type="number" name="quantidade" value="{produto[3]}" required><br>
                <button style="padding:10px; width:95%; background:#00d2ff; border:none; font-weight:bold; cursor:pointer;" type="submit">Salvar</button>
            </form>
            <br><a href="/" style="color:#888;">Cancelar</a>
        </div>
    </body>
    """

# --- HOME ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('usuario_logado'): return redirect('/login')

    conn = conectar_banco()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        quantidade = request.form['quantidade']
        cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome, preco, quantidade))
        conn.commit()
        flash('Cadastrado!', 'sucesso')
        return redirect('/')

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("SELECT SUM(valor), COUNT(*) FROM vendas")
    dados = cursor.fetchone()
    total_faturado = dados[0] if dados[0] else 0.0
    total_vendas = dados[1] if dados[1] else 0

    cursor.execute("SELECT produto_nome, valor, data_hora FROM vendas ORDER BY id DESC LIMIT 10")
    historico = cursor.fetchall()
    conn.close()

    mensagens_html = ""
    mensagens = get_flashed_messages(with_categories=True)
    if mensagens:
        for categoria, msg in mensagens:
            cor = '#00ff88' if categoria == 'sucesso' else ('#ff0055' if categoria == 'erro' else '#ffcc00')
            mensagens_html += f'<div style="background:{cor}; color:black; padding:10px; margin-bottom:20px; border-radius:5px; text-align:center; font-weight:bold;">{msg}</div>'

    html = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Sistema Cyberpunk La Persona</title>
            <meta charset="UTF-8">
            <style>
                body {{ background-color: #0f0f13; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; margin: 0; padding-bottom: 50px; }}
                .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
                
                .dashboard {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .card-metric {{ flex: 1; background: #1e1e24; padding: 20px; border-radius: 12px; border-left: 4px solid #00d2ff; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }}
                .metric-value {{ font-size: 2.2em; font-weight: bold; color: white; margin-top: 5px; }}
                
                .card-form {{ background: #1a1a20; padding: 20px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #333; }}
                .input-group {{ display: flex; gap: 10px; }}
                input {{ background: #0f0f13; border: 1px solid #444; color: white; padding: 12px; border-radius: 6px; flex: 1; }}
                .btn-cad {{ background: #00d2ff; border: none; padding: 0 25px; border-radius: 6px; font-weight:bold; cursor:pointer; }}

                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th {{ text-align: left; color: #888; padding: 10px; border-bottom: 1px solid #333; }}
                td {{ padding: 10px; border-bottom: 1px solid #222; color: #ccc; }}
                .valor-venda {{ color: #00ff88; font-weight: bold; }}

                .btn {{ text-decoration: none; padding: 8px 12px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.9em; }}
                .btn-vender {{ background: linear-gradient(90deg, #00b09b, #96c93d); color: black; }}
                .btn-edit {{ background: #444; }}
                .btn-del {{ background: #ff0055; width: 30px; text-align: center; display: inline-block; }}
                
                .btn-reset {{ float:right; color:#ff0055; text-decoration:none; font-size:0.8em; border:1px solid #ff0055; padding:5px 10px; border-radius:5px; margin-left:10px; }}
                .btn-excel {{ float:right; color:#00ff88; text-decoration:none; font-size:0.8em; border:1px solid #00ff88; padding:5px 10px; border-radius:5px; }}
                
                .btn-logout {{ float:right; color:#888; text-decoration:none; margin-left:20px; border:1px solid #444; padding:5px 10px; border-radius:5px; }}
                .btn-logout:hover {{ background:#fff; color:#000; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/logout" class="btn-logout">🔒 Sair</a>
                <div style="clear:both; margin-bottom:20px;"></div>

                {mensagens_html}

                <div class="dashboard">
                    <div class="card-metric">
                        <span style="color:#888;">Faturamento Total</span>
                        <div class="metric-value" style="color:#00ff88;">R$ {total_faturado:.2f}</div>
                    </div>
                    <div class="card-metric">
                        <span style="color:#888;">Vendas Realizadas</span>
                        <div class="metric-value" style="color:#00d2ff;">{total_vendas}</div>
                    </div>
                </div>

                <div class="card-form">
                    <h3 style="margin-top:0; color:#00d2ff;">➕ Novo Produto</h3>
                    <form method="POST" class="input-group">
                        <input type="text" name="nome" placeholder="Nome" required>
                        <input type="number" step="0.01" name="preco" placeholder="Preço" required>
                        <input type="number" name="quantidade" placeholder="Qtd" style="max-width: 80px;" required>
                        <button class="btn-cad" type="submit">Adicionar</button>
                    </form>
                </div>

                <h3 style="color:#fff;">📦 Estoque Disponível</h3>
                <ul style="list-style:none; padding:0;">
    """
    
    for p in produtos:
        cor = "color:#ff0055" if p[3] == 0 else "color:#888"
        html += f"""
            <li style="background:#1e1e24; margin-bottom:10px; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="font-size:1.1em; display:block;">{p[1]}</strong>
                    <span style="{cor}">Estoque: {p[3]}</span> | <span>R$ {p[2]:.2f}</span>
                </div>
                <div>
                    <a href="/vender/{p[0]}" class="btn btn-vender">💲 VENDER</a>
                    <a href="/editar/{p[0]}" class="btn btn-edit">✏️</a>
                    <a href="/excluir/{p[0]}" class="btn btn-del" onclick="return confirm('Excluir?')">🗑️</a>
                </div>
            </li>
        """

    html += f"""
                </ul>
                <hr style="border-color:#333; margin: 40px 0;">

                <div>
                    <h3 style="color:#fff; display:inline-block;">📜 Extrato Recente</h3>
                    
                    <a href="/limpar_caixa" class="btn-reset" onclick="return confirm('ATENÇÃO: Isso apaga todas as vendas de hoje! Confirmar?')">🗑️ Zerar Caixa</a>
                    <a href="/baixar_relatorio" class="btn-excel">📥 Baixar Excel</a>
                    
                    <table>
                        <tr>
                            <th>Hora</th>
                            <th>Produto</th>
                            <th>Valor</th>
                        </tr>
    """
    
    for venda in historico:
        hora_formatada = venda[2].split(' ')[1][:5] if venda[2] else '--:--'
        html += f"""
            <tr>
                <td>{hora_formatada}</td>
                <td>{venda[0]}</td>
                <td class="valor-venda">+ R$ {venda[1]:.2f}</td>
            </tr>
        """
        
    html += """
                    </table>
                    <p style="text-align:center; color:#555; margin-top:20px; font-size:0.8em;">Versão 2.0 - Desenvolvido por Wezley</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html

if __name__ == '__main__':
    inicializar_banco()
    app.run(host='0.0.0.0', port=8000)