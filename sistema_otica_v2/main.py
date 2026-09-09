import customtkinter as ctk
from database import inicializar_banco
from telas.login import LoginFrame
from backup import realizar_backup_sqlite

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class SistemaOtica(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema da Ótica - V2")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # 1. Inicializa o banco e as tabelas
        inicializar_banco()

        # 2. Executa o backup automático do banco na inicialização com aviso na tela
        realizar_backup_sqlite(db_path="sistema_otica.db", max_backups=10)

        # 3. Abre a tela de login
        self.mostrar_login()

    def limpar(self):
        for widget in self.winfo_children():
            widget.destroy()

    def mostrar_login(self):
        self.limpar()
        LoginFrame(self, self.abrir_dashboard).pack(fill="both", expand=True)

    def abrir_dashboard(self):
        from telas.dashboard import DashboardFrame
        self.limpar()
        DashboardFrame(self, self.mostrar_login).pack(fill="both", expand=True)

if __name__ == "__main__":
    app = SistemaOtica()
    app.mainloop()