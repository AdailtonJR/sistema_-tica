import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database import conectar


class ContasReceberFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.montar_tela()
        self.carregar_contas()

    def montar_tela(self):

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=25,
            pady=20
        )

        topo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo,
            text="Contas a Receber",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ctk.CTkButton(
            topo,
            text="Atualizar",
            command=self.carregar_contas
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ctk.CTkButton(
            topo,
            text="Voltar",
            command=self.voltar
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        resumo = ctk.CTkFrame(self)
        resumo.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=25,
            pady=(0, 10)
        )

        self.total_pendente = ctk.CTkLabel(
            resumo,
            text="Pendente: R$ 0,00",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        self.total_pendente.pack(
            side="left",
            padx=20,
            pady=12
        )

        self.total_pago = ctk.CTkLabel(
            resumo,
            text="Recebido: R$ 0,00",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        )

        self.total_pago.pack(
            side="left",
            padx=20,
            pady=12
        )

        self.lista = ctk.CTkScrollableFrame(self)

        self.lista.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=25,
            pady=10
        )

    def carregar_contas(self):

        for widget in self.lista.winfo_children():
            widget.destroy()

        conn = conectar()

        try:

            # ======================================================
            # IMPORTANTE:
            # A conta só aparece se a venda NÃO estiver cancelada.
            # ======================================================

            contas = conn.execute("""
                SELECT
                    cr.*,
                    c.nome AS cliente_nome
                FROM contas_receber cr

                LEFT JOIN clientes c
                    ON c.id = cr.cliente_id

                INNER JOIN vendas v
                    ON v.id = cr.venda_id

                WHERE
                    v.status IS NULL
                    OR v.status != 'Cancelada'

                ORDER BY cr.id DESC
            """).fetchall()

        except Exception as erro:

            conn.close()

            messagebox.showerror(
                "Erro",
                f"Não foi possível carregar as contas.\n\n{erro}"
            )

            return

        conn.close()

        pendente = 0
        pago = 0

        for conta in contas:

            valor = float(conta["valor"] or 0)

            status = conta["status"] or "Pendente"

            if status == "Pago":
                pago += valor
            else:
                pendente += valor

            self.criar_linha(conta)

        self.total_pendente.configure(
            text=f"Pendente: {self.moeda(pendente)}"
        )

        self.total_pago.configure(
            text=f"Recebido: {self.moeda(pago)}"
        )

    def criar_linha(self, conta):

        linha = ctk.CTkFrame(self.lista)

        linha.pack(
            fill="x",
            pady=4
        )

        for coluna in range(7):
            linha.grid_columnconfigure(
                coluna,
                weight=1
            )

        cliente = conta["cliente_nome"] or "Cliente não informado"

        ctk.CTkLabel(
            linha,
            text=f"Venda #{conta['venda_id']}"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=10
        )

        ctk.CTkLabel(
            linha,
            text=cliente
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ctk.CTkLabel(
            linha,
            text=f"{conta['parcela']}/{conta['total_parcelas']}"
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        ctk.CTkLabel(
            linha,
            text=self.moeda(conta["valor"])
        ).grid(
            row=0,
            column=3,
            padx=5
        )

        ctk.CTkLabel(
            linha,
            text=conta["vencimento"] or "-"
        ).grid(
            row=0,
            column=4,
            padx=5
        )

        status = conta["status"] or "Pendente"

        ctk.CTkLabel(
            linha,
            text=status
        ).grid(
            row=0,
            column=5,
            padx=5
        )

        if status != "Pago":

            ctk.CTkButton(
                linha,
                text="Receber",
                width=90,
                command=lambda conta_id=conta["id"]:
                    self.receber(conta_id)
            ).grid(
                row=0,
                column=6,
                padx=5
            )

        else:

            ctk.CTkLabel(
                linha,
                text="✓ Pago"
            ).grid(
                row=0,
                column=6,
                padx=5
            )

    def receber(self, conta_id):

        resposta = messagebox.askyesno(
            "Confirmar",
            "Deseja confirmar o recebimento desta parcela?"
        )

        if not resposta:
            return

        conn = conectar()

        try:

            # Segurança adicional:
            # não permite receber uma parcela cuja venda foi cancelada.

            conta = conn.execute("""
                SELECT
                    cr.id,
                    v.status
                FROM contas_receber cr
                INNER JOIN vendas v
                    ON v.id = cr.venda_id
                WHERE cr.id = ?
            """, (conta_id,)).fetchone()

            if not conta:
                messagebox.showerror(
                    "Erro",
                    "Conta a receber não encontrada."
                )
                conn.close()
                return

            if conta["status"] == "Cancelada":
                messagebox.showwarning(
                    "Venda cancelada",
                    "Esta venda foi cancelada e não pode receber pagamento."
                )
                conn.close()
                self.carregar_contas()
                return

            conn.execute("""
                UPDATE contas_receber
                SET
                    status = 'Pago',
                    pagamento = 'Recebido',
                    data_pagamento = ?
                WHERE id = ?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                conta_id
            ))

            conn.commit()
            conn.close()

        except Exception as erro:

            conn.close()

            messagebox.showerror(
                "Erro",
                f"Não foi possível registrar o pagamento.\n\n{erro}"
            )
            return

        messagebox.showinfo(
            "Sucesso",
            "Pagamento registrado com sucesso!"
        )

        self.carregar_contas()

    @staticmethod
    def moeda(valor):

        try:
            valor = float(valor or 0)
        except:
            valor = 0

        return (
            f"R$ {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )