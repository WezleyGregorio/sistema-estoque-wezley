import flet as ft
from database.dados import adicionar_produto, listar_produtos

def TelaEstoque(page: ft.Page):
    # Campos de Cadastro
    txt_codigo = ft.TextField(label="Código (SKU)", width=100)
    txt_nome = ft.TextField(label="Modelo do Sapato", width=200)
    txt_marca = ft.TextField(label="Marca", width=150, value="La Persona")
    txt_tam = ft.TextField(label="Tam.", width=70)
    txt_preco = ft.TextField(label="Preço Venda", width=100, prefix_text="R$ ")
    txt_qtd = ft.TextField(label="Qtd", width=70)

    # Tabela de Dados (DataTablet)
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Código")),
            ft.DataColumn(ft.Text("Modelo")),
            ft.DataColumn(ft.Text("Marca")),
            ft.DataColumn(ft.Text("Tam.")),
            ft.DataColumn(ft.Text("Preço")),
            ft.DataColumn(ft.Text("Estoque")),
        ],
        rows=[]
    )

    def carregar_dados():
        tabela.rows.clear()
        produtos = listar_produtos()
        for p in produtos:
            # p[0]=id, p[1]=codigo, p[2]=nome...
            tabela.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p[1])), # Código
                    ft.DataCell(ft.Text(p[2])), # Nome
                    ft.DataCell(ft.Text(p[3])), # Marca
                    ft.DataCell(ft.Text(p[4])), # Tamanho
                    ft.DataCell(ft.Text(f"R$ {p[6]}")), # Preço Venda
                    ft.DataCell(ft.Text(str(p[7]))), # Estoque
                ])
            )
        page.update()

    def salvar(e):
        try:
            adicionar_produto(
                txt_codigo.value, txt_nome.value, txt_marca.value, 
                txt_tam.value, 0.0, float(txt_preco.value), int(txt_qtd.value)
            )
            ft.SnackBar(ft.Text("Produto Salvo!"), bgcolor="green").open = True
            carregar_dados() # Atualiza a tabela
            page.update()
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Erro ao salvar! Verifique os números."), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    btn_salvar = ft.ElevatedButton("CADASTRAR PRODUTO", on_click=salvar, bgcolor="#00f0ff", color="black")

    # Carrega dados ao abrir
    carregar_dados()

    return ft.Column(
        [
            ft.Text("GESTÃO DE ESTOQUE", size=25, weight="bold", color="#00f0ff"),
            ft.Container(
                content=ft.Row([txt_codigo, txt_nome, txt_marca, txt_tam, txt_preco, txt_qtd], wrap=True),
                padding=10, bgcolor="#1a1c24", border_radius=10
            ),
            btn_salvar,
            ft.Divider(),
            ft.Text("Lista de Produtos:", size=15, color="grey"),
            ft.Container(content=tabela, bgcolor="#111", border_radius=10, padding=10)
        ],
        scroll="adaptive"
    )