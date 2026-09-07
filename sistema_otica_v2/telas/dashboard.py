import customtkinter as ctk
from database import conectar


class DashboardFrame(ctk.CTkFrame):

    def __init__(self, master, sair):
        super().__init__(master)

        self.sair = sair

        self.montar()

    # ==========================================================
    # MONTAR DASHBOARD
    # ==========================================================

    def montar(self):

        self.grid_columnconfigure(
            1,
            weight=1
        )

        self.grid_rowconfigure(
            0,
            weight=1
        )

        # ======================================================
        # MENU LATERAL
        # ======================================================

        menu = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0
        )

        menu.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        menu.grid_propagate(False)

        ctk.CTkLabel(
            menu,
            text="ÓTICA V2",
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        ).pack(
            pady=(35, 35)
        )

        botoes = [

            ("🏠  Dashboard",
             self.dashboard),

            ("👤  Clientes",
             self.abrir_clientes),

            ("👓  Produtos",
             self.abrir_produtos),

            ("📋  Receitas",
             self.abrir_receitas),

            ("🛒  Vendas",
             self.abrir_vendas),

            ("💵  Caixa / Fechamento",
             self.abrir_caixa),

            ("🔧  Ordens de Serviço",
             self.abrir_ordens_servico),

            ("💰  Contas a Receber",
             self.abrir_contas_receber),

            ("📊  Relatórios",
             self.abrir_relatorios),

            ("💰  Financeiro",
             self.abrir_financeiro),

            ("🔐  Segurança",
             self.abrir_seguranca),
        ]

        for texto, comando in botoes:

            ctk.CTkButton(
                menu,
                text=texto,
                command=comando,
                height=42,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                anchor="w"
            ).pack(
                fill="x",
                padx=15,
                pady=4
            )

        # ======================================================
        # BOTÃO SAIR
        # ======================================================

        ctk.CTkButton(
            menu,
            text="Sair",
            command=self.sair,
            height=40,
            fg_color="#b3261e",
            hover_color="#8f1d18"
        ).pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=25
        )

        # ======================================================
        # CONTEÚDO
        # ======================================================

        self.conteudo = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.conteudo.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=25,
            pady=25
        )

        self.dashboard()

    # ==========================================================
    # LIMPAR CONTEÚDO
    # ==========================================================

    def limpar_conteudo(self):

        for widget in self.conteudo.winfo_children():
            widget.destroy()

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    def dashboard(self):

        self.limpar_conteudo()

        ctk.CTkLabel(
            self.conteudo,
            text="Dashboard",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        ).pack(
            anchor="w",
            pady=(0, 25)
        )

        conn = conectar()

        clientes = conn.execute(
            """
            SELECT COUNT(*) total
            FROM clientes
            """
        ).fetchone()["total"]

        produtos = conn.execute(
            """
            SELECT COUNT(*) total
            FROM produtos
            """
        ).fetchone()["total"]

        estoque = conn.execute(
            """
            SELECT COALESCE(
                SUM(estoque),
                0
            ) total
            FROM produtos
            """
        ).fetchone()["total"]

        faturamento = conn.execute(
            """
            SELECT COALESCE(
                SUM(total),
                0
            ) total
            FROM vendas
            WHERE status IS NULL OR status != 'Cancelada'
            """
        ).fetchone()["total"]

        # Contas a receber
        try:

            receber = conn.execute(
                """
                SELECT COALESCE(
                    SUM(valor),
                    0
                ) total
                FROM contas_receber
                WHERE status = 'Pendente'
                """
            ).fetchone()["total"]

        except:

            receber = 0

        conn.close()

        # ======================================================
        # CARDS
        # ======================================================

        linha = ctk.CTkFrame(
            self.conteudo,
            fg_color="transparent"
        )

        linha.pack(
            fill="x"
        )

        self.card(
            linha,
            "Clientes",
            clientes
        )

        self.card(
            linha,
            "Produtos",
            produtos
        )

        self.card(
            linha,
            "Itens em estoque",
            estoque
        )

        self.card(
            linha,
            "Faturamento",
            self.moeda(faturamento)
        )

        self.card(
            linha,
            "A receber",
            self.moeda(receber)
        )

        # ======================================================
        # INFORMAÇÃO
        # ======================================================

        info = ctk.CTkFrame(
            self.conteudo,
            corner_radius=15
        )

        info.pack(
            fill="both",
            expand=True,
            pady=25
        )

        ctk.CTkLabel(
            info,
            text="ÓTICA",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        ).pack(
            pady=(50, 10)
        )

        ctk.CTkLabel(
            info,
            text=(
                "Sistema de gestão para ótica.\n\n"
                "Clientes • Produtos • Receitas • "
                "Estoque • Vendas • Financeiro"
            ),
            text_color="gray",
            justify="center"
        ).pack()

    # ==========================================================
    # CARD
    # ==========================================================

    def card(
        self,
        parent,
        titulo,
        valor
    ):

        card = ctk.CTkFrame(
            parent,
            height=120,
            corner_radius=15
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=6
        )

        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=titulo,
            text_color="gray"
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4)
        )

        ctk.CTkLabel(
            card,
            text=str(valor),
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=18
        )

    # ==========================================================
    # CLIENTES
    # ==========================================================

    def abrir_clientes(self):

        from telas.clientes import ClientesFrame

        self.limpar_conteudo()

        ClientesFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # PRODUTOS
    # ==========================================================

    def abrir_produtos(self):

        from telas.produtos import ProdutosFrame

        self.limpar_conteudo()

        ProdutosFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # RECEITAS
    # ==========================================================

    def abrir_receitas(self):

        from telas.receitas import ReceitasFrame

        self.limpar_conteudo()

        ReceitasFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # VENDAS
    # ==========================================================

    def abrir_vendas(self):

        from telas.vendas import VendasFrame

        self.limpar_conteudo()

        VendasFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # CAIXA / FECHAMENTO
    # ==========================================================

    def abrir_caixa(self):

        from telas.caixa_frame import CaixaFrame

        self.limpar_conteudo()

        CaixaFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # CONTAS A RECEBER
    # ==========================================================

    def abrir_contas_receber(self):

        from telas.contas_receber import ContasReceberFrame

        self.limpar_conteudo()

        ContasReceberFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    def abrir_ordens_servico(self):

        from telas.ordens_servico import OrdensServicoFrame

        self.limpar_conteudo()

        OrdensServicoFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    def abrir_financeiro(self):

        from telas.financeiro import FinanceiroFrame

        self.limpar_conteudo()

        FinanceiroFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    # ==========================================================
    # AVISO
    # ==========================================================

    def aviso(self):

        from tkinter import messagebox

        messagebox.showinfo(
            "V2",
            "Este módulo será desenvolvido na próxima etapa."
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

    def abrir_seguranca(self):

        from telas.seguranca import SegurancaFrame

        self.limpar_conteudo()

        SegurancaFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )

    def abrir_relatorios(self):

        from telas.relatorios import RelatoriosFrame

        self.limpar_conteudo()

        RelatoriosFrame(
            self.conteudo,
            self.dashboard
        ).pack(
            fill="both",
            expand=True
        )