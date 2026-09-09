import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import os
import tempfile
import threading
from database import conectar


class VendasFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)
        self.voltar = voltar
        self.carrinho = []
        # Corrigido: Garantir a criação/migração das colunas ANTES de montar a tela
        self.criar_tabelas()
        self.montar_tela()

    # ==========================================================
    # BANCO DE DADOS E TABELAS
    # ==========================================================

    def criar_tabelas(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                data TEXT DEFAULT CURRENT_TIMESTAMP,
                subtotal REAL DEFAULT 0,
                desconto REAL DEFAULT 0,
                total REAL DEFAULT 0,
                entrada REAL DEFAULT 0,
                forma_pagamento TEXT,
                tipo_cartao TEXT,
                bandeira_cartao TEXT,
                observacoes TEXT,
                parcelas INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Concluída',
                cancelada_em TEXT,
                cancelada_por TEXT,
                juros_percentual REAL DEFAULT 0,
                total_sem_juros REAL DEFAULT 0
            )
        """)

        # Garantir adição das colunas tipo_cartao e bandeira_cartao caso o banco já existisse
        cursor.execute("PRAGMA table_info(vendas);")
        colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

        if "tipo_cartao" not in colunas_existentes:
            cursor.execute("ALTER TABLE vendas ADD COLUMN tipo_cartao TEXT;")
        if "bandeira_cartao" not in colunas_existentes:
            cursor.execute("ALTER TABLE vendas ADD COLUMN bandeira_cartao TEXT;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                subtotal REAL NOT NULL
            )
        """)

        cursor.execute("""
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

    def moeda(self, valor):
        val = valor if valor is not None else 0.0
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def buscar_clientes(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome")
        linhas = cursor.fetchall()
        conn.close()
        return [{"id": l[0], "nome": l[1], "cpf": l[2]} for l in linhas]

    def buscar_produtos(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco, estoque FROM produtos ORDER BY nome")
        linhas = cursor.fetchall()
        conn.close()
        return [{"id": l[0], "nome": l[1], "preco": l[2], "estoque": l[3]} for l in linhas]

    # ==========================================================
    # IMPRESSÃO DE COMPROVANTE (SEGURA CONTRA ERROS DE GIL)
    # ==========================================================

    def imprimir_comprovante(self, venda_id):
        def _executar_impressao():
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT v.id, c.nome, c.cpf, v.data, v.forma_pagamento, v.parcelas, 
                       v.subtotal, v.desconto, v.total, v.tipo_cartao, v.bandeira_cartao
                FROM vendas v
                LEFT JOIN clientes c ON c.id = v.cliente_id
                WHERE v.id = ?
            """, (venda_id,))
            venda = cursor.fetchone()

            cursor.execute("""
                SELECT p.nome, i.quantidade, i.preco_unitario, i.subtotal
                FROM vendas_itens i
                JOIN produtos p ON p.id = i.produto_id
                WHERE i.venda_id = ?
            """, (venda_id,))
            itens = cursor.fetchall()
            conn.close()

            if not venda:
                self.after(0, lambda: messagebox.showerror("Erro", "Venda não encontrada para impressão."))
                return

            # Formatação no padrão de comprovante não-fiscal (40 colunas)
            largura = 40
            div = "-" * largura

            cupom = []
            cupom.append("          COMPROVANTE DE VENDA          ".center(largura))
            cupom.append(div)
            cupom.append(f"Venda: #{venda[0]}")
            cupom.append(f"Data:  {venda[3] or datetime.now().strftime('%Y-%m-%d %H:%M')}")
            cupom.append(f"Cliente: {venda[1] or 'Consumidor Final'}")
            if venda[2]:
                cupom.append(f"CPF: {venda[2]}")
            cupom.append(div)
            cupom.append(f"{'QTD x ITEM':<24} {'VALOR':>14}")
            cupom.append(div)

            for item in itens:
                nome_p, qtd, preco_u, sub = item
                nome_p = (nome_p[:22] + "..") if len(nome_p) > 24 else nome_p
                cupom.append(f"{nome_p}")
                cupom.append(f"  {qtd} x {self.moeda(preco_u):<12} {self.moeda(sub):>18}")

            cupom.append(div)
            cupom.append(f"{'Subtotal:':<20} {self.moeda(venda[6]):>19}")
            if venda[7] and venda[7] > 0:
                cupom.append(f"{'Desconto:':<20} {self.moeda(venda[7]):>19}")
            cupom.append(f"{'TOTAL:':<20} {self.moeda(venda[8]):>19}")
            cupom.append(div)

            info_pgto = f"Forma Pgto: {venda[4]}"
            if venda[5] and venda[5] > 1:
                info_pgto += f" ({venda[5]}x)"
            cupom.append(info_pgto)

            if venda[9] or venda[10]:
                cupom.append(f"Cartao: {venda[9] or ''} {venda[10] or ''}".strip())

            cupom.append(div)
            cupom.append("       Obrigado pela preferencia!       ".center(largura))
            cupom.append("\n\n")

            texto_cupom = "\n".join(cupom)

            try:
                temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")
                temp_file.write(texto_cupom)
                temp_file.close()

                # Tenta enviar diretamente para a impressora padrão
                os.startfile(temp_file.name, "print")
            except Exception:
                # Fallback seguro: abre o arquivo de texto para impressão manual caso não haja impressora padrão configurada
                os.startfile(temp_file.name)

        # Roda em thread separada para não travar nem quebrar a GIL do Tkinter
        threading.Thread(target=_executar_impressao, daemon=True).start()

    # ==========================================================
    # TELA PRINCIPAL DE VENDAS
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
            topo, text="Voltar", command=self.voltar, width=100,
            fg_color="transparent", border_width=1
        ).grid(row=0, column=3, padx=5)

        conteudo = ctk.CTkFrame(self)
        conteudo.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        conteudo.grid_columnconfigure(0, weight=1)
        conteudo.grid_rowconfigure(1, weight=1)

        self.pesquisa = ctk.CTkEntry(
            conteudo, placeholder_text="Pesquisar venda por cliente..."
        )
        self.pesquisa.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.pesquisa.bind("<KeyRelease>", lambda e: self.carregar_vendas())

        self.lista = ctk.CTkScrollableFrame(conteudo)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.carregar_vendas()

    def carregar_vendas(self):
        for widget in self.lista.winfo_children():
            widget.destroy()

        termo = self.pesquisa.get().strip().lower()
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.id, c.nome, v.data, v.forma_pagamento, v.parcelas, v.total, v.status
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            ORDER BY v.id DESC
        """)
        vendas = cursor.fetchall()
        conn.close()

        for row in vendas:
            v_id, cliente_nome, data, forma_pagamento, parcelas, total, status = row
            cliente = cliente_nome or "Venda sem cliente"
            st_limpo = (status or "Concluída").strip().title()

            if termo and termo not in cliente.lower():
                continue

            linha = ctk.CTkFrame(self.lista)
            linha.pack(fill="x", pady=6, padx=5)

            info_frame = ctk.CTkFrame(linha, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info_frame, text=f"Venda #{v_id}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 15))
            ctk.CTkLabel(info_frame, text=cliente).pack(side="left", padx=10)
            ctk.CTkLabel(info_frame, text=data or "-").pack(side="left", padx=10)

            qtd_parcelas = parcelas or 1
            pagamento = forma_pagamento or "-"
            if pagamento in ["Cartão de crédito", "Cartão"] and qtd_parcelas > 1:
                pagamento = f"Crédito {qtd_parcelas}x"

            ctk.CTkLabel(info_frame, text=pagamento).pack(side="left", padx=10)
            ctk.CTkLabel(info_frame, text=self.moeda(total), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

            cor_status = "#e53935" if st_limpo == "Cancelada" else "#4caf50"
            ctk.CTkLabel(info_frame, text=f"[{st_limpo}]", text_color=cor_status).pack(side="left", padx=10)

            acoes_frame = ctk.CTkFrame(linha, fg_color="transparent")
            acoes_frame.pack(side="right", padx=10, pady=8)

            ctk.CTkButton(
                acoes_frame, text="Ver", width=70, command=lambda vid=v_id: self.ver_venda(vid)
            ).pack(side="left", padx=4)

            if st_limpo != "Cancelada":
                ctk.CTkButton(
                    acoes_frame, text="Cancelar", width=85, fg_color="#b3261e", hover_color="#8f1d18",
                    command=lambda vid=v_id: self.solicitar_cancelamento(vid)
                ).pack(side="left", padx=4)

    # ==========================================================
    # CANCELAMENTO DE VENDAS
    # ==========================================================

    def pedir_senha_supervisor(self, callback_sucesso):
        janela_senha = ctk.CTkToplevel(self)
        janela_senha.title("Autorização do Supervisor")
        janela_senha.geometry("380x220")
        janela_senha.resizable(False, False)
        janela_senha.transient(self.winfo_toplevel())
        janela_senha.grab_set()

        ctk.CTkLabel(
            janela_senha, text="Cancelar Venda", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            janela_senha, text="Digite a senha do supervisor para autorizar:", font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 10))

        entry_senha = ctk.CTkEntry(janela_senha, show="*", width=220, placeholder_text="Senha do supervisor")
        entry_senha.pack(pady=5)
        entry_senha.focus_set()

        def verificar_e_prosseguir():
            senha_digitada = entry_senha.get().strip()

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM usuarios WHERE (usuario = 'supervisor' OR nivel = 'supervisor') AND senha = ? AND ativo = 1",
                (senha_digitada,)
            )
            supervisor = cursor.fetchone()
            conn.close()

            if supervisor:
                janela_senha.destroy()
                callback_sucesso()
            else:
                messagebox.showerror("Acesso Negado", "Senha de supervisor incorreta!", parent=janela_senha)
                entry_senha.delete(0, "end")

        entry_senha.bind("<Return>", lambda event: verificar_e_prosseguir())

        btn_frame = ctk.CTkFrame(janela_senha, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame, text="Confirmar", width=100, fg_color="#2e7d32", hover_color="#1b5e20",
            command=verificar_e_prosseguir
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=100, fg_color="transparent", border_width=1,
            command=janela_senha.destroy
        ).pack(side="left", padx=5)

    def solicitar_cancelamento(self, venda_id):
        def efetuar_cancelamento():
            if not messagebox.askyesno("Confirmar Cancelamento", f"Deseja realmente cancelar a Venda #{venda_id}?\nEsta ação devolverá os itens ao estoque.", parent=self):
                return

            conn = conectar()
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT produto_id, quantidade FROM vendas_itens WHERE venda_id = ?", (venda_id,))
                itens = cursor.fetchall()
                for prod_id, qtd in itens:
                    cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (qtd, prod_id))

                cursor.execute("UPDATE vendas SET status = 'Cancelada', cancelada_em = CURRENT_TIMESTAMP WHERE id = ?", (venda_id,))
                cursor.execute("DELETE FROM contas_receber WHERE venda_id = ? AND status = 'Pendente'", (venda_id,))

                conn.commit()
                messagebox.showinfo("Sucesso", f"Venda #{venda_id} cancelada com sucesso!", parent=self)
                self.carregar_vendas()
            except Exception as err:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao cancelar venda:\n{err}", parent=self)
            finally:
                conn.close()

        self.pedir_senha_supervisor(efetuar_cancelamento)

    def ver_venda(self, venda_id):
        janela = ctk.CTkToplevel(self)
        janela.title(f"Detalhes da Venda #{venda_id}")
        janela.geometry("600x580")
        janela.transient(self.winfo_toplevel())

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.id, c.nome, v.data, v.forma_pagamento, v.parcelas, v.total, v.status, v.tipo_cartao, v.bandeira_cartao
            FROM vendas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            WHERE v.id = ?
        """, (venda_id,))
        venda = cursor.fetchone()

        cursor.execute("""
            SELECT i.quantidade, i.preco_unitario, i.subtotal, p.nome
            FROM vendas_itens i
            JOIN produtos p ON p.id = i.produto_id
            WHERE i.venda_id = ?
        """, (venda_id,))
        itens = cursor.fetchall()
        conn.close()

        if not venda:
            messagebox.showerror("Erro", "Venda não encontrada.", parent=janela)
            janela.destroy()
            return

        ctk.CTkLabel(janela, text=f"Venda #{venda[0]}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(janela, text=f"Cliente: {venda[1] or 'N/A'}").pack(anchor="w", padx=20)
        ctk.CTkLabel(janela, text=f"Data: {venda[2] or '-'}").pack(anchor="w", padx=20)
        
        info_pgto = f"Forma de Pagamento: {venda[3]} ({venda[4]}x)"
        if venda[7] or venda[8]:
            info_pgto += f" - {venda[7] or ''} {venda[8] or ''}"
        ctk.CTkLabel(janela, text=info_pgto).pack(anchor="w", padx=20)

        lista_itens = ctk.CTkScrollableFrame(janela, height=200)
        lista_itens.pack(fill="both", expand=True, padx=20, pady=10)

        for item in itens:
            qtd, preco_u, sub, p_nome = item
            linha = ctk.CTkFrame(lista_itens)
            linha.pack(fill="x", pady=2)
            ctk.CTkLabel(linha, text=p_nome).pack(side="left", padx=5)
            ctk.CTkLabel(linha, text=f"{qtd} x {self.moeda(preco_u)} = {self.moeda(sub)}").pack(side="right", padx=5)

        ctk.CTkLabel(janela, text=f"Total: {self.moeda(venda[5])}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        ctk.CTkButton(
            janela, text="Imprimir Comprovante", 
            command=lambda: self.imprimir_comprovante(venda_id)
        ).pack(pady=(0, 15))

    # ==========================================================
    # JANELA DE NOVA VENDA
    # ==========================================================

    def nova_venda(self):
        self.carrinho = []
        janela = ctk.CTkToplevel(self)
        janela.title("Nova Venda")
        janela.geometry("1000x850")
        janela.transient(self.winfo_toplevel())
        janela.grab_set()

        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(janela, text="Nova Venda", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, padx=25, pady=20, sticky="w")

        clientes = self.buscar_clientes()
        mapa_clientes = {f"{c['nome']} - {c['cpf']}" if c['cpf'] else c['nome']: c['id'] for c in clientes}
        nomes_clientes = list(mapa_clientes.keys())

        cliente_frame = ctk.CTkFrame(janela)
        cliente_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=5)
        cliente_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cliente_frame, text="Cliente:").grid(row=0, column=0, padx=10, pady=10)
        cliente_combo = ctk.CTkComboBox(cliente_frame, values=nomes_clientes or ["Nenhum cliente cadastrado"])
        if nomes_clientes:
            cliente_combo.set(nomes_clientes[0])
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
        mapa_produtos = {
            f"{p['nome']} | R$ {float(p['preco'] or 0):.2f} | Estoque: {int(p['estoque'] or 0)}": p
            for p in produtos
        }
        nomes_produtos = list(mapa_produtos.keys())

        produto_combo = ctk.CTkComboBox(produto_frame, values=nomes_produtos or ["Nenhum produto cadastrado"])
        if nomes_produtos:
            produto_combo.set(nomes_produtos[0])
        produto_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        quantidade = ctk.CTkEntry(produto_frame, width=90, placeholder_text="Qtd.")
        quantidade.grid(row=0, column=2, padx=10, pady=10)
        quantidade.insert(0, "1")

        lista_carrinho = ctk.CTkScrollableFrame(area)
        lista_carrinho.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        resumo = ctk.CTkFrame(area)
        resumo.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        resumo.grid_columnconfigure(1, weight=1)

        # DESCONTO
        ctk.CTkLabel(resumo, text="Desconto (R$):").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        desconto_entry = ctk.CTkEntry(resumo, width=120)
        desconto_entry.grid(row=0, column=1, sticky="w", padx=10, pady=6)
        desconto_entry.insert(0, "0")

        # FORMA DE PAGAMENTO
        ctk.CTkLabel(resumo, text="Forma de pagamento:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        pagamento = ctk.CTkComboBox(resumo, values=["Dinheiro", "Pix", "Cartão de débito", "Cartão de crédito", "Boleto", "Outro"], width=220)
        pagamento.grid(row=1, column=1, sticky="w", padx=10, pady=6)
        pagamento.set("Pix")

        # DETALHES DO CARTÃO (TIPO E BANDEIRA)
        cartao_frame = ctk.CTkFrame(resumo, fg_color="transparent")
        cartao_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="w")

        ctk.CTkLabel(cartao_frame, text="Tipo:").pack(side="left", padx=(0, 5))
        tipo_cartao_combo = ctk.CTkComboBox(cartao_frame, values=["Crédito", "Débito"], width=110)
        tipo_cartao_combo.pack(side="left", padx=(0, 15))
        tipo_cartao_combo.set("Crédito")

        ctk.CTkLabel(cartao_frame, text="Bandeira:").pack(side="left", padx=(0, 5))
        bandeira_combo = ctk.CTkComboBox(cartao_frame, values=["Visa", "Mastercard", "Elo", "Hipercard", "Amex", "Outra"], width=120)
        bandeira_combo.pack(side="left")
        bandeira_combo.set("Visa")

        # PARCELAMENTO
        ctk.CTkLabel(resumo, text="Parcelamento:").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        parcelas_combo = ctk.CTkComboBox(resumo, values=[f"{i}x" for i in range(1, 13)], width=120)
        parcelas_combo.grid(row=3, column=1, sticky="w", padx=10, pady=6)
        parcelas_combo.set("1x")

        # CONFIGURAÇÃO DE JUROS
        juros_var = ctk.BooleanVar(value=False)

        def alternar_juros():
            if juros_var.get():
                juros_entry.configure(state="normal")
            else:
                juros_entry.configure(state="disabled")
            atualizar_calculos()

        juros_frame = ctk.CTkFrame(resumo, fg_color="transparent")
        juros_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=6, sticky="w")

        aplicar_juros_check = ctk.CTkCheckBox(
            juros_frame, text="Cobrar Juros", variable=juros_var, command=alternar_juros
        )
        aplicar_juros_check.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(juros_frame, text="Taxa de Juros (% Total):").pack(side="left", padx=5)
        juros_entry = ctk.CTkEntry(juros_frame, width=80)
        juros_entry.insert(0, "2.0")
        juros_entry.configure(state="disabled")
        juros_entry.pack(side="left", padx=5)

        # RÓTULOS DE INFORMAÇÕES
        parcela_label = ctk.CTkLabel(resumo, text="")
        parcela_label.grid(row=5, column=0, columnspan=2, padx=10, pady=4, sticky="w")

        total_label = ctk.CTkLabel(resumo, text="Total: R$ 0,00", font=ctk.CTkFont(size=22, weight="bold"))
        total_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        def atualizar_calculos(*args):
            try:
                desconto = float(desconto_entry.get().replace(",", ".") or 0)
            except ValueError:
                desconto = 0.0

            subtotal = sum(item["subtotal"] for item in self.carrinho)
            desconto = max(0.0, min(desconto, subtotal))
            total_sem_juros = subtotal - desconto

            forma_pgto = pagamento.get()

            if "Cartão" in forma_pgto:
                cartao_frame.grid()
                if forma_pgto == "Cartão de débito":
                    tipo_cartao_combo.set("Débito")
                elif forma_pgto == "Cartão de crédito":
                    tipo_cartao_combo.set("Crédito")
            else:
                cartao_frame.grid_remove()

            if forma_pgto != "Cartão de crédito":
                parcelas_combo.set("1x")
                parcelas = 1
            else:
                try:
                    parcelas = int(parcelas_combo.get().replace("x", ""))
                except ValueError:
                    parcelas = 1

            juros_percentual = 0.0
            if juros_var.get():
                try:
                    juros_percentual = float(juros_entry.get().replace(",", ".") or 0)
                except ValueError:
                    juros_percentual = 0.0

            total = round(total_sem_juros * (1 + juros_percentual / 100), 2)

            if forma_pgto == "Cartão de crédito":
                valor_parcela = total / parcelas if parcelas > 0 else total
                if juros_percentual > 0:
                    parcela_label.configure(text=f"{parcelas}x de {self.moeda(valor_parcela)} | Juros inclusos: {juros_percentual:.2f}%")
                else:
                    parcela_label.configure(text=f"{parcelas}x de {self.moeda(valor_parcela)} | Sem juros")
            else:
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

            atualizar_calculos()

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

        pagamento.configure(command=lambda e: atualizar_calculos())
        parcelas_combo.configure(command=lambda e: atualizar_calculos())
        desconto_entry.bind("<KeyRelease>", lambda e: atualizar_calculos())
        juros_entry.bind("<KeyRelease>", lambda e: atualizar_calculos())

        botoes = ctk.CTkFrame(janela, fg_color="transparent")
        botoes.grid(row=3, column=0, sticky="ew", padx=25, pady=15)

        def salvar_venda():
            if not self.carrinho:
                messagebox.showwarning("Venda", "Adicione pelo menos um produto ao carrinho.", parent=janela)
                return

            cliente_id = mapa_clientes.get(cliente_combo.get())
            if not cliente_id:
                messagebox.showwarning("Venda", "Selecione um cliente válido.", parent=janela)
                return

            try:
                desconto = float(desconto_entry.get().replace(",", ".") or 0)
            except ValueError:
                desconto = 0.0

            subtotal = sum(item["subtotal"] for item in self.carrinho)
            total_sem_juros = max(0.0, subtotal - desconto)

            forma_pgto = pagamento.get()
            parcelas = 1 if forma_pgto != "Cartão de crédito" else int(parcelas_combo.get().replace("x", ""))
            
            tipo_cartao = tipo_cartao_combo.get() if "Cartão" in forma_pgto else None
            bandeira_cartao = bandeira_combo.get() if "Cartão" in forma_pgto else None

            juros_percentual = 0.0
            if juros_var.get():
                try:
                    juros_percentual = float(juros_entry.get().replace(",", ".") or 0)
                except ValueError:
                    juros_percentual = 0.0

            total = round(total_sem_juros * (1 + juros_percentual / 100), 2)

            conn = conectar()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO vendas (cliente_id, subtotal, desconto, total, forma_pagamento, tipo_cartao, bandeira_cartao, parcelas, juros_percentual, total_sem_juros)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cliente_id, subtotal, desconto, total, forma_pgto, tipo_cartao, bandeira_cartao, parcelas, juros_percentual, total_sem_juros))

                venda_id = cursor.lastrowid

                for item in self.carrinho:
                    cursor.execute("""
                        INSERT INTO vendas_itens (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (venda_id, item["produto_id"], item["quantidade"], item["preco"], item["subtotal"]))

                    cursor.execute("""
                        UPDATE produtos SET estoque = estoque - ? WHERE id = ?
                    """, (item["quantidade"], item["produto_id"]))

                # CONTAS A RECEBER
                data_atual = datetime.now()
                
                if forma_pgto in ["Dinheiro", "Pix", "Cartão de débito"] or (forma_pgto != "Cartão de crédito" and parcelas == 1):
                    cursor.execute("""
                        INSERT INTO contas_receber (venda_id, cliente_id, parcela, total_parcelas, valor, vencimento, pagamento, data_pagamento, status)
                        VALUES (?, ?, 1, 1, ?, ?, ?, CURRENT_TIMESTAMP, 'Pago')
                    """, (venda_id, cliente_id, total, data_atual.strftime("%Y-%m-%d"), forma_pgto))
                else:
                    valor_base = round(total / parcelas, 2)
                    diferenca_centavos = round(total - (valor_base * parcelas), 2)

                    for i in range(1, parcelas + 1):
                        vencimento = (data_atual + timedelta(days=30 * i)).strftime("%Y-%m-%d")
                        valor_parcela = valor_base + diferenca_centavos if i == parcelas else valor_base
                        
                        cursor.execute("""
                            INSERT INTO contas_receber (venda_id, cliente_id, parcela, total_parcelas, valor, vencimento, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pendente')
                        """, (venda_id, cliente_id, i, parcelas, valor_parcela, vencimento))

                conn.commit()
                janela.destroy()
                self.carregar_vendas()

                if messagebox.askyesno("Imprimir Comprovante", f"Venda #{venda_id} realizada com sucesso!\nDeseja imprimir o comprovante?", parent=self):
                    self.imprimir_comprovante(venda_id)

            except Exception as err:
                conn.rollback()
                messagebox.showerror("Erro ao salvar", f"Ocorreu um erro ao salvar a venda:\n{err}", parent=janela)
            finally:
                conn.close()

        ctk.CTkButton(botoes, text="Salvar Venda", command=salvar_venda, fg_color="#2e7d32", hover_color="#1b5e20").pack(side="right", padx=5)
        ctk.CTkButton(botoes, text="Cancelar", command=janela.destroy, fg_color="transparent", border_width=1).pack(side="right", padx=5)