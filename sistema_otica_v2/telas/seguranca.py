import customtkinter as ctk
from tkinter import messagebox
from database import conectar


class SegurancaFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)
        self.voltar = voltar
        self.garantir_tabela_usuarios()
        self.montar_tela()

    def garantir_tabela_usuarios(self):
        """Cria a tabela de usuários se não existir e insere o supervisor padrão."""
        conn = conectar()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    ativo INTEGER DEFAULT 1
                )
            """)
            
            # Insere o supervisor padrão caso não exista
            cursor = conn.execute("SELECT id FROM usuarios WHERE usuario = ?", ("supervisor",))
            if not cursor.fetchone():
                conn.execute(
                    "INSERT INTO usuarios (usuario, senha, ativo) VALUES (?, ?, 1)",
                    ("supervisor", "1234")
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erro ao inicializar tabela de usuários: {e}")
        finally:
            conn.close()

    def montar_tela(self):
        ctk.CTkLabel(
            self,
            text="Segurança",
            font=ctk.CTkFont(size=30, weight="bold")
        ).pack(anchor="w", padx=30, pady=(30, 25))

        painel = ctk.CTkFrame(self, width=500)
        painel.pack(padx=30, pady=10, anchor="nw")

        ctk.CTkLabel(
            painel,
            text="Alterar senha do Supervisor",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(padx=30, pady=(25, 20))

        ctk.CTkLabel(painel, text="Senha atual").pack(anchor="w", padx=30)
        self.senha_atual = ctk.CTkEntry(painel, show="*", width=400)
        self.senha_atual.pack(padx=30, pady=(5, 15))

        ctk.CTkLabel(painel, text="Nova senha").pack(anchor="w", padx=30)
        self.nova_senha = ctk.CTkEntry(painel, show="*", width=400)
        self.nova_senha.pack(padx=30, pady=(5, 15))

        ctk.CTkLabel(painel, text="Confirmar nova senha").pack(anchor="w", padx=30)
        self.confirmar_senha = ctk.CTkEntry(painel, show="*", width=400)
        self.confirmar_senha.pack(padx=30, pady=(5, 20))

        ctk.CTkButton(
            painel,
            text="Alterar senha",
            height=42,
            command=self.alterar_senha
        ).pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(
            painel,
            text="Voltar",
            height=38,
            fg_color="transparent",
            border_width=1,
            command=self.voltar
        ).pack(fill="x", padx=30, pady=(0, 25))

    def alterar_senha(self):
        atual = self.senha_atual.get().strip()
        nova = self.nova_senha.get().strip()
        confirmacao = self.confirmar_senha.get().strip()

        if not atual or not nova or not confirmacao:
            messagebox.showwarning("Segurança", "Preencha todos os campos.")
            return

        if nova != confirmacao:
            messagebox.showwarning("Segurança", "A nova senha e a confirmação são diferentes.")
            return

        if len(nova) < 4:
            messagebox.showwarning("Segurança", "A nova senha deve ter pelo menos 4 caracteres.")
            return

        conn = conectar()
        try:
            supervisor = conn.execute(
                """
                SELECT id
                FROM usuarios
                WHERE usuario = ?
                  AND senha = ?
                  AND ativo = 1
                """,
                ("supervisor", atual)
            ).fetchone()

            if not supervisor:
                conn.close()
                messagebox.showerror("Segurança", "A senha atual está incorreta.")
                return

            conn.execute(
                """
                UPDATE usuarios
                SET senha = ?
                WHERE usuario = ?
                """,
                (nova, "supervisor")
            )

            conn.commit()
            conn.close()

            self.senha_atual.delete(0, "end")
            self.nova_senha.delete(0, "end")
            self.confirmar_senha.delete(0, "end")

            messagebox.showinfo("Segurança", "Senha do Supervisor alterada com sucesso!")

        except Exception as erro:
            try:
                conn.close()
            except:
                pass

            messagebox.showerror("Segurança", f"Não foi possível alterar a senha:\n\n{erro}")