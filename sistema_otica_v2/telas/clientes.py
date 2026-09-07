import customtkinter as ctk
from tkinter import messagebox
from database import conectar


class ClientesFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar

        self.montar_tela()

    # ============================================================
    # TELA PRINCIPAL
    # ============================================================

    def montar_tela(self):

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------
        # CABEÇALHO
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

        topo.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            topo,
            text="Clientes",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        )

        titulo.grid(
            row=0,
            column=0,
            sticky="w"
        )

        # --------------------------------------------------------
        # PESQUISA
        # --------------------------------------------------------

        self.campo_pesquisa = ctk.CTkEntry(
            topo,
            placeholder_text="Pesquisar por nome, CPF ou telefone..."
        )

        self.campo_pesquisa.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=20
        )

        self.campo_pesquisa.bind(
            "<KeyRelease>",
            lambda evento: self.carregar_clientes()
        )

        # --------------------------------------------------------
        # BOTÃO NOVO CLIENTE
        # --------------------------------------------------------

        botao_novo = ctk.CTkButton(
            topo,
            text="+ Novo cliente",
            width=150,
            command=self.novo_cliente
        )

        botao_novo.grid(
            row=0,
            column=2,
            padx=5
        )

        # --------------------------------------------------------
        # BOTÃO VOLTAR
        # --------------------------------------------------------

        botao_voltar = ctk.CTkButton(
            topo,
            text="Voltar",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=self.voltar
        )

        botao_voltar.grid(
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

        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------
        # CABEÇALHO DA LISTA
        # --------------------------------------------------------

        cabecalho = ctk.CTkFrame(
            area,
            height=45,
            corner_radius=0
        )

        cabecalho.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        cabecalho.grid_columnconfigure(0, weight=2)
        cabecalho.grid_columnconfigure(1, weight=1)
        cabecalho.grid_columnconfigure(2, weight=1)
        cabecalho.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            cabecalho,
            text="Nome",
            font=ctk.CTkFont(weight="bold")
        ).grid(
            row=0,
            column=0,
            padx=12,
            pady=12,
            sticky="w"
        )

        ctk.CTkLabel(
            cabecalho,
            text="CPF",
            font=ctk.CTkFont(weight="bold")
        ).grid(
            row=0,
            column=1,
            padx=12,
            pady=12,
            sticky="w"
        )

        ctk.CTkLabel(
            cabecalho,
            text="Telefone",
            font=ctk.CTkFont(weight="bold")
        ).grid(
            row=0,
            column=2,
            padx=12,
            pady=12,
            sticky="w"
        )

        ctk.CTkLabel(
            cabecalho,
            text="Ações",
            font=ctk.CTkFont(weight="bold")
        ).grid(
            row=0,
            column=3,
            padx=12,
            pady=12,
            sticky="w"
        )

        # --------------------------------------------------------
        # LISTA DE CLIENTES
        # --------------------------------------------------------

        self.lista_clientes = ctk.CTkScrollableFrame(
            area,
            fg_color="transparent"
        )

        self.lista_clientes.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

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

        self.carregar_clientes()

    # ============================================================
    # CARREGAR CLIENTES
    # ============================================================

    def carregar_clientes(self):

        for widget in self.lista_clientes.winfo_children():
            widget.destroy()

        termo = self.campo_pesquisa.get().strip()

        try:

            conn = conectar()

            clientes = conn.execute(
                """
                SELECT
                    id,
                    nome,
                    cpf,
                    telefone
                FROM clientes
                WHERE
                    nome LIKE ?
                    OR cpf LIKE ?
                    OR telefone LIKE ?
                ORDER BY nome COLLATE NOCASE
                """,
                (
                    f"%{termo}%",
                    f"%{termo}%",
                    f"%{termo}%"
                )
            ).fetchall()

            conn.close()

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível carregar os clientes.\n\n{erro}"
            )

            return

        # --------------------------------------------------------
        # MOSTRAR CLIENTES
        # --------------------------------------------------------

        for cliente in clientes:

            linha = ctk.CTkFrame(
                self.lista_clientes,
                fg_color=("gray92", "gray17")
            )

            linha.pack(
                fill="x",
                pady=3
            )

            linha.grid_columnconfigure(0, weight=2)
            linha.grid_columnconfigure(1, weight=1)
            linha.grid_columnconfigure(2, weight=1)
            linha.grid_columnconfigure(3, weight=1)

            # Nome

            ctk.CTkLabel(
                linha,
                text=cliente["nome"],
                anchor="w"
            ).grid(
                row=0,
                column=0,
                padx=12,
                pady=10,
                sticky="ew"
            )

            # CPF

            ctk.CTkLabel(
                linha,
                text=cliente["cpf"] or "-",
                anchor="w"
            ).grid(
                row=0,
                column=1,
                padx=12,
                pady=10,
                sticky="ew"
            )

            # Telefone

            ctk.CTkLabel(
                linha,
                text=cliente["telefone"] or "-",
                anchor="w"
            ).grid(
                row=0,
                column=2,
                padx=12,
                pady=10,
                sticky="ew"
            )

            # ----------------------------------------------------
            # AÇÕES
            # ----------------------------------------------------

            acoes = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )

            acoes.grid(
                row=0,
                column=3,
                padx=5,
                pady=5
            )

            ctk.CTkButton(
                acoes,
                text="Editar",
                width=65,
                height=30,
                command=lambda id_cliente=cliente["id"]:
                    self.editar_cliente(id_cliente)
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
                command=lambda id_cliente=cliente["id"]:
                    self.excluir_cliente(id_cliente)
            ).pack(
                side="left",
                padx=2
            )

        self.status.configure(
            text=f"{len(clientes)} cliente(s) encontrado(s)."
        )

    # ============================================================
    # NOVO CLIENTE
    # ============================================================

    def novo_cliente(self):

        self.abrir_formulario()

    # ============================================================
    # EDITAR CLIENTE
    # ============================================================

    def editar_cliente(self, cliente_id):

        self.abrir_formulario(cliente_id)

    # ============================================================
    # FORMULÁRIO
    # ============================================================

    def abrir_formulario(self, cliente_id=None):

        janela = ctk.CTkToplevel(self)

        janela.title(
            "Novo cliente"
            if cliente_id is None
            else "Editar cliente"
        )

        janela.geometry(
            "720x700"
        )

        janela.transient(
            self.winfo_toplevel()
        )

        janela.grab_set()

        # --------------------------------------------------------
        # TÍTULO
        # --------------------------------------------------------

        titulo = ctk.CTkLabel(
            janela,
            text=(
                "Novo cliente"
                if cliente_id is None
                else "Editar cliente"
            ),
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        )

        titulo.pack(
            pady=20
        )

        # --------------------------------------------------------
        # FORMULÁRIO
        # --------------------------------------------------------

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

        campos = [
            ("Nome completo *", "nome"),
            ("CPF", "cpf"),
            ("Data de nascimento", "nascimento"),
            ("Telefone", "telefone"),
            ("WhatsApp", "whatsapp"),
            ("E-mail", "email"),
            ("Endereço", "endereco"),
            ("Número", "numero"),
            ("Bairro", "bairro"),
            ("Cidade", "cidade"),
            ("Estado", "estado")
        ]

        entradas = {}

        for indice, (rotulo, chave) in enumerate(campos):

            ctk.CTkLabel(
                formulario,
                text=rotulo
            ).grid(
                row=indice,
                column=0,
                padx=10,
                pady=7,
                sticky="w"
            )

            entradas[chave] = ctk.CTkEntry(
                formulario,
                width=420
            )

            entradas[chave].grid(
                row=indice,
                column=1,
                padx=10,
                pady=7,
                sticky="ew"
            )

        # --------------------------------------------------------
        # OBSERVAÇÕES
        # --------------------------------------------------------

        linha_obs = len(campos)

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
        # CARREGAR DADOS PARA EDIÇÃO
        # --------------------------------------------------------

        if cliente_id is not None:

            try:

                conn = conectar()

                cliente = conn.execute(
                    """
                    SELECT *
                    FROM clientes
                    WHERE id = ?
                    """,
                    (cliente_id,)
                ).fetchone()

                conn.close()

                if cliente:

                    for _, chave in campos:

                        valor = cliente[chave]

                        if valor is not None:

                            entradas[chave].insert(
                                0,
                                str(valor)
                            )

                    if cliente["observacoes"]:

                        observacoes.insert(
                            "1.0",
                            cliente["observacoes"]
                        )

            except Exception as erro:

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível carregar o cliente.\n\n{erro}",
                    parent=janela
                )

                janela.destroy()

                return

        # --------------------------------------------------------
        # SALVAR
        # --------------------------------------------------------

        def salvar():

            nome = entradas["nome"].get().strip()

            if not nome:

                messagebox.showwarning(
                    "Cliente",
                    "O nome do cliente é obrigatório.",
                    parent=janela
                )

                return

            valores = {}

            for _, chave in campos:

                valores[chave] = (
                    entradas[chave]
                    .get()
                    .strip()
                )

            valores["observacoes"] = (
                observacoes
                .get("1.0", "end")
                .strip()
            )

            try:

                conn = conectar()

                if cliente_id is None:

                    conn.execute(
                        """
                        INSERT INTO clientes
                        (
                            nome,
                            cpf,
                            nascimento,
                            telefone,
                            whatsapp,
                            email,
                            endereco,
                            numero,
                            bairro,
                            cidade,
                            estado,
                            observacoes
                        )
                        VALUES
                        (
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            valores["nome"],
                            valores["cpf"],
                            valores["nascimento"],
                            valores["telefone"],
                            valores["whatsapp"],
                            valores["email"],
                            valores["endereco"],
                            valores["numero"],
                            valores["bairro"],
                            valores["cidade"],
                            valores["estado"],
                            valores["observacoes"]
                        )
                    )

                else:

                    conn.execute(
                        """
                        UPDATE clientes
                        SET
                            nome = ?,
                            cpf = ?,
                            nascimento = ?,
                            telefone = ?,
                            whatsapp = ?,
                            email = ?,
                            endereco = ?,
                            numero = ?,
                            bairro = ?,
                            cidade = ?,
                            estado = ?,
                            observacoes = ?
                        WHERE id = ?
                        """,
                        (
                            valores["nome"],
                            valores["cpf"],
                            valores["nascimento"],
                            valores["telefone"],
                            valores["whatsapp"],
                            valores["email"],
                            valores["endereco"],
                            valores["numero"],
                            valores["bairro"],
                            valores["cidade"],
                            valores["estado"],
                            valores["observacoes"],
                            cliente_id
                        )
                    )

                conn.commit()
                conn.close()

                janela.destroy()

                self.carregar_clientes()

                messagebox.showinfo(
                    "Cliente",
                    "Cliente salvo com sucesso!"
                )

            except Exception as erro:

                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível salvar o cliente.\n\n{erro}",
                    parent=janela
                )

        # --------------------------------------------------------
        # RODAPÉ
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
            text="Salvar cliente",
            command=salvar
        ).pack(
            side="right",
            padx=5
        )

    # ============================================================
    # EXCLUIR CLIENTE
    # ============================================================

    def excluir_cliente(self, cliente_id):

        try:

            conn = conectar()

            cliente = conn.execute(
                """
                SELECT nome
                FROM clientes
                WHERE id = ?
                """,
                (cliente_id,)
            ).fetchone()

            # Verifica se já existem vendas
            vendas = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM vendas
                WHERE cliente_id = ?
                """,
                (cliente_id,)
            ).fetchone()["total"]

            # Verifica se já existem receitas
            receitas = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM receitas
                WHERE cliente_id = ?
                """,
                (cliente_id,)
            ).fetchone()["total"]

            conn.close()

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível verificar o cliente.\n\n{erro}"
            )

            return

        if cliente is None:

            messagebox.showwarning(
                "Cliente",
                "Cliente não encontrado."
            )

            return

        # --------------------------------------------------------
        # NÃO PERMITIR EXCLUSÃO COM HISTÓRICO
        # --------------------------------------------------------

        if vendas > 0 or receitas > 0:

            messagebox.showwarning(
                "Exclusão bloqueada",
                "Este cliente possui histórico de vendas "
                "ou receitas e não pode ser excluído."
            )

            return

        confirmar = messagebox.askyesno(
            "Excluir cliente",
            f"Tem certeza que deseja excluir:\n\n"
            f"{cliente['nome']}?"
        )

        if not confirmar:
            return

        try:

            conn = conectar()

            conn.execute(
                """
                DELETE FROM clientes
                WHERE id = ?
                """,
                (cliente_id,)
            )

            conn.commit()
            conn.close()

            self.carregar_clientes()

            messagebox.showinfo(
                "Cliente",
                "Cliente excluído com sucesso."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível excluir o cliente.\n\n{erro}"
            )