import os
import platform
import subprocess
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
from database import conectar

# Importações do ReportLab para geração do PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class CaixaFrame(ctk.CTkFrame):

    def __init__(self, master, voltar):
        super().__init__(master)
        self.voltar = voltar
        self.caixa_atual_id = None
        self.montar_tela()
        self.verificar_status_caixa()

    def moeda(self, valor):
        val = valor if valor is not None else 0.0
        return (
            f"R$ {val:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def verificar_status_caixa(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, saldo_inicial, data_abertura FROM caixa WHERE status ="
            " 'Aberto' ORDER BY id DESC LIMIT 1"
        )
        caixa = cursor.fetchone()
        conn.close()

        if caixa:
            self.caixa_atual_id = caixa[0]
            self.lbl_status.configure(
                text=f"Status: ABERTO (Iniciado em {caixa[2]})",
                text_color="#2e7d32",
            )
            self.btn_abrir.configure(state="disabled")
            self.btn_fechar.configure(state="normal")
            self.btn_movimentacao.configure(state="normal")
            self.carregar_resumo_dia()
        else:
            self.caixa_atual_id = None
            self.lbl_status.configure(
                text="Status: FECHADO", text_color="#b3261e"
            )
            self.btn_abrir.configure(state="normal")
            self.btn_fechar.configure(state="disabled")
            self.btn_movimentacao.configure(state="disabled")
            self.limpar_resumo()

    def montar_tela(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        topo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            topo,
            text="Fechamento de Caixa",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.lbl_status = ctk.CTkLabel(
            topo, text="Verificando...", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_status.grid(row=0, column=1, padx=20, sticky="w")

        ctk.CTkButton(
            topo,
            text="Voltar",
            command=self.voltar,
            width=100,
            fg_color="transparent",
            border_width=1,
        ).grid(row=0, column=2, padx=5)

        # Conteúdo Principal
        conteudo = ctk.CTkFrame(self)
        conteudo.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        conteudo.grid_columnconfigure((0, 1), weight=1)
        conteudo.grid_rowconfigure(1, weight=1)

        # Ações do Caixa
        acoes_frame = ctk.CTkFrame(conteudo)
        acoes_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=15
        )

        self.btn_abrir = ctk.CTkButton(
            acoes_frame,
            text="Abrir Caixa",
            command=self.abrir_caixa_dialog,
            fg_color="#2e7d32",
            hover_color="#1b5e20",
        )
        self.btn_abrir.pack(side="left", padx=10, pady=10)

        self.btn_movimentacao = ctk.CTkButton(
            acoes_frame,
            text="Sangria / Suprimento",
            command=self.movimentacao_dialog,
        )
        self.btn_movimentacao.pack(side="left", padx=10, pady=10)

        self.btn_fechar = ctk.CTkButton(
            acoes_frame,
            text="Fechar Caixa",
            command=self.fechar_caixa,
            fg_color="#b3261e",
            hover_color="#8f1d18",
        )
        self.btn_fechar.pack(side="right", padx=10, pady=10)

        # Resumo por Forma de Pagamento
        self.resumo_frame = ctk.CTkScrollableFrame(
            conteudo, label_text="Resumo de Vendas do Turno"
        )
        self.resumo_frame.grid(
            row=1, column=0, sticky="nsew", padx=(15, 7), pady=15
        )

        # Totalizadores
        self.totais_frame = ctk.CTkFrame(conteudo)
        self.totais_frame.grid(
            row=1, column=1, sticky="nsew", padx=(7, 15), pady=15
        )

        self.lbl_saldo_inicial = ctk.CTkLabel(
            self.totais_frame,
            text="Saldo Inicial: R$ 0,00",
            font=ctk.CTkFont(size=16),
        )
        self.lbl_saldo_inicial.pack(anchor="w", padx=20, pady=10)

        self.lbl_total_vendas = ctk.CTkLabel(
            self.totais_frame,
            text="Total Vendas: R$ 0,00",
            font=ctk.CTkFont(size=16),
        )
        self.lbl_total_vendas.pack(anchor="w", padx=20, pady=10)

        self.lbl_suprimentos = ctk.CTkLabel(
            self.totais_frame,
            text="Suprimentos (+): R$ 0,00",
            font=ctk.CTkFont(size=16),
            text_color="#2e7d32",
        )
        self.lbl_suprimentos.pack(anchor="w", padx=20, pady=10)

        self.lbl_sangrias = ctk.CTkLabel(
            self.totais_frame,
            text="Sangrias (-): R$ 0,00",
            font=ctk.CTkFont(size=16),
            text_color="#b3261e",
        )
        self.lbl_sangrias.pack(anchor="w", padx=20, pady=10)

        self.lbl_dinheiro_gaveta = ctk.CTkLabel(
            self.totais_frame,
            text="Dinheiro em Gaveta: R$ 0,00",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.lbl_dinheiro_gaveta.pack(anchor="w", padx=20, pady=20)

    def abrir_caixa_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Informe o valor inicial (Fundo de Maneio):", title="Abrir Caixa"
        )
        valor_str = dialog.get_input()
        if valor_str is not None:
            try:
                valor = float(valor_str.replace(",", "."))
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO caixa (saldo_inicial, status, data_abertura)"
                    " VALUES (?, 'Aberto', CURRENT_TIMESTAMP)",
                    (valor,),
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Sucesso", "Caixa aberto com sucesso!")
                self.verificar_status_caixa()
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido informado.")

    def carregar_resumo_dia(self):
        for widget in self.resumo_frame.winfo_children():
            widget.destroy()

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT saldo_inicial, data_abertura FROM caixa WHERE id = ?",
            (self.caixa_atual_id,),
        )
        caixa_info = cursor.fetchone()
        saldo_inicial = caixa_info[0] or 0.0
        data_abertura = caixa_info[1]

        cursor.execute(
            """
            SELECT forma_pagamento, SUM(total) 
            FROM vendas 
            WHERE data >= ? AND (status IS NULL OR status != 'Cancelada')
            GROUP BY forma_pagamento
        """,
            (data_abertura,),
        )
        vendas = cursor.fetchall()

        total_vendas = 0.0
        total_dinheiro_vendas = 0.0

        for forma, total in vendas:
            val = total or 0.0
            total_vendas += val
            if forma and forma.lower() == "dinheiro":
                total_dinheiro_vendas += val

            linha = ctk.CTkFrame(self.resumo_frame)
            linha.pack(fill="x", pady=4)
            ctk.CTkLabel(
                linha, text=str(forma), font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=10)
            ctk.CTkLabel(linha, text=self.moeda(val)).pack(
                side="right", padx=10
            )

        cursor.execute(
            """
            SELECT tipo, SUM(valor) FROM movimentacoes_caixa 
            WHERE caixa_id = ? GROUP BY tipo
        """,
            (self.caixa_atual_id,),
        )
        movimentacoes = dict(cursor.fetchall())
        conn.close()

        suprimentos = movimentacoes.get("Suprimento", 0.0)
        sangrias = movimentacoes.get("Sangria", 0.0)

        total_gaveta = (
            saldo_inicial + total_dinheiro_vendas + suprimentos - sangrias
        )

        self.lbl_saldo_inicial.configure(
            text=f"Saldo Inicial: {self.moeda(saldo_inicial)}"
        )
        self.lbl_total_vendas.configure(
            text=f"Total Faturado: {self.moeda(total_vendas)}"
        )
        self.lbl_suprimentos.configure(
            text=f"Suprimentos (+): {self.moeda(suprimentos)}"
        )
        self.lbl_sangrias.configure(
            text=f"Sangrias (-): {self.moeda(sangrias)}"
        )
        self.lbl_dinheiro_gaveta.configure(
            text=f"Dinheiro em Gaveta: {self.moeda(total_gaveta)}"
        )

    def limpar_resumo(self):
        for widget in self.resumo_frame.winfo_children():
            widget.destroy()
        self.lbl_saldo_inicial.configure(text="Saldo Inicial: R$ 0,00")
        self.lbl_total_vendas.configure(text="Total Vendas: R$ 0,00")
        self.lbl_suprimentos.configure(text="Suprimentos (+): R$ 0,00")
        self.lbl_sangrias.configure(text="Sangrias (-): R$ 0,00")
        self.lbl_dinheiro_gaveta.configure(text="Dinheiro em Gaveta: R$ 0,00")

    def movimentacao_dialog(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Registrar Sangria / Suprimento")
        janela.geometry("400x300")
        janela.transient(self.winfo_toplevel())
        janela.grab_set()

        ctk.CTkLabel(janela, text="Tipo de Movimentação:").pack(pady=(20, 5))
        tipo_combo = ctk.CTkComboBox(janela, values=["Sangria", "Suprimento"])
        tipo_combo.pack(pady=5)

        ctk.CTkLabel(janela, text="Valor (R$):").pack(pady=5)
        valor_entry = ctk.CTkEntry(janela)
        valor_entry.pack(pady=5)

        ctk.CTkLabel(janela, text="Motivo / Observação:").pack(pady=5)
        motivo_entry = ctk.CTkEntry(janela)
        motivo_entry.pack(pady=5)

        def salvar():
            try:
                valor = float(valor_entry.get().replace(",", "."))
                tipo = tipo_combo.get()
                motivo = motivo_entry.get()

                conn = conectar()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO movimentacoes_caixa (caixa_id, tipo, valor, motivo)
                    VALUES (?, ?, ?, ?)
                """,
                    (self.caixa_atual_id, tipo, valor, motivo),
                )
                conn.commit()
                conn.close()

                messagebox.showinfo(
                    "Sucesso",
                    f"{tipo} realizada com sucesso!",
                    parent=janela,
                )
                janela.destroy()
                self.carregar_resumo_dia()
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido.", parent=janela)

        ctk.CTkButton(janela, text="Confirmar", command=salvar).pack(pady=20)

    def fechar_caixa(self):
        try:
            if not self.caixa_atual_id:
                messagebox.showwarning(
                    "Aviso", "Não há nenhum caixa aberto no momento!"
                )
                return

            conn = conectar()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, saldo_inicial, data_abertura FROM caixa WHERE id = ?",
                (self.caixa_atual_id,),
            )
            caixa = cursor.fetchone()

            caixa_id = caixa[0]
            saldo_inicial = float(caixa[1] or 0.0)
            data_abertura = caixa[2]

            cursor.execute(
                """
                SELECT forma_pagamento, COALESCE(SUM(total), 0) 
                FROM vendas 
                WHERE data >= ? AND (status IS NULL OR status != 'Cancelada')
                GROUP BY forma_pagamento
            """,
                (data_abertura,),
            )
            vendas_por_forma = cursor.fetchall()

            vendas_dinheiro = 0.0
            total_faturado = 0.0
            dados_vendas = []
            linhas_vendas_texto = []

            for forma, total in vendas_por_forma:
                val = float(total or 0.0)
                total_faturado += val
                forma_nome = forma if forma else "Não Especificado"
                dados_vendas.append((forma_nome, val))
                linhas_vendas_texto.append(f"   • {forma_nome}: {self.moeda(val)}")

                if forma and forma.lower() == "dinheiro":
                    vendas_dinheiro = val

            texto_vendas_detalhado = (
                "\n".join(linhas_vendas_texto)
                if linhas_vendas_texto
                else "   • Nenhuma venda registrada"
            )

            cursor.execute(
                """
                SELECT tipo, COALESCE(SUM(valor), 0) 
                FROM movimentacoes_caixa 
                WHERE caixa_id = ? 
                GROUP BY tipo
            """,
                (caixa_id,),
            )
            movs = dict(cursor.fetchall())
            conn.close()

            suprimentos = float(movs.get("Suprimento", 0.0))
            sangrias = float(movs.get("Sangria", 0.0))

            saldo_esperado = (
                saldo_inicial + vendas_dinheiro + suprimentos - sangrias
            )

            resumo_texto = (
                "--- RESUMO DE FECHAMENTO ---\n\n"
                "📊 FATURAMENTO DO TURNO:\n"
                f"{texto_vendas_detalhado}\n"
                f" Total Faturado: {self.moeda(total_faturado)}\n\n"
                "-----------------------------\n"
                "💵 CONFERÊNCIA DA GAVETA (DINHEIRO):\n"
                f"(+) Saldo Inicial: {self.moeda(saldo_inicial)}\n"
                f"(+) Vendas em Dinheiro: {self.moeda(vendas_dinheiro)}\n"
                f"(+) Suprimentos: {self.moeda(suprimentos)}\n"
                f"(-) Sangrias: {self.moeda(sangrias)}\n"
                f"(=) Dinheiro Esperado em Gaveta: {self.moeda(saldo_esperado)}\n\n"
                "Deseja confirmar o fechamento do caixa?"
            )

            confirmar = messagebox.askyesno("Fechamento de Caixa", resumo_texto)

            if confirmar:
                data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = conectar()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE caixa 
                    SET status = 'Fechado', 
                        data_fechamento = ?, 
                        saldo_final = ? 
                    WHERE id = ?
                """,
                    (data_fechamento, saldo_esperado, caixa_id),
                )
                conn.commit()
                conn.close()

                messagebox.showinfo("Sucesso", "Caixa fechado com sucesso!")

                if messagebox.askyesno(
                    "Imprimir PDF",
                    "Deseja gerar e imprimir o PDF do comprovante?",
                ):
                    self.gerar_comprovante_pdf(
                        caixa_id,
                        data_abertura,
                        data_fechamento,
                        saldo_inicial,
                        total_faturado,
                        vendas_dinheiro,
                        suprimentos,
                        sangrias,
                        saldo_esperado,
                        dados_vendas,
                    )

                self.verificar_status_caixa()

        except Exception as e:
            messagebox.showerror(
                "Erro", f"Ocorreu um erro ao fechar o caixa:\n{e}"
            )

    def gerar_comprovante_pdf(
        self,
        caixa_id,
        abertura,
        fechamento,
        s_ini,
        tot_fat,
        v_din,
        supr,
        sang,
        s_esp,
        dados_vendas,
    ):
        """Gera o comprovante de fechamento de caixa em formato PDF estilizado."""
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=f"Fechamento_Caixa_{caixa_id}.pdf",
            title="Salvar Comprovante em PDF",
        )

        if not caminho:
            return

        try:
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40,
            )
            story = []

            styles = getSampleStyleSheet()

            # Customização dos Estilos
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                alignment=1,  # Centralizado
                textColor=colors.HexColor("#1e293b"),
            )

            subtitle_style = ParagraphStyle(
                "SubTitleStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                alignment=1,
                textColor=colors.HexColor("#64748b"),
            )

            section_style = ParagraphStyle(
                "SectionStyle",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=16,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=6,
            )

            normal_style = ParagraphStyle(
                "NormalStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#334155"),
            )

            # Cabeçalho do PDF
            story.append(Paragraph("RELATÓRIO DE FECHAMENTO DE CAIXA", title_style))
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"Caixa ID #{caixa_id} | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    subtitle_style,
                )
            )
            story.append(Spacer(1, 15))

            # Tabela de Informações Gerais
            info_data = [
                [
                    Paragraph("<b>Abertura:</b>", normal_style),
                    Paragraph(str(abertura), normal_style),
                ],
                [
                    Paragraph("<b>Fechamento:</b>", normal_style),
                    Paragraph(str(fechamento), normal_style),
                ],
            ]
            t_info = Table(info_data, colWidths=[100, 400])
            t_info.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ]
                )
            )
            story.append(t_info)
            story.append(Spacer(1, 15))

            # Seção: Faturamento por Forma de Pagamento
            story.append(Paragraph("Resumo de Faturamento", section_style))

            vendas_table_data = [["Forma de Pagamento", "Total (R$)"]]
            if dados_vendas:
                for forma, val in dados_vendas:
                    vendas_table_data.append([forma, self.moeda(val)])
            else:
                vendas_table_data.append(["Nenhuma venda registrada", "R$ 0,00"])

            vendas_table_data.append(["TOTAL FATURADO", self.moeda(tot_fat)])

            t_vendas = Table(vendas_table_data, colWidths=[350, 150])
            t_vendas.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("BACKGROUND", (0, 1), (-1, -2), colors.white),
                        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#0f172a")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(t_vendas)
            story.append(Spacer(1, 15))

            # Seção: Conferência de Dinheiro em Gaveta
            story.append(
                Paragraph("Conferência de Gaveta (Espécie)", section_style)
            )

            gaveta_data = [
                ["(+) Saldo Inicial", self.moeda(s_ini)],
                ["(+) Vendas em Dinheiro", self.moeda(v_din)],
                ["(+) Suprimentos", self.moeda(supr)],
                ["(-) Sangrias", self.moeda(sang)],
                ["(=) DINHEIRO EM GAVETA ESPERADO", self.moeda(s_esp)],
            ]

            t_gaveta = Table(gaveta_data, colWidths=[350, 150])
            t_gaveta.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dcfce7")),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#14532d")),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(t_gaveta)

            # Construir PDF
            doc.build(story)

            messagebox.showinfo(
                "Sucesso", f"Comprovante em PDF salvo com sucesso:\n{caminho}"
            )

            # Abrir/Imprimir o PDF gerado de acordo com o Sistema Operacional
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(caminho)
            elif sistema == "Darwin":
                subprocess.run(["open", caminho])
            else:
                subprocess.run(["xdg-open", caminho])

        except Exception as e:
            messagebox.showerror(
                "Erro de Geração",
                f"Ocorreu uma falha ao gerar o arquivo PDF:\n{e}",
            )