import flet as ft

def TelaLogin(page: ft.Page, on_login_success):
    COR_NEON = "#00f0ff"
    
    user = ft.TextField(label="USUÁRIO", border_color=COR_NEON, color="white", width=280)
    senha = ft.TextField(label="SENHA", password=True, can_reveal_password=True, border_color=COR_NEON, color="white", width=280)

    def tentar_login(e):
        if user.value == "admin" and senha.value == "1234":
            on_login_success() 
        else:
            page.snack_bar = ft.SnackBar(ft.Text("ACESSO NEGADO"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    btn_entrar = ft.ElevatedButton(
        "ACESSAR SISTEMA", 
        width=280, height=45,
        color="white", bgcolor="#7000ff",
        on_click=tentar_login
    )

    return ft.Container(
        content=ft.Column(
            [
                # A CORREÇÃO ESTÁ AQUI EMBAIXO: ft.Icons (com I maiúsculo)
                ft.Icon(ft.Icons.SHIELD_MOON, size=60, color=COR_NEON),
                ft.Text("LA PERSONA", size=30, weight="bold", color="white"),
                ft.Divider(color="transparent", height=20),
                user, senha, 
                ft.Divider(color="transparent", height=10),
                btn_entrar
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        alignment=ft.alignment.center,
        padding=40,
        bgcolor="#111",
        border_radius=20,
        border=ft.border.all(1, COR_NEON)
    )