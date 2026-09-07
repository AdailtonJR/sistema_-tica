import customtkinter as ctk
from tkinter import messagebox
from database import conectar


class ReceitasFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.criar_tabela()
        self.montar_tela()

    # ============================================================
    # BANCO - RECEITAS
    # ============================================================

    def criar_tabela(self):

        conn = conectar()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                data_receita TEXT,
                validade TEXT,

                od_esferico TEXT,
                od_cilindrico TEXT,
                od_eixo TEXT,
                od_adicao TEXT,

                oe_esferico TEXT,
                oe_cilindrico TEXT,
                oe_eixo TEXT,
                oe_adicao TEXT,

                dp TEXT,
                altura_od TEXT,
                altura_oe TEXT,

                tipo_lente TEXT,
                observacoes TEXT,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (cliente_id)
                    REFERENCES clientes(id)
            )
        """)

        conn.commit()
        conn.close()

    # ============================================================
    # TELA PRINCIPAL
    # ============================================================

    def montar_tela(self):

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------
        # TOPO
        # --------------------------------------------------------

        topo = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        topo.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=25,
            pady=(20, 10)
        )

        topo.grid_columnconfigure(
            1,
            weight=1
        )

        ctk.CTkLabel(
            topo,
            text="Receitas Ópticas",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.pesquisa = ctk.CTkEntry(
            topo,
            placeholder_text="Pesquisar cliente..."
        )

        self.pesquisa.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=20
        )

        self.pesquisa.bind(
            "<KeyRelease>",
            lambda evento: self.carregar_receitas()
        )

        ctk.CTkButton(
            topo,
            text="+ Nova receita",
            width=150,
            command=self.nova_receita
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        ctk.CTkButton(
            topo,
            text="Voltar",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=self.voltar
        ).grid(
            row=0,
            column=3,
            padx=5
        )

        # --------------------------------------------------------
        # ÁREA DA LISTA
        # --------------------------------------------------------

        area = ctk.CTkFrame(self)

        area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=25,
            pady=10
        )

        area.grid_rowconfigure(
            1,
            weight=1
        )

        area.grid_columnconfigure(
            0,
            weight=1
        )

        cabecalho = ctk.CTkFrame(area)

        cabecalho.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        cabecalho.grid_columnconfigure(0, weight=3)
        cabecalho.grid_columnconfigure(1, weight=1)
        cabecalho.grid_columnconfigure(2, weight=2)
        cabecalho.grid_columnconfigure(3, weight=2)
        cabecalho.grid_columnconfigure(4, weight=2)

        titulos = [
            "Cliente",
            "Data",
            "Tipo de lente",
            "OD",
            "OE"
        ]

        for i, titulo in enumerate(titulos):

            ctk.CTkLabel(
                cabecalho,
                text=titulo,
                font=ctk.CTkFont(
                    weight="bold"
                )
            ).grid(
                row=0,
                column=i,
                padx=10,
                pady=12,
                sticky="w"
            )

        self.lista = ctk.CTkScrollableFrame(
            area,
            fg_color="transparent"
        )

        self.lista.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.status = ctk.CTkLabel(
            self,
            text="",
            text_color="gray"
        )

        self.status.grid(
            row=2,
            column=0,
            sticky="w",
            padx=30,
            pady=(0, 15)
        )

        self.carregar_receitas()

    # ============================================================
    # CLIENTES
    # ============================================================

    def buscar_clientes(self):

        conn = conectar()

        clientes = conn.execute("""
            SELECT
                id,
                nome,
                cpf
            FROM clientes
            ORDER BY nome
        """).fetchall()

        conn.close()

        return clientes

    # ============================================================
    # CARREGAR RECEITAS
    # ============================================================

    def carregar_receitas(self):

        for widget in self.lista.winfo_children():
            widget.destroy()

        termo = self.pesquisa.get().strip().lower()

        conn = conectar()

        receitas = conn.execute("""
            SELECT
                r.*,
                c.nome AS cliente_nome
            FROM receitas r
            LEFT JOIN clientes c
                ON c.id = r.cliente_id
            ORDER BY r.id DESC
        """).fetchall()

        conn.close()

        quantidade = 0

        for receita in receitas:

            cliente = (
                receita["cliente_nome"]
                or "Cliente não encontrado"
            )

            if termo and termo not in cliente.lower():
                continue

            quantidade += 1

            linha = ctk.CTkFrame(
                self.lista
            )

            linha.pack(
                fill="x",
                pady=3
            )

            for coluna, peso in enumerate(
                [3, 1, 2, 2, 2, 2]
            ):

                linha.grid_columnconfigure(
                    coluna,
                    weight=peso
                )

            ctk.CTkLabel(
                linha,
                text=cliente,
                anchor="w"
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10,
                sticky="ew"
            )

            ctk.CTkLabel(
                linha,
                text=receita["data_receita"] or "-",
                anchor="w"
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10,
                sticky="ew"
            )

            ctk.CTkLabel(
                linha,
                text=receita["tipo_lente"] or "-",
                anchor="w"
            ).grid(
                row=0,
                column=2,
                padx=10,
                pady=10,
                sticky="ew"
            )

            ctk.CTkLabel(
                linha,
                text=self.resumo_grau(
                    receita["od_esferico"],
                    receita["od_cilindrico"],
                    receita["od_eixo"]
                ),
                anchor="w"
            ).grid(
                row=0,
                column=3,
                padx=10,
                pady=10,
                sticky="ew"
            )

            ctk.CTkLabel(
                linha,
                text=self.resumo_grau(
                    receita["oe_esferico"],
                    receita["oe_cilindrico"],
                    receita["oe_eixo"]
                ),
                anchor="w"
            ).grid(
                row=0,
                column=4,
                padx=10,
                pady=10,
                sticky="ew"
            )

            acoes = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )

            acoes.grid(
                row=0,
                column=5,
                padx=5
            )

            ctk.CTkButton(
                acoes,
                text="Editar",
                width=70,
                height=30,
                command=lambda rid=receita["id"]:
                    self.editar_receita(rid)
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                acoes,
                text="Excluir",
                width=70,
                height=30,
                fg_color="#b3261e",
                hover_color="#8f1d18",
                command=lambda rid=receita["id"]:
                    self.excluir_receita(rid)
            ).pack(
                side="left",
                padx=2
            )

        self.status.configure(
            text=f"{quantidade} receita(s) encontrada(s)."
        )

    # ============================================================
    # RESUMO GRAU
    # ============================================================

    @staticmethod
    def resumo_grau(
        esferico,
        cilindrico,
        eixo
    ):

        return (
            f"E: {esferico or '-'} | "
            f"C: {cilindrico or '-'} | "
            f"Eixo: {eixo or '-'}"
        )

    # ============================================================
    # NOVA RECEITA
    # ============================================================

    def nova_receita(self):

        self.abrir_formulario()

    # ============================================================
    # EDITAR RECEITA
    # ============================================================

    def editar_receita(
        self,
        receita_id
    ):

        self.abrir_formulario(
            receita_id
        )

    # ============================================================
    # FORMULÁRIO
    # ============================================================

    def abrir_formulario(
        self,
        receita_id=None
    ):

        janela = ctk.CTkToplevel(self)

        janela.title(
            "Nova receita"
            if receita_id is None
            else "Editar receita"
        )

        janela.geometry(
            "850x850"
        )

        janela.transient(
            self.winfo_toplevel()
        )

        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text=(
                "Nova Receita Óptica"
                if receita_id is None
                else "Editar Receita Óptica"
            ),
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        ).pack(
            pady=20
        )

        formulario = ctk.CTkScrollableFrame(
            janela
        )

        formulario.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=5
        )

        formulario.grid_columnconfigure(
            1,
            weight=1
        )

        # ========================================================
        # CLIENTE
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="Cliente *"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=8,
            sticky="w"
        )

        clientes = self.buscar_clientes()

        mapa_clientes = {}
        nomes_clientes = []

        for cliente in clientes:

            nome = cliente["nome"]

            cpf = cliente["cpf"] or ""

            texto = (
                f"{nome} - {cpf}"
                if cpf
                else nome
            )

            mapa_clientes[texto] = cliente["id"]

            nomes_clientes.append(
                texto
            )

        if not nomes_clientes:

            cliente_combo = ctk.CTkComboBox(
                formulario,
                values=[
                    "Nenhum cliente cadastrado"
                ]
            )

            cliente_combo.set(
                "Nenhum cliente cadastrado"
            )

        else:

            cliente_combo = ctk.CTkComboBox(
                formulario,
                values=nomes_clientes
            )

            cliente_combo.set(
                nomes_clientes[0]
            )

        cliente_combo.grid(
            row=0,
            column=1,
            padx=10,
            pady=8,
            sticky="ew"
        )

        # ========================================================
        # DATAS
        # ========================================================

        entradas = {}

        for linha, (texto, chave) in enumerate(
            [
                ("Data da receita", "data_receita"),
                ("Validade", "validade")
            ],
            start=1
        ):

            ctk.CTkLabel(
                formulario,
                text=texto
            ).grid(
                row=linha,
                column=0,
                padx=10,
                pady=8,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario,
                placeholder_text="DD/MM/AAAA"
            )

            entradas[chave].grid(
                row=linha,
                column=1,
                padx=10,
                pady=8,
                sticky="ew"
            )

        # ========================================================
        # OLHO DIREITO
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="OLHO DIREITO (OD)",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            padx=10,
            pady=(20, 10),
            sticky="w"
        )

        linha = 4

        for texto, chave in [
            ("Esférico", "od_esferico"),
            ("Cilíndrico", "od_cilindrico"),
            ("Eixo", "od_eixo"),
            ("Adição", "od_adicao")
        ]:

            ctk.CTkLabel(
                formulario,
                text=texto
            ).grid(
                row=linha,
                column=0,
                padx=10,
                pady=6,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario
            )

            entradas[chave].grid(
                row=linha,
                column=1,
                padx=10,
                pady=6,
                sticky="ew"
            )

            linha += 1

        # ========================================================
        # OLHO ESQUERDO
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="OLHO ESQUERDO (OE)",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        ).grid(
            row=8,
            column=0,
            columnspan=2,
            padx=10,
            pady=(20, 10),
            sticky="w"
        )

        linha = 9

        for texto, chave in [
            ("Esférico", "oe_esferico"),
            ("Cilíndrico", "oe_cilindrico"),
            ("Eixo", "oe_eixo"),
            ("Adição", "oe_adicao")
        ]:

            ctk.CTkLabel(
                formulario,
                text=texto
            ).grid(
                row=linha,
                column=0,
                padx=10,
                pady=6,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario
            )

            entradas[chave].grid(
                row=linha,
                column=1,
                padx=10,
                pady=6,
                sticky="ew"
            )

            linha += 1

        # ========================================================
        # MEDIDAS
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="MEDIDAS",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        ).grid(
            row=13,
            column=0,
            columnspan=2,
            padx=10,
            pady=(20, 10),
            sticky="w"
        )

        linha = 14

        for texto, chave in [
            ("DP", "dp"),
            ("Altura OD", "altura_od"),
            ("Altura OE", "altura_oe")
        ]:

            ctk.CTkLabel(
                formulario,
                text=texto
            ).grid(
                row=linha,
                column=0,
                padx=10,
                pady=6,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario
            )

            entradas[chave].grid(
                row=linha,
                column=1,
                padx=10,
                pady=6,
                sticky="ew"
            )

            linha += 1

        # ========================================================
        # TIPO DE LENTE
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="Tipo de lente"
        ).grid(
            row=17,
            column=0,
            padx=10,
            pady=8,
            sticky="w"
        )

        tipo_lente = ctk.CTkComboBox(
            formulario,
            values=[
                "Monofocal",
                "Bifocal",
                "Multifocal",
                "Ocupacional",
                "Lente de contato",
                "Outro"
            ]
        )

        tipo_lente.grid(
            row=17,
            column=1,
            padx=10,
            pady=8,
            sticky="ew"
        )

        tipo_lente.set(
            "Monofocal"
        )

        # ========================================================
        # OBSERVAÇÕES
        # ========================================================

        ctk.CTkLabel(
            formulario,
            text="Observações"
        ).grid(
            row=18,
            column=0,
            padx=10,
            pady=8,
            sticky="nw"
        )

        observacoes = ctk.CTkTextbox(
            formulario,
            height=120
        )

        observacoes.grid(
            row=18,
            column=1,
            padx=10,
            pady=8,
            sticky="ew"
        )

        # ========================================================
        # CARREGAR EDIÇÃO
        # ========================================================

        if receita_id is not None:

            conn = conectar()

            receita = conn.execute(
                """
                SELECT *
                FROM receitas
                WHERE id = ?
                """,
                (receita_id,)
            ).fetchone()

            conn.close()

            if receita:

                for texto, cliente_id in mapa_clientes.items():

                    if cliente_id == receita["cliente_id"]:

                        cliente_combo.set(
                            texto
                        )

                        break

                for chave in entradas:

                    valor = receita[chave]

                    if valor is not None:

                        entradas[chave].insert(
                            0,
                            str(valor)
                        )

                tipo_lente.set(
                    receita["tipo_lente"]
                    or "Monofocal"
                )

                if receita["observacoes"]:

                    observacoes.insert(
                        "1.0",
                        receita["observacoes"]
                    )

        # ========================================================
        # SALVAR
        # ========================================================

        def salvar():

            if not nomes_clientes:

                messagebox.showwarning(
                    "Receita",
                    "Não existe nenhum cliente cadastrado.",
                    parent=janela
                )

                return

            cliente_id = mapa_clientes.get(
                cliente_combo.get()
            )

            if not cliente_id:

                messagebox.showwarning(
                    "Receita",
                    "Selecione um cliente.",
                    parent=janela
                )

                return

            valores = {}

            for chave in entradas:

                valores[chave] = (
                    entradas[chave]
                    .get()
                    .strip()
                )

            valores["tipo_lente"] = (
                tipo_lente.get()
            )

            valores["observacoes"] = (
                observacoes
                .get(
                    "1.0",
                    "end"
                )
                .strip()
            )

            conn = None

            try:

                conn = conectar()

                if receita_id is None:

                    conn.execute(
                        """
                        INSERT INTO receitas (
                            cliente_id,
                            data_receita,
                            validade,

                            od_esferico,
                            od_cilindrico,
                            od_eixo,
                            od_adicao,

                            oe_esferico,
                            oe_cilindrico,
                            oe_eixo,
                            oe_adicao,

                            dp,
                            altura_od,
                            altura_oe,

                            tipo_lente,
                            observacoes
                        )

                        VALUES (
                            ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?
                        )
                        """,
                        (
                            cliente_id,
                            valores["data_receita"],
                            valores["validade"],

                            valores["od_esferico"],
                            valores["od_cilindrico"],
                            valores["od_eixo"],
                            valores["od_adicao"],

                            valores["oe_esferico"],
                            valores["oe_cilindrico"],
                            valores["oe_eixo"],
                            valores["oe_adicao"],

                            valores["dp"],
                            valores["altura_od"],
                            valores["altura_oe"],

                            valores["tipo_lente"],
                            valores["observacoes"]
                        )
                    )

                else:

                    conn.execute(
                        """
                        UPDATE receitas
                        SET
                            cliente_id = ?,
                            data_receita = ?,
                            validade = ?,

                            od_esferico = ?,
                            od_cilindrico = ?,
                            od_eixo = ?,
                            od_adicao = ?,

                            oe_esferico = ?,
                            oe_cilindrico = ?,
                            oe_eixo = ?,
                            oe_adicao = ?,

                            dp = ?,
                            altura_od = ?,
                            altura_oe = ?,

                            tipo_lente = ?,
                            observacoes = ?

                        WHERE id = ?
                        """,
                        (
                            cliente_id,
                            valores["data_receita"],
                            valores["validade"],

                            valores["od_esferico"],
                            valores["od_cilindrico"],
                            valores["od_eixo"],
                            valores["od_adicao"],

                            valores["oe_esferico"],
                            valores["oe_cilindrico"],
                            valores["oe_eixo"],
                            valores["oe_adicao"],

                            valores["dp"],
                            valores["altura_od"],
                            valores["altura_oe"],

                            valores["tipo_lente"],
                            valores["observacoes"],

                            receita_id
                        )
                    )

                conn.commit()
                conn.close()

                janela.destroy()

                self.carregar_receitas()

                messagebox.showinfo(
                    "Receita",
                    "Receita salva com sucesso!"
                )

            except Exception as erro:

                if conn:

                    try:
                        conn.rollback()
                        conn.close()
                    except:
                        pass

                messagebox.showerror(
                    "Erro ao salvar",
                    f"Não foi possível salvar a receita.\n\n"
                    f"Detalhes técnicos:\n{erro}",
                    parent=janela
                )

        # ========================================================
        # RODAPÉ
        # ========================================================

        rodape = ctk.CTkFrame(
            janela,
            fg_color="transparent"
        )

        rodape.pack(
            fill="x",
            padx=25,
            pady=15
        )

        ctk.CTkButton(
            rodape,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            command=janela.destroy
        ).pack(
            side="right",
            padx=5
        )

        ctk.CTkButton(
            rodape,
            text="Salvar receita",
            command=salvar
        ).pack(
            side="right",
            padx=5
        )

    # ============================================================
    # EXCLUIR
    # ============================================================

    def excluir_receita(
        self,
        receita_id
    ):

        confirmar = messagebox.askyesno(
            "Excluir receita",
            "Tem certeza que deseja excluir esta receita?"
        )

        if not confirmar:
            return

        try:

            conn = conectar()

            conn.execute(
                """
                DELETE FROM receitas
                WHERE id = ?
                """,
                (receita_id,)
            )

            conn.commit()
            conn.close()

            self.carregar_receitas()

            messagebox.showinfo(
                "Receita",
                "Receita excluída com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível excluir a receita:\n\n{erro}"
            )