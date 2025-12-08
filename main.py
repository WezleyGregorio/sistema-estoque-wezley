import sqlite3
import csv
import io
# Importamos 'render_template' para usar os arquivos HTML
from flask import Flask, request, redirect, flash, get_flashed_messages, session, Response, render_template, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_la_persona_cyber' # Chave de segurança
SENHA_SISTEMA = '1234' # SUA SENHA

# --- Conexão com Banco ---
def conectar_banco():
    # No Windows local, o arquivo será criado na mesma pasta
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

# --- ROTAS DE ACESSO (Login/Logout) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver logado, manda pro dashboard
    if session.get('usuario_logado'): return redirect('/')

    if request.method == 'POST':
        senha = request.form['senha']
        if senha == SENHA_SISTEMA:
            session['usuario_logado'] = True
            return redirect('/')
        else:
            flash('Senha Incorreta! Acesso Negado.', 'erro')
            return redirect('/login')
            
    # Agora usamos o arquivo HTML separado!
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'aviso')
    return redirect('/login')

# --- ROTA PRINCIPAL: DASHBOARD ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('usuario_logado'): return redirect('/login')

    conn = conectar_banco()
    cursor = conn.cursor()

    # Se veio um cadastro do formulário rápido
    if request.method == 'POST':
        try:
            nome = request.form['nome']
            preco = float(request.form['preco'])
            quantidade = int(request.form['quantidade'])
            cursor.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)", (nome, preco, quantidade))
            conn.commit()
            flash(f'Produto "{nome}" cadastrado com sucesso!', 'sucesso')
        except:
             flash('Erro ao cadastrar. Verifique os dados.', 'erro')
        return redirect(url_for('index')) # Redireciona para limpar o form

    # Buscar dados para os Cards do Dashboard
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos_cadastrados = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantidade) FROM produtos")
    result_estoque = cursor.fetchone()[0]
    total_unidades_estoque = result_estoque if result_estoque else 0

    cursor.execute("SELECT SUM(valor), COUNT(*) FROM vendas")
    dados_vendas = cursor.fetchone()
    total_faturado = dados_vendas[0] if dados_vendas[0] else 0.0
    total_vendas_qtd = dados_vendas[1] if dados_vendas[1] else 0

    # Buscar histórico recente
    cursor.execute("SELECT id, produto_nome, data_hora, valor FROM vendas ORDER BY id DESC LIMIT 10")
    historico = cursor.fetchall()
    conn.close()

    # Renderiza o template do dashboard enviando todas essas variáveis
    return render_template('dashboard.html', 
                           total_produtos_cadastrados=total_produtos_cadastrados,
                           total_unidades_estoque=total_unidades_estoque,
                           total_faturado=total_faturado,
                           total_vendas_qtd=total_vendas_qtd,
                           historico=historico)

# --- ROTA: ESTOQUE (Lista Completa) ---
@app.route('/estoque')
def estoque():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY id DESC")
    produtos = cursor.fetchall()
    conn.close()
    return render_template('estoque.html', produtos=produtos)

# --- ROTA: CAIXA / PDV (Visual) ---
@app.route('/caixa')
def caixa():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    # Busca produtos para a lista lateral do caixa
    cursor.execute("SELECT * FROM produtos WHERE quantidade > 0 ORDER BY nome")
    produtos = cursor.fetchall()
    conn.close()
    return render_template('caixa.html', produtos=produtos)


# --- ROTAS DE AÇÃO (Vender, Excluir, Relatório) ---

# Rota especial para vender direto da tela de estoque (venda rápida de 1 item)
@app.route('/vender_estoque/<int:id_produto>')
def vender_estoque(id_produto):
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
            flash(f'Venda rápida de "{nome}" (R$ {preco:.2f}) realizada!', 'sucesso')
        else:
            flash(f'Erro: "{nome}" está esgotado!', 'erro')
    conn.close()
    # Retorna para a tela de onde veio (estoque)
    return redirect(url_for('estoque'))

@app.route('/excluir/<int:id_produto>')
def excluir(id_produto):
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conn.commit()
    conn.close()
    flash('Produto excluído do estoque.', 'aviso')
    return redirect(url_for('estoque'))

@app.route('/limpar_caixa')
def limpar_caixa():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas") 
    conn.commit()
    conn.close()
    flash('Histórico de vendas do dia foi zerado.', 'aviso')
    return redirect('/')

@app.route('/baixar_relatorio')
def baixar_relatorio():
    if not session.get('usuario_logado'): return redirect('/login')
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_hora, produto_nome, valor FROM vendas")
    vendas = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID Venda', 'Data e Hora', 'Produto', 'Valor (R$)'])
    for venda in vendas:
        writer.writerow(venda)
    output.seek(0)
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=relatorio_vendas_cyber.csv"}
    )

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    inicializar_banco()
    # No notebook local, rodamos com debug para ver erros se acontecerem
    print("--- SISTEMA CYBERPUNK INICIADO ---")
    print("Acesse no navegador: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)