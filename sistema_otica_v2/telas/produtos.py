import customtkinter as ctk
from tkinter import messagebox
from database import conectar


class ProdutosFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.criar_tabela()
        self.montar_tela()

    # ============================================================
    # BANCO DE DADOS
    # ============================================================

    def criar_tabela(self):

        conn = conectar()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                codigo TEXT,
                tipo TEXT DEFAULT 'Outro',
                marca TEXT,
                modelo TEXT,
                descricao TEXT,
                cor TEXT,
                tamanho TEXT,
                material TEXT,
                indice TEXT,
                tratamento TEXT,
                grau TEXT,
                fornecedor TEXT,
                custo REAL DEFAULT 0,
                preco REAL DEFAULT 0,
                estoque INTEGER DEFAULT 0,
                estoque_minimo INTEGER DEFAULT 1,
                observacoes TEXT
            )
        """)

        # Verifica as colunas existentes
        colunas = conn.execute(
            "PRAGMA table_info(produtos)"
        ).fetchall()

        existentes = {coluna["name"] for coluna in colunas}

        novas_colunas = {
            "nome": "TEXT DEFAULT 'Produto'",
            "codigo": "TEXT",
            "tipo": "TEXT DEFAULT 'Outro'",
            "marca": "TEXT",
            "modelo": "TEXT",
            "descricao": "TEXT",
            "cor": "TEXT",
            "tamanho": "TEXT",
            "material": "TEXT",
            "indice": "TEXT",
            "tratamento": "TEXT",
            "grau": "TEXT",
            "fornecedor": "TEXT",
            "custo": "REAL DEFAULT 0",
            "preco": "REAL DEFAULT 0",
            "estoque": "INTEGER DEFAULT 0",
            "estoque_minimo": "INTEGER DEFAULT 1",
            "observacoes": "TEXT"
        }

        for nome_coluna, tipo_coluna in novas_colunas.items():

            if nome_coluna not in existentes:

                conn.execute(
                    f"ALTER TABLE produtos ADD COLUMN "
                    f"{nome_coluna} {tipo_coluna}"
                )

        conn.commit()
        conn.close()

    # ============================================================
    # TELA
    # ============================================================

    def montar_tela(self):

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

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

        topo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            topo,
            text="Produtos e Estoque",
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
            placeholder_text="Pesquisar produto..."
        )

        self.pesquisa.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=20
        )

        self.pesquisa.bind(
            "<KeyRelease>",
            lambda evento: self.carregar_produtos()
        )

        ctk.CTkButton(
            topo,
            text="+ Novo produto",
            width=150,
            command=self.novo_produto
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
        # LISTA
        # --------------------------------------------------------

        area = ctk.CTkFrame(self)

        area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=25,
            pady=10
        )

        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(area)

        cabecalho.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        colunas = [
            ("Produto", 3),
            ("Tipo", 1),
            ("Preço", 1),
            ("Estoque", 1),
            ("Situação", 1),
            ("Ações", 2)
        ]

        for i, (texto, peso) in enumerate(colunas):

            cabecalho.grid_columnconfigure(
                i,
                weight=peso
            )

            ctk.CTkLabel(
                cabecalho,
                text=texto,
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

        self.carregar_produtos()

    # ============================================================
    # CARREGAR PRODUTOS
    # ============================================================

    def carregar_produtos(self):

        for widget in self.lista.winfo_children():
            widget.destroy()

        termo = self.pesquisa.get().strip()

        conn = conectar()

        produtos = conn.execute("""
            SELECT *
            FROM produtos
            WHERE
                nome LIKE ?
                OR codigo LIKE ?
                OR marca LIKE ?
                OR modelo LIKE ?
                OR descricao LIKE ?
            ORDER BY id DESC
        """, (
            f"%{termo}%",
            f"%{termo}%",
            f"%{termo}%",
            f"%{termo}%",
            f"%{termo}%"
        )).fetchall()

        conn.close()

        for produto in produtos:

            linha = ctk.CTkFrame(
                self.lista
            )

            linha.pack(
                fill="x",
                pady=3
            )

            for coluna, peso in enumerate(
                [3, 1, 1, 1, 1, 2]
            ):

                linha.grid_columnconfigure(
                    coluna,
                    weight=peso
                )

            # NOME

            nome = produto["nome"] or "Produto"

            ctk.CTkLabel(
                linha,
                text=nome,
                anchor="w"
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=10,
                sticky="ew"
            )

            # TIPO

            ctk.CTkLabel(
                linha,
                text=produto["tipo"] or "Outro",
                anchor="w"
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10,
                sticky="ew"
            )

            # PREÇO

            ctk.CTkLabel(
                linha,
                text=self.formatar_moeda(
                    produto["preco"]
                ),
                anchor="w"
            ).grid(
                row=0,
                column=2,
                padx=10,
                pady=10,
                sticky="ew"
            )

            # ESTOQUE

            estoque = produto["estoque"] or 0

            ctk.CTkLabel(
                linha,
                text=str(estoque),
                anchor="w"
            ).grid(
                row=0,
                column=3,
                padx=10,
                pady=10,
                sticky="ew"
            )

            # SITUAÇÃO

            minimo = produto["estoque_minimo"] or 1

            if estoque <= 0:
                situacao = "SEM ESTOQUE"

            elif estoque <= minimo:
                situacao = "ESTOQUE BAIXO"

            else:
                situacao = "NORMAL"

            ctk.CTkLabel(
                linha,
                text=situacao,
                anchor="w"
            ).grid(
                row=0,
                column=4,
                padx=10,
                pady=10,
                sticky="ew"
            )

            # BOTÕES

            acoes = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )

            acoes.grid(
                row=0,
                column=5,
                padx=5,
                pady=5
            )

            ctk.CTkButton(
                acoes,
                text="Editar",
                width=65,
                height=30,
                command=lambda id_produto=produto["id"]:
                    self.editar_produto(id_produto)
            ).pack(
                side="left",
                padx=2
            )

            ctk.CTkButton(
                acoes,
                text="Excluir",
                width=65,
                height=30,
                fg_color="#b3261e",
                hover_color="#8f1d18",
                command=lambda id_produto=produto["id"]:
                    self.excluir_produto(id_produto)
            ).pack(
                side="left",
                padx=2
            )

        self.status.configure(
            text=f"{len(produtos)} produto(s) encontrado(s)."
        )

    # ============================================================
    # NOVO PRODUTO
    # ============================================================

    def novo_produto(self):

        self.abrir_formulario()

    # ============================================================
    # EDITAR PRODUTO
    # ============================================================

    def editar_produto(self, produto_id):

        self.abrir_formulario(produto_id)

    # ============================================================
    # FORMULÁRIO
    # ============================================================

    def abrir_formulario(self, produto_id=None):

        janela = ctk.CTkToplevel(self)

        janela.title(
            "Novo produto"
            if produto_id is None
            else "Editar produto"
        )

        janela.geometry(
            "850x900"
        )

        janela.transient(
            self.winfo_toplevel()
        )

        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text=(
                "Novo produto"
                if produto_id is None
                else "Editar produto"
            ),
            font=ctk.CTkFont(
                size=25,
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

        # --------------------------------------------------------
        # NOME
        # --------------------------------------------------------

        ctk.CTkLabel(
            formulario,
            text="Nome do produto *"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=7,
            sticky="w"
        )

        entrada_nome = ctk.CTkEntry(
            formulario,
            placeholder_text="Ex.: Armação Ray-Ban RX001"
        )

        entrada_nome.grid(
            row=0,
            column=1,
            padx=10,
            pady=7,
            sticky="ew"
        )

        # --------------------------------------------------------
        # TIPO
        # --------------------------------------------------------

        ctk.CTkLabel(
            formulario,
            text="Tipo *"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=7,
            sticky="w"
        )

        tipo = ctk.CTkComboBox(
            formulario,
            values=[
                "Armação",
                "Lente",
                "Óculos de sol",
                "Acessório",
                "Outro"
            ]
        )

        tipo.grid(
            row=1,
            column=1,
            padx=10,
            pady=7,
            sticky="ew"
        )

        tipo.set("Armação")

        # --------------------------------------------------------
        # DEMAIS CAMPOS
        # --------------------------------------------------------

        campos = [
            ("Código", "codigo"),
            ("Marca", "marca"),
            ("Modelo", "modelo"),
            ("Descrição", "descricao"),
            ("Cor", "cor"),
            ("Tamanho", "tamanho"),
            ("Material", "material"),
            ("Índice", "indice"),
            ("Tratamento", "tratamento"),
            ("Grau", "grau"),
            ("Fornecedor", "fornecedor"),
            ("Custo", "custo"),
            ("Preço de venda", "preco"),
            ("Estoque", "estoque"),
            ("Estoque mínimo", "estoque_minimo")
        ]

        entradas = {}

        for numero, (rotulo, chave) in enumerate(
            campos,
            start=2
        ):

            ctk.CTkLabel(
                formulario,
                text=rotulo
            ).grid(
                row=numero,
                column=0,
                padx=10,
                pady=7,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario
            )

            entradas[chave].grid(
                row=numero,
                column=1,
                padx=10,
                pady=7,
                sticky="ew"
            )

        # --------------------------------------------------------
        # OBSERVAÇÕES
        # --------------------------------------------------------

        linha_obs = len(campos) + 2

        ctk.CTkLabel(
            formulario,
            text="Observações"
        ).grid(
            row=linha_obs,
            column=0,
            padx=10,
            pady=7,
            sticky="nw"
        )

        observacoes = ctk.CTkTextbox(
            formulario,
            height=100
        )

        observacoes.grid(
            row=linha_obs,
            column=1,
            padx=10,
            pady=7,
            sticky="ew"
        )

        # --------------------------------------------------------
        # CARREGAR EDIÇÃO
        # --------------------------------------------------------

        if produto_id is not None:

            conn = conectar()

            produto = conn.execute(
                """
                SELECT *
                FROM produtos
                WHERE id = ?
                """,
                (produto_id,)
            ).fetchone()

            conn.close()

            if produto:

                if produto["nome"]:
                    entrada_nome.insert(
                        0,
                        produto["nome"]
                    )

                tipo.set(
                    produto["tipo"] or "Outro"
                )

                for _, chave in campos:

                    valor = produto[chave]

                    if valor is not None:

                        entradas[chave].insert(
                            0,
                            str(valor)
                        )

                if produto["observacoes"]:

                    observacoes.insert(
                        "1.0",
                        produto["observacoes"]
                    )

        # --------------------------------------------------------
        # SALVAR
        # --------------------------------------------------------

        def salvar():

            nome = entrada_nome.get().strip()

            if not nome:

                messagebox.showwarning(
                    "Produto",
                    "Digite o nome do produto.",
                    parent=janela
                )

                entrada_nome.focus()

                return

            try:

                custo = float(
                    entradas["custo"].get()
                    .strip()
                    .replace(",", ".")
                    or 0
                )

                preco = float(
                    entradas["preco"].get()
                    .strip()
                    .replace(",", ".")
                    or 0
                )

                estoque = int(
                    entradas["estoque"].get()
                    .strip()
                    or 0
                )

                estoque_minimo = int(
                    entradas["estoque_minimo"].get()
                    .strip()
                    or 1
                )

            except ValueError:

                messagebox.showwarning(
                    "Produto",
                    "Custo, preço, estoque e estoque mínimo devem conter valores válidos.",
                    parent=janela
                )

                return

            valores = {}

            for _, chave in campos:

                if chave in (
                    "custo",
                    "preco",
                    "estoque",
                    "estoque_minimo"
                ):
                    continue

                valores[chave] = (
                    entradas[chave]
                    .get()
                    .strip()
                )

            valores["custo"] = custo
            valores["preco"] = preco
            valores["estoque"] = estoque
            valores["estoque_minimo"] = estoque_minimo

            valores["observacoes"] = (
                observacoes
                .get("1.0", "end")
                .strip()
            )

            conn = None

            try:

                conn = conectar()

                if produto_id is None:

                    conn.execute(
                        """
                        INSERT INTO produtos
                        (
                            nome,
                            codigo,
                            tipo,
                            marca,
                            modelo,
                            descricao,
                            cor,
                            tamanho,
                            material,
                            indice,
                            tratamento,
                            grau,
                            fornecedor,
                            custo,
                            preco,
                            estoque,
                            estoque_minimo,
                            observacoes
                        )
                        VALUES
                        (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?
                        )
                        """,
                        (
                            nome,
                            valores["codigo"],
                            tipo.get(),
                            valores["marca"],
                            valores["modelo"],
                            valores["descricao"],
                            valores["cor"],
                            valores["tamanho"],
                            valores["material"],
                            valores["indice"],
                            valores["tratamento"],
                            valores["grau"],
                            valores["fornecedor"],
                            valores["custo"],
                            valores["preco"],
                            valores["estoque"],
                            valores["estoque_minimo"],
                            valores["observacoes"]
                        )
                    )

                else:

                    conn.execute(
                        """
                        UPDATE produtos
                        SET
                            nome = ?,
                            codigo = ?,
                            tipo = ?,
                            marca = ?,
                            modelo = ?,
                            descricao = ?,
                            cor = ?,
                            tamanho = ?,
                            material = ?,
                            indice = ?,
                            tratamento = ?,
                            grau = ?,
                            fornecedor = ?,
                            custo = ?,
                            preco = ?,
                            estoque = ?,
                            estoque_minimo = ?,
                            observacoes = ?
                        WHERE id = ?
                        """,
                        (
                            nome,
                            valores["codigo"],
                            tipo.get(),
                            valores["marca"],
                            valores["modelo"],
                            valores["descricao"],
                            valores["cor"],
                            valores["tamanho"],
                            valores["material"],
                            valores["indice"],
                            valores["tratamento"],
                            valores["grau"],
                            valores["fornecedor"],
                            valores["custo"],
                            valores["preco"],
                            valores["estoque"],
                            valores["estoque_minimo"],
                            valores["observacoes"],
                            produto_id
                        )
                    )

                conn.commit()
                conn.close()

                janela.destroy()

                self.carregar_produtos()

                messagebox.showinfo(
                    "Produto",
                    "Produto salvo com sucesso!"
                )

            except Exception as erro:

                if conn:

                    try:
                        conn.rollback()
                        conn.close()
                    except:
                        pass

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível salvar o produto:\n\n{erro}",
                    parent=janela
                )

        # --------------------------------------------------------
        # BOTÕES
        # --------------------------------------------------------

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
            text="Salvar produto",
            command=salvar
        ).pack(
            side="right",
            padx=5
        )

    # ============================================================
    # EXCLUIR
    # ============================================================

    def excluir_produto(self, produto_id):

        conn = conectar()

        produto = conn.execute(
            """
            SELECT nome
            FROM produtos
            WHERE id = ?
            """,
            (produto_id,)
        ).fetchone()

        conn.close()

        if not produto:

            messagebox.showwarning(
                "Produto",
                "Produto não encontrado."
            )

            return

        confirmar = messagebox.askyesno(
            "Excluir produto",
            f"Tem certeza que deseja excluir:\n\n"
            f"{produto['nome']}?"
        )

        if not confirmar:
            return

        try:

            conn = conectar()

            conn.execute(
                """
                DELETE FROM produtos
                WHERE id = ?
                """,
                (produto_id,)
            )

            conn.commit()
            conn.close()

            self.carregar_produtos()

            messagebox.showinfo(
                "Produto",
                "Produto excluído com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível excluir o produto:\n\n{erro}"
            )

    # ============================================================
    # FORMATAÇÃO DE MOEDA
    # ============================================================

    @staticmethod
    def formatar_moeda(valor):

        try:

            valor = float(valor or 0)

            return (
                f"R$ {valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        except:

            return "R$ 0,00"