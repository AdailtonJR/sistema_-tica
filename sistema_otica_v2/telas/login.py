import customtkinter as ctk
from tkinter import messagebox
from database import conectar

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, sucesso_login):
        super().__init__(master, fg_color="transparent")
        self.sucesso_login = sucesso_login

        card = ctk.CTkFrame(self, width=420, height=430, corner_radius=18)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, text="SISTEMA DA ÓTICA",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(55, 8))

        ctk.CTkLabel(
            card, text="V2 • Controle completo da ótica",
            text_color="gray"
        ).pack(pady=(0, 30))

        self.usuario = ctk.CTkEntry(card, width=300, height=42, placeholder_text="Usuário")
        self.usuario.pack(pady=10)

        self.senha = ctk.CTkEntry(card, width=300, height=42, placeholder_text="Senha", show="*")
        self.senha.pack(pady=10)
        self.senha.bind("<Return>", lambda e: self.entrar())

        ctk.CTkButton(
            card, text="ENTRAR", width=300, height=45,
            command=self.entrar
        ).pack(pady=25)

        ctk.CTkLabel(
            card, text="Acesso inicial: admin / 1234",
            text_color="gray"
        ).pack()

        self.usuario.focus()

    def entrar(self):
        usuario = self.usuario.get().strip()
        senha = self.senha.get()

        conn = conectar()
        row = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND senha=? AND ativo=1",
            (usuario, senha)
        ).fetchone()
        conn.close()

        if row:
            self.sucesso_login()
        else:
            messagebox.showerror("Login", "Usuário ou senha inválidos.")
