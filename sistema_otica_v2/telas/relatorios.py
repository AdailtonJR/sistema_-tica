import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from database import conectar


class RelatoriosFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.montar_tela()
        self.carregar_relatorio()

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
            text="Relatórios",
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
            text="Voltar",
            width=100,
            command=self.voltar
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        # ======================================================
        # FILTROS
        # ======================================================

        filtros = ctk.CTkFrame(self)

        filtros.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=25,
            pady=5
        )

        ctk.CTkLabel(
            filtros,
            text="Período:"
        ).pack(
            side="left",
            padx=(15, 5),
            pady=10
        )

        self.periodo = ctk.CTkComboBox(
            filtros,
            values=[
                "Hoje",
                "Últimos 7 dias",
                "Últimos 30 dias",
                "Todo o período"
            ],
            width=180
        )

        self.periodo.set("Últimos 30 dias")

        self.periodo.pack(
            side="left",
            padx=5
        )

        ctk.CTkButton(
            filtros,
            text="Gerar relatório",
            width=140,
            command=self.carregar_relatorio
        ).pack(
            side="left",
            padx=10
        )

        # ======================================================
        # ÁREA DO RELATÓRIO
        # ======================================================

        self.area = ctk.CTkScrollableFrame(
            self
        )

        self.area.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=25,
            pady=15
        )

    # ==========================================================
    # RELATÓRIO
    # ==========================================================

    def carregar_relatorio(self):

        for widget in self.area.winfo_children():
            widget.destroy()

        inicio = self.obter_data_inicio()

        conn = conectar()

        try:

            vendas = conn.execute(
                """
                SELECT
                    id,
                    data,
                    total,
                    forma_pagamento,
                    status
                FROM vendas
                WHERE date(data) >= date(?)
                ORDER BY id DESC
                """,
                (inicio,)
            ).fetchall()

            produtos = conn.execute(
                """
                SELECT
                    p.nome,
                    SUM(vi.quantidade) AS quantidade,
                    SUM(vi.subtotal) AS total
                FROM vendas_itens vi
                JOIN vendas v
                    ON v.id = vi.venda_id
                JOIN produtos p
                    ON p.id = vi.produto_id
                WHERE date(v.data) >= date(?)
                  AND (
                      v.status IS NULL
                      OR v.status != 'Cancelada'
                  )
                GROUP BY p.id, p.nome
                ORDER BY quantidade DESC
                LIMIT 10
                """,
                (inicio,)
            ).fetchall()

            formas = conn.execute(
                """
                SELECT
                    forma_pagamento,
                    COUNT(*) AS quantidade,
                    COALESCE(SUM(total),0) AS total
                FROM vendas
                WHERE date(data) >= date(?)
                  AND (
                      status IS NULL
                      OR status != 'Cancelada'
                  )
                GROUP BY forma_pagamento
                ORDER BY total DESC
                """,
                (inicio,)
            ).fetchall()

            conn.close()

        except Exception as erro:

            conn.close()

            messagebox.showerror(
                "Relatórios",
                f"Erro ao gerar relatório:\n\n{erro}"
            )

            return

        # ======================================================
        # TOTAIS
        # ======================================================

        faturamento = 0
        vendas_validas = 0
        vendas_canceladas = 0

        for venda in vendas:

            status = venda["status"] or "Concluída"

            if status == "Cancelada":

                vendas_canceladas += 1

            else:

                vendas_validas += 1
                faturamento += float(
                    venda["total"] or 0
                )

        # ======================================================
        # CABEÇALHO
        # ======================================================

        ctk.CTkLabel(
            self.area,
            text="Resumo do período",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        ).pack(
            anchor="w",
            pady=(5, 15)
        )

        resumo = ctk.CTkFrame(
            self.area,
            fg_color="transparent"
        )

        resumo.pack(
            fill="x"
        )

        self.criar_card(
            resumo,
            "Faturamento",
            self.moeda(faturamento)
        )

        self.criar_card(
            resumo,
            "Vendas realizadas",
            vendas_validas
        )

        self.criar_card(
            resumo,
            "Vendas canceladas",
            vendas_canceladas
        )

        # ======================================================
        # FORMAS DE PAGAMENTO
        # ======================================================

        ctk.CTkLabel(
            self.area,
            text="Vendas por forma de pagamento",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            pady=(30, 10)
        )

        for forma in formas:

            frame = ctk.CTkFrame(
                self.area
            )

            frame.pack(
                fill="x",
                pady=3
            )

            texto = (
                f"{forma['forma_pagamento'] or 'Não informado'}"
                f"    |    "
                f"{forma['quantidade']} venda(s)"
                f"    |    "
                f"{self.moeda(forma['total'])}"
            )

            ctk.CTkLabel(
                frame,
                text=texto
            ).pack(
                anchor="w",
                padx=15,
                pady=10
            )

        # ======================================================
        # PRODUTOS MAIS VENDIDOS
        # ======================================================

        ctk.CTkLabel(
            self.area,
            text="Produtos mais vendidos",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            pady=(30, 10)
        )

        for produto in produtos:

            frame = ctk.CTkFrame(
                self.area
            )

            frame.pack(
                fill="x",
                pady=3
            )

            texto = (
                f"{produto['nome']}"
                f"    |    "
                f"{produto['quantidade']} unidade(s)"
                f"    |    "
                f"{self.moeda(produto['total'])}"
            )

            ctk.CTkLabel(
                frame,
                text=texto
            ).pack(
                anchor="w",
                padx=15,
                pady=10
            )

        # ======================================================
        # VENDAS RECENTES
        # ======================================================

        ctk.CTkLabel(
            self.area,
            text="Vendas recentes",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        ).pack(
            anchor="w",
            pady=(30, 10)
        )

        for venda in vendas[:20]:

            status = venda["status"] or "Concluída"

            texto = (
                f"Venda #{venda['id']}"
                f"    |    "
                f"{venda['data'] or '-'}"
                f"    |    "
                f"{self.moeda(venda['total'])}"
                f"    |    "
                f"{venda['forma_pagamento'] or '-'}"
                f"    |    "
                f"{status}"
            )

            frame = ctk.CTkFrame(
                self.area
            )

            frame.pack(
                fill="x",
                pady=3
            )

            ctk.CTkLabel(
                frame,
                text=texto
            ).pack(
                anchor="w",
                padx=15,
                pady=10
            )

    # ==========================================================
    # CARD
    # ==========================================================

    def criar_card(self, parent, titulo, valor):

        card = ctk.CTkFrame(
            parent,
            width=220,
            height=90,
            corner_radius=12
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=titulo,
            text_color="gray"
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 2)
        )

        ctk.CTkLabel(
            card,
            text=str(valor),
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=15
        )

    # ==========================================================
    # DATA INICIAL
    # ==========================================================

    def obter_data_inicio(self):

        hoje = datetime.now()

        periodo = self.periodo.get()

        if periodo == "Hoje":

            data = hoje

        elif periodo == "Últimos 7 dias":

            data = hoje - timedelta(days=7)

        elif periodo == "Últimos 30 dias":

            data = hoje - timedelta(days=30)

        else:

            data = datetime(
                2000,
                1,
                1
            )

        return data.strftime(
            "%Y-%m-%d"
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