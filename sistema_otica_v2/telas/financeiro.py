import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database import conectar


class FinanceiroFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.montar_tela()
        self.carregar_dados()

    # ==========================================================
    # TELA
    # ==========================================================

    def montar_tela(self):

        topo = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

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
            text="Financeiro",
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
            command=self.carregar_dados,
            width=110
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ctk.CTkButton(
            topo,
            text="Voltar",
            command=self.voltar,
            width=100
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        # ======================================================
        # FILTRO
        # ======================================================

        filtro = ctk.CTkFrame(self)

        filtro.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=25,
            pady=5
        )

        ctk.CTkLabel(
            filtro,
            text="Status:"
        ).pack(
            side="left",
            padx=(15, 5),
            pady=10
        )

        self.status_combo = ctk.CTkComboBox(
            filtro,
            values=[
                "Todos",
                "Pendente",
                "Pago",
                "Vencido"
            ],
            width=150,
            command=lambda _: self.carregar_dados()
        )

        self.status_combo.set("Todos")

        self.status_combo.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ======================================================
        # CARDS
        # ======================================================

        cards = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        cards.grid(
            row=1,
            column=0,
            sticky="e",
            padx=25,
            pady=5
        )

        self.card_pendente = self.criar_card(
            cards,
            "A Receber"
        )

        self.card_pago = self.criar_card(
            cards,
            "Recebido"
        )

        self.card_vencido = self.criar_card(
            cards,
            "Vencido"
        )

        # ======================================================
        # LISTA
        # ======================================================

        self.lista = ctk.CTkScrollableFrame(
            self
        )

        self.lista.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=25,
            pady=15
        )

    # ==========================================================
    # CARD
    # ==========================================================

    def criar_card(self, parent, titulo):

        frame = ctk.CTkFrame(
            parent,
            width=190,
            height=85,
            corner_radius=12
        )

        frame.pack(
            side="left",
            padx=5
        )

        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame,
            text=titulo,
            text_color="gray"
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 0)
        )

        valor = ctk.CTkLabel(
            frame,
            text="R$ 0,00",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        valor.pack(
            anchor="w",
            padx=15
        )

        return valor

    # ==========================================================
    # CARREGAR
    # ==========================================================

    def carregar_dados(self):

        for widget in self.lista.winfo_children():
            widget.destroy()

        conn = conectar()

        try:

            contas = conn.execute("""
                SELECT
                    cr.*,
                    c.nome AS cliente_nome
                FROM contas_receber cr
                LEFT JOIN clientes c
                    ON c.id = cr.cliente_id
                INNER JOIN vendas v
                    ON v.id = cr.venda_id
                WHERE v.status IS NULL OR v.status != 'Cancelada'
                ORDER BY cr.vencimento
            """).fetchall()

        except Exception as erro:

            conn.close()

            messagebox.showerror(
                "Financeiro",
                f"Erro ao carregar financeiro:\n\n{erro}"
            )

            return

        conn.close()

        hoje = datetime.now().strftime(
            "%Y-%m-%d"
        )

        total_pendente = 0
        total_pago = 0
        total_vencido = 0

        status_filtro = self.status_combo.get()

        for conta in contas:

            status = conta["status"] or "Pendente"

            vencimento = (
                conta["vencimento"] or ""
            )

            # Atualiza situação vencida
            if (
                status == "Pendente"
                and vencimento
                and vencimento < hoje
            ):
                status = "Vencido"

            valor = float(
                conta["valor"] or 0
            )

            if status == "Pago":

                total_pago += valor

            elif status == "Vencido":

                total_vencido += valor

            else:

                total_pendente += valor

            if status_filtro != "Todos":

                if status != status_filtro:
                    continue

            self.criar_linha(
                conta,
                status
            )

        self.card_pendente.configure(
            text=self.moeda(total_pendente)
        )

        self.card_pago.configure(
            text=self.moeda(total_pago)
        )

        self.card_vencido.configure(
            text=self.moeda(total_vencido)
        )

    # ==========================================================
    # LINHA
    # ==========================================================

    def criar_linha(self, conta, status):

        linha = ctk.CTkFrame(
            self.lista
        )

        linha.pack(
            fill="x",
            pady=4
        )

        for coluna in range(7):

            linha.grid_columnconfigure(
                coluna,
                weight=1
            )

        cliente = (
            conta["cliente_nome"]
            or "Cliente não informado"
        )

        parcela = (
            f"{conta['parcela']}/"
            f"{conta['total_parcelas']}"
        )

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
            text=f"Parcela {parcela}"
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
                command=lambda cid=conta["id"]:
                    self.receber(cid)
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

    # ==========================================================
    # RECEBER
    # ==========================================================

    def receber(self, conta_id):

        resposta = messagebox.askyesno(
            "Confirmar recebimento",
            "Deseja confirmar o recebimento desta parcela?"
        )

        if not resposta:
            return

        conn = conectar()

        try:

            conn.execute("""
                UPDATE contas_receber
                SET
                    status = 'Pago',
                    pago = 1,
                    pagamento = 'Recebido',
                    data_pagamento = ?
                WHERE id = ?
            """, (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                conta_id
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Financeiro",
                "Pagamento registrado com sucesso!"
            )

            self.carregar_dados()

        except Exception as erro:

            conn.rollback()
            conn.close()

            messagebox.showerror(
                "Financeiro",
                f"Não foi possível registrar:\n\n{erro}"
            )

    # ==========================================================
    # MOEDA
    # ==========================================================

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