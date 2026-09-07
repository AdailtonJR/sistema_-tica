import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from database import conectar


class VendasFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)

        self.voltar = voltar
        self.carrinho = []

        self.criar_tabelas()
        self.montar_tela()

    # ==========================================================
    # BANCO DE DADOS
    # ==========================================================

    def criar_tabelas(self):
        conn = conectar()

        colunas_vendas = [
            row["name"] for row in conn.execute("PRAGMA table_info(vendas)").fetchall()
        ]

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                data TEXT DEFAULT CURRENT_TIMESTAMP,
                subtotal REAL DEFAULT 0,
                desconto REAL DEFAULT 0,
                total REAL DEFAULT 0,
                entrada REAL DEFAULT 0,
                forma_pagamento TEXT,
                observacoes TEXT,
                parcelas INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Concluída',
                cancelada_em TEXT,
                cancelada_por TEXT
            )
        """)

        if "status" not in colunas_vendas and colunas_vendas:
            conn.execute("ALTER TABLE vendas ADD COLUMN status TEXT DEFAULT 'Concluída'")

        if "cancelada_em" not in colunas_vendas and colunas_vendas:
            conn.execute("ALTER TABLE vendas ADD COLUMN cancelada_em TEXT")

        if "cancelada_por" not in colunas_vendas and colunas_vendas:
            conn.execute("ALTER TABLE vendas ADD COLUMN cancelada_por TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                subtotal REAL NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contas_receber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                cliente_id INTEGER,
                parcela INTEGER,
                total_parcelas INTEGER,
                valor REAL,
                vencimento TEXT,
                pagamento TEXT,
                data_pagamento TEXT,
                status TEXT DEFAULT 'Pendente',
                observacoes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def buscar_clientes(self):
        conn = conectar()
        clientes = conn.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome ASC").fetchall()
        conn.close()
        return clientes

    def buscar_produtos(self):
        conn = conectar()
        produtos = conn.execute("SELECT id, nome, preco, estoque FROM produtos ORDER BY nome ASC").fetchall()
        conn.close()
        return produtos

    def moeda(self, valor):
        valor = valor or 0.0
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ==========================================================
    # TELA PRINCIPAL
    # ==========================================================

    def montar_tela(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        topo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            topo, text="Vendas", font=ctk.CTkFont(size=30, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            topo, text="Nova venda", command=self.nova_venda, width=130
        ).grid(row=0, column=2, padx=5)

        ctk.CTkButton(
            topo, text="Voltar", command=self.voltar, width=100, fg_color="transparent", border_width=1
        ).grid(row=0, column=3, padx=5)

        conteudo = ctk.CTkFrame(self)
        conteudo.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        conteudo.grid_columnconfigure(0, weight=1)
        conteudo.grid_rowconfigure(1, weight=1)

        self.pesquisa = ctk.CTkEntry(conteudo, placeholder_text="Pesquisar venda por cliente...")
        self.pesquisa.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.pesquisa.bind("<KeyRelease>", lambda evento: self.carregar_vendas())

        self.lista = ctk.CTkScrollableFrame(conteudo)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.carregar_vendas()

    # ==========================================================
    # LISTAR VENDAS
    # ==========================================================

    def carregar_vendas(self):
        for widget in self.lista.winfo_children():
            widget.destroy()

        termo = self.pesquisa.get().strip().lower()
        conn = conectar()

        vendas = conn.execute("""
            SELECT
                v.*,
                c.nome AS cliente_nome
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            ORDER BY v.id DESC
        """).fetchall()

        conn.close()

        for venda in vendas:
            cliente = venda["cliente_nome"] or "Venda sem cliente"

            if termo and termo not in cliente.lower():
                continue

            linha = ctk.CTkFrame(self.lista)
            linha.pack(fill="x", pady=4)

            for coluna in range(6):
                linha.grid_columnconfigure(coluna, weight=1)

            ctk.CTkLabel(
                linha, text=f"Venda #{venda['id']}", font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

            ctk.CTkLabel(linha, text=cliente).grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(linha, text=venda["data"] or "-").grid(row=0, column=2, padx=10, pady=10, sticky="w")

            parcelas = venda["parcelas"] or 1
            pagamento = venda["forma_pagamento"] or "-"
            if pagamento == "Cartão de crédito" and parcelas > 1:
                pagamento = f"Crédito {parcelas}x"

            ctk.CTkLabel(linha, text=pagamento).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(linha, text=self.moeda(venda["total"])).grid(row=0, column=4, padx=10, pady=10, sticky="w")

            status = venda["status"] or "Concluída"
            ctk.CTkLabel(linha, text=status).grid(row=0, column=5, padx=10, pady=10, sticky="w")

            ctk.CTkButton(
                linha, text="Ver", width=70, command=lambda vid=venda["id"]: self.ver_venda(vid)
            ).grid(row=1, column=4, padx=10, pady=5)

            if status != "Cancelada":
                ctk.CTkButton(
                    linha, text="Cancelar", width=90, fg_color="#b3261e", hover_color="#8f1d18",
                    command=lambda vid=venda["id"]: self.solicitar_cancelamento(vid)
                ).grid(row=1, column=5, padx=10, pady=5)

    # ==========================================================
    # NOVA VENDA
    # ==========================================================

    def nova_venda(self):
        self.carrinho = []

        janela = ctk.CTkToplevel(self)
        janela.title("Nova Venda")
        janela.geometry("1000x780")
        janela.transient(self.winfo_toplevel())
        janela.grab_set()

        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            janela, text="Nova Venda", font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, padx=25, pady=20, sticky="w")

        clientes = self.buscar_clientes()
        mapa_clientes = {}
        nomes_clientes = []

        for cliente in clientes:
            nome = cliente["nome"]
            cpf = cliente["cpf"] or ""
            texto = f"{nome} - {cpf}" if cpf else nome
            mapa_clientes[texto] = cliente["id"]
            nomes_clientes.append(texto)

        cliente_frame = ctk.CTkFrame(janela)
        cliente_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=5)
        cliente_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cliente_frame, text="Cliente:").grid(row=0, column=0, padx=10, pady=10)

        if nomes_clientes:
            cliente_combo = ctk.CTkComboBox(cliente_frame, values=nomes_clientes)
            cliente_combo.set(nomes_clientes[0])
        else:
            cliente_combo = ctk.CTkComboBox(cliente_frame, values=["Nenhum cliente cadastrado"])
            cliente_combo.set("Nenhum cliente cadastrado")

        cliente_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        area = ctk.CTkFrame(janela)
        area.grid(row=2, column=0, sticky="nsew", padx=25, pady=10)
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(2, weight=1)

        produto_frame = ctk.CTkFrame(area)
        produto_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        produto_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(produto_frame, text="Produto:").grid(row=0, column=0, padx=10, pady=10)

        produtos = self.buscar_produtos()
        mapa_produtos = {}
        nomes_produtos = []

        for produto in produtos:
            preco = float(produto["preco"] or 0)
            estoque = int(produto["estoque"] or 0)
            texto = f"{produto['nome']} | R$ {preco:.2f} | Estoque: {estoque}"
            mapa_produtos[texto] = produto
            nomes_produtos.append(texto)

        if nomes_produtos:
            produto_combo = ctk.CTkComboBox(produto_frame, values=nomes_produtos)
            produto_combo.set(nomes_produtos[0])
        else:
            produto_combo = ctk.CTkComboBox(produto_frame, values=["Nenhum produto cadastrado"])
            produto_combo.set("Nenhum produto cadastrado")

        produto_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        quantidade = ctk.CTkEntry(produto_frame, width=90, placeholder_text="Qtd.")
        quantidade.grid(row=0, column=2, padx=10, pady=10)
        quantidade.insert(0, "1")

        lista_carrinho = ctk.CTkScrollableFrame(area)
        lista_carrinho.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        resumo = ctk.CTkFrame(area)
        resumo.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        resumo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(resumo, text="Desconto:").grid(row=0, column=0, padx=10, pady=8)
        desconto_entry = ctk.CTkEntry(resumo, width=120)
        desconto_entry.grid(row=0, column=1, sticky="w", padx=10, pady=8)
        desconto_entry.insert(0, "0")

        ctk.CTkLabel(resumo, text="Forma de pagamento:").grid(row=1, column=0, padx=10, pady=8)
        pagamento = ctk.CTkComboBox(
            resumo,
            values=["Dinheiro", "Pix", "Cartão de débito", "Cartão de crédito", "Boleto", "Outro"],
            width=220
        )
        pagamento.grid(row=1, column=1, sticky="w", padx=10, pady=8)
        pagamento.set("Pix")

        ctk.CTkLabel(resumo, text="Parcelamento:").grid(row=2, column=0, padx=10, pady=8)
        parcelas_combo = ctk.CTkComboBox(
            resumo,
            values=[f"{i}x" for i in range(1, 13)],
            width=120
        )
        parcelas_combo.grid(row=2, column=1, sticky="w", padx=10, pady=8)
        parcelas_combo.set("1x")

        parcela_label = ctk.CTkLabel(resumo, text="")
        parcela_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        total_label = ctk.CTkLabel(resumo, text="Total: R$ 0,00", font=ctk.CTkFont(size=22, weight="bold"))
        total_label.grid(row=4, column=0, columnspan=2, padx=10, pady=12, sticky="w")

        def atualizar_parcelamento():
            try:
                desconto = float(desconto_entry.get().replace(",", ".") or 0)
            except ValueError:
                desconto = 0

            subtotal = sum(item["subtotal"] for item in self.carrinho)
            desconto = max(0, min(desconto, subtotal))
            total = subtotal - desconto

            try:
                parcelas = int(parcelas_combo.get().replace("x", ""))
            except ValueError:
                parcelas = 1

            if pagamento.get() == "Cartão de crédito":
                valor_parcela = total / parcelas if parcelas > 0 else total
                parcela_label.configure(text=f"{parcelas}x de {self.moeda(valor_parcela)}")
            else:
                parcelas_combo.set("1x")
                parcela_label.configure(text="")

            total_label.configure(text=f"Total: {self.moeda(total)}")

        def atualizar_carrinho():
            for widget in lista_carrinho.winfo_children():
                widget.destroy()

            for indice, item in enumerate(self.carrinho):
                linha = ctk.CTkFrame(lista_carrinho)
                linha.pack(fill="x", pady=3)

                ctk.CTkLabel(linha, text=item["nome"]).pack(side="left", padx=10, expand=True, fill="x")
                ctk.CTkLabel(linha, text=f"{item['quantidade']} x {self.moeda(item['preco'])}").pack(side="left", padx=10)
                ctk.CTkLabel(linha, text=self.moeda(item["subtotal"])).pack(side="left", padx=10)

                ctk.CTkButton(
                    linha, text="X", width=35, fg_color="#b3261e", hover_color="#8f1d18",
                    command=lambda i=indice: remover_item(i)
                ).pack(side="right", padx=5)

            atualizar_parcelamento()

        def adicionar_item():
            if not nomes_produtos:
                messagebox.showwarning("Venda", "Não existem produtos cadastrados.", parent=janela)
                return

            produto = mapa_produtos.get(produto_combo.get())
            if not produto:
                return

            try:
                qtd = int(quantidade.get())
            except ValueError:
                messagebox.showwarning("Venda", "Informe uma quantidade válida.", parent=janela)
                return

            if qtd <= 0:
                messagebox.showwarning("Venda", "A quantidade deve ser maior que zero.", parent=janela)
                return

            estoque = int(produto["estoque"] or 0)
            existente = sum(item["quantidade"] for item in self.carrinho if item["produto_id"] == produto["id"])

            if existente + qtd > estoque:
                messagebox.showwarning("Estoque insuficiente", f"Estoque disponível: {estoque}", parent=janela)
                return

            preco = float(produto["preco"] or 0)
            self.carrinho.append({
                "produto_id": produto["id"],
                "nome": produto["nome"],
                "quantidade": qtd,
                "preco": preco,
                "subtotal": preco * qtd
            })

            quantidade.delete(0, "end")
            quantidade.insert(0, "1")
            atualizar_carrinho()

        def remover_item(indice):
            if 0 <= indice < len(self.carrinho):
                self.carrinho.pop(indice)
                atualizar_carrinho()

        ctk.CTkButton(produto_frame, text="Adicionar", command=adicionar_item).grid(row=0, column=3, padx=10, pady=10)
        pagamento.configure(command=lambda e: atualizar_parcelamento())
        parcelas_combo.configure(command=lambda e: atualizar_parcelamento())
        desconto_entry.bind("<KeyRelease>", lambda e: atualizar_parcelamento())

        botoes = ctk.CTkFrame(janela, fg_color="transparent")
        botoes.grid(row=3, column=0, sticky="ew", padx=25, pady=15)

        def salvar_venda():
            if not self.carrinho:
                messagebox.showwarning("Venda", "Adicione pelo menos um produto.", parent=janela)
                return

            cliente_id = mapa_clientes.get(cliente_combo.get())
            if not cliente_id:
                messagebox.showwarning("Venda", "Selecione um cliente.", parent=janela)
                return

            try:
                desconto = float(desconto_entry.get().replace(",", ".") or 0)
            except ValueError:
                messagebox.showwarning("Venda", "Informe um desconto válido.", parent=janela)
                return

            subtotal = sum(item["subtotal"] for item in self.carrinho)
            desconto = max(0, min(desconto, subtotal))
            total = subtotal - desconto
            forma = pagamento.get()
            parcelas = int(parcelas_combo.get().replace("x", "")) if forma == "Cartão de crédito" else 1

            conn = None
            try:
                conn = conectar()
                conn.execute("BEGIN TRANSACTION")

                # Valida estoque no momento de salvar
                for item in self.carrinho:
                    prod = conn.execute("SELECT estoque, nome FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
                    if not prod:
                        raise Exception(f"Produto {item['nome']} não encontrado no banco.")
                    if prod["estoque"] < item["quantidade"]:
                        raise Exception(f"Estoque insuficiente para {prod['nome']}. Disponível: {prod['estoque']}")

                # Insere a Venda
                cursor = conn.execute("""
                    INSERT INTO vendas (cliente_id, subtotal, desconto, total, forma_pagamento, parcelas, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Concluída')
                """, (cliente_id, subtotal, desconto, total, forma, parcelas))
                venda_id = cursor.lastrowid

                # Insere os Itens e Atualiza o Estoque
                for item in self.carrinho:
                    conn.execute("""
                        INSERT INTO vendas_itens (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (venda_id, item["produto_id"], item["quantidade"], item["preco"], item["subtotal"]))

                    conn.execute("""
                        UPDATE produtos SET estoque = estoque - ? WHERE id = ?
                    """, (item["quantidade"], item["produto_id"]))

                # Gera Contas a Receber se for parcelado ou a prazo
                if parcelas > 1 or forma in ["Boleto", "Cartão de crédito"]:
                    valor_parcela = total / parcelas
                    data_base = datetime.now()
                    for p in range(1, parcelas + 1):
                        vencimento = (data_base + timedelta(days=30 * p)).strftime("%Y-%m-%d")
                        conn.execute("""
                            INSERT INTO contas_receber (venda_id, cliente_id, parcela, total_parcelas, valor, vencimento, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pendente')
                        """, (venda_id, cliente_id, p, parcelas, valor_parcela, vencimento))

                conn.commit()
                messagebox.showinfo("Sucesso", "Venda realizada com sucesso!", parent=janela)
                janela.destroy()
                self.carregar_vendas()

            except Exception as e:
                if conn:
                    conn.rollback()
                messagebox.showerror("Erro na Venda", f"Ocorreu um erro ao processar a venda:\n{str(e)}", parent=janela)
            finally:
                if conn:
                    conn.close()

        ctk.CTkButton(botoes, text="Finalizar Venda", command=salvar_venda, width=150).pack(side="right", padx=5)
        ctk.CTkButton(botoes, text="Cancelar", command=janela.destroy, width=100, fg_color="transparent", border_width=1).pack(side="right", padx=5)

    # ==========================================================
    # VISUALIZAR E CANCELAR VENDAS
    # ==========================================================

    def ver_venda(self, venda_id):
        janela = ctk.CTkToplevel(self)
        janela.title(f"Detalhes da Venda #{venda_id}")
        janela.geometry("600x500")
        janela.transient(self.winfo_toplevel())

        conn = conectar()
        venda = conn.execute("""
            SELECT v.*, c.nome as cliente_nome 
            FROM vendas v 
            LEFT JOIN clientes c ON c.id = v.cliente_id 
            WHERE v.id = ?
        """, (venda_id,)).fetchone()

        itens = conn.execute("""
            SELECT i.*, p.nome 
            FROM vendas_itens i 
            JOIN produtos p ON p.id = i.produto_id 
            WHERE i.venda_id = ?
        """, (venda_id,)).fetchall()
        conn.close()

        if not venda:
            messagebox.showerror("Erro", "Venda não encontrada.", parent=janela)
            janela.destroy()
            return

        ctk.CTkLabel(janela, text=f"Venda #{venda['id']}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(janela, text=f"Cliente: {venda['cliente_nome'] or 'N/A'}").pack(anchor="w", padx=20)
        ctk.CTkLabel(janela, text=f"Data: {venda['data']}").pack(anchor="w", padx=20)
        ctk.CTkLabel(janela, text=f"Forma de Pagamento: {venda['forma_pagamento']} ({venda['parcelas']}x)").pack(anchor="w", padx=20)

        lista_itens = ctk.CTkScrollableFrame(janela, height=200)
        lista_itens.pack(fill="both", expand=True, padx=20, pady=10)

        for item in itens:
            linha = ctk.CTkFrame(lista_itens)
            linha.pack(fill="x", pady=2)
            ctk.CTkLabel(linha, text=item["nome"]).pack(side="left", padx=5)
            ctk.CTkLabel(linha, text=f"{item['quantidade']} x {self.moeda(item['preco_unitario'])}").pack(side="right", padx=5)

        ctk.CTkLabel(janela, text=f"Total: {self.moeda(venda['total'])}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    def solicitar_cancelamento(self, venda_id):
        if not messagebox.askyesno("Confirmar Cancelamento", f"Deseja realmente cancelar a Venda #{venda_id}?\nEsta ação devolverá os itens ao estoque.", parent=self):
            return

        conn = None
        try:
            conn = conectar()
            conn.execute("BEGIN TRANSACTION")

            itens = conn.execute("SELECT produto_id, quantidade FROM vendas_itens WHERE venda_id = ?", (venda_id,)).fetchall()
            for item in itens:
                conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (item["quantidade"], item["produto_id"]))

            conn.execute("UPDATE vendas SET status = 'Cancelada', cancelada_em = CURRENT_TIMESTAMP WHERE id = ?", (venda_id,))
            conn.execute("DELETE FROM contas_receber WHERE venda_id = ? AND status = 'Pendente'", (venda_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Venda cancelada e estoque estornado!", parent=self)
            self.carregar_vendas()
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erro", f"Erro ao cancelar venda:\n{str(e)}", parent=self)
        finally:
            if conn:
                conn.close()