import flet as ft
# Importamos a tela nova que criamos
from src.ui.estoque import TelaEstoque 

def TelaDashboard(page: ft.Page):
    
    def abrir_estoque(e):
        page.clean()
        page.add(TelaEstoque(page))
        page.update()

    return ft.Column(
        [
            ft.Text("PAINEL DE CONTROLE", size=30, color="#00f0ff", weight="bold"),
            ft.Divider(color="grey"),
            
            # Botão Grande de Ação
            ft.ElevatedButton(
                "📦 GERENCIAR ESTOQUE", 
                on_click=abrir_estoque,
                height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            
            ft.Divider(height=30, color="transparent"),
            
            ft.Row([
                ft.Container(
                    height=120, width=180, 
                    bgcolor="#1a1c24", border_radius=15, padding=15,
                    content=ft.Column([
                        ft.Icon(ft.Icons.ATTACH_MONEY, color="green"),
                        ft.Text("Vendas Hoje", color="white"),
                        ft.Text("R$ 0,00", size=20, weight="bold", color="white")
                    ])
                ),
            ])
        ]
    )