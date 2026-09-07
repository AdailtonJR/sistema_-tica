import os
import tempfile
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from database import conectar

# Importações do ReportLab para geração de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class OrdensServicoFrame(ctk.CTkFrame):
    def __init__(self, master, voltar):
        super().__init__(master)
        self.voltar = voltar
        self.os_id = None
        self.clientes = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.criar_tabela()
        self.montar_tela()
        self.carregar_clientes()
        self.carregar_os()

    def criar_tabela(self):
        conn = conectar()
        conn.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            previsao_entrega TEXT,
            tipo_servico TEXT,
            descricao TEXT,
            od_esferico TEXT, od_cilindrico TEXT, od_eixo TEXT, od_adicao TEXT,
            oe_esferico TEXT, oe_cilindrico TEXT, oe_eixo TEXT, oe_adicao TEXT,
            dnp_od TEXT, dnp_oe TEXT, altura_od TEXT, altura_oe TEXT,
            medida_a TEXT, ponte TEXT, diagonal_maior TEXT, vertical TEXT,
            tipo_lente TEXT, indice TEXT, material TEXT, tratamento TEXT,
            armacao_marca TEXT, armacao_modelo TEXT, armacao_cor TEXT, armacao_codigo TEXT,
            valor REAL DEFAULT 0, desconto REAL DEFAULT 0, total REAL DEFAULT 0,
            entrada REAL DEFAULT 0, saldo REAL DEFAULT 0, forma_pagamento TEXT,
            observacoes TEXT, status TEXT DEFAULT 'Aberta'
        )''')
        
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(ordens_servico)")
        existentes = {row[1] for row in cur.fetchall()}
        for coluna in ['diagonal_maior', 'vertical']:
            if coluna not in existentes:
                cur.execute(f"ALTER TABLE ordens_servico ADD COLUMN {coluna} TEXT")
                
        conn.commit()
        conn.close()

    def montar_tela(self):
        topo = ctk.CTkFrame(self, fg_color='transparent')
        topo.grid(row=0, column=0, sticky='ew', padx=20, pady=15)
        topo.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(topo, text='Ordens de Serviço', font=ctk.CTkFont(size=28, weight='bold')).grid(row=0, column=0, sticky='w')
        ctk.CTkButton(topo, text='Nova OS', command=self.nova_os, width=100).grid(row=0, column=1, padx=5)
        ctk.CTkButton(topo, text='Voltar', command=self.voltar, width=90).grid(row=0, column=2, padx=5)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0,20))
        self.tabs.add('Cadastro / Impressão')
        self.tabs.add('Ordens cadastradas')
        self.montar_formulario(self.tabs.tab('Cadastro / Impressão'))
        self.montar_lista(self.tabs.tab('Ordens cadastradas'))

    def entry(self, parent, label, row, col, width=130):
        ctk.CTkLabel(parent, text=label).grid(row=row, column=col, padx=5, pady=(5,0), sticky='w')
        e = ctk.CTkEntry(parent, width=width)
        e.grid(row=row+1, column=col, padx=5, pady=(0,6), sticky='ew')
        return e

    def montar_formulario(self, parent):
        parent.grid_columnconfigure((0,1,2,3), weight=1)
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill='both', expand=True, padx=5, pady=5)
        scroll.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(scroll, text='Dados da OS', font=ctk.CTkFont(size=20, weight='bold')).grid(row=0,column=0,columnspan=4,sticky='w',padx=10,pady=10)
        ctk.CTkLabel(scroll,text='Cliente').grid(row=1,column=0,padx=5,pady=5,sticky='w')
        self.cliente_combo=ctk.CTkComboBox(scroll,values=['Selecione'],width=280)
        self.cliente_combo.grid(row=2,column=0,columnspan=2,padx=5,pady=5,sticky='ew')
        self.data=self.entry(scroll,'Data',1,2)
        self.previsao=self.entry(scroll,'Previsão de entrega',1,3)
        self.data.insert(0,datetime.now().strftime('%d/%m/%Y'))
        self.previsao.insert(0,(datetime.now()+timedelta(days=3)).strftime('%d/%m/%Y'))
        self.tipo=self.entry(scroll,'Tipo de serviço',3,0)
        self.descricao=self.textbox(scroll,'Descrição do serviço',3,1,3)

        ctk.CTkLabel(scroll,text='RECEITA / GRAU',font=ctk.CTkFont(size=20,weight='bold')).grid(row=5,column=0,columnspan=4,sticky='w',padx=10,pady=(15,5))
        headers=['Olho','ESF','CIL','EIXO','ADD']
        for i,h in enumerate(headers): ctk.CTkLabel(scroll,text=h).grid(row=6,column=i,padx=5,pady=3)
        ctk.CTkLabel(scroll,text='OD (Direito)').grid(row=7,column=0,padx=5,pady=5)
        self.od_esf=self.simple(scroll,7,1); self.od_cil=self.simple(scroll,7,2); self.od_eixo=self.simple(scroll,7,3); self.od_add=self.simple(scroll,7,4)
        ctk.CTkLabel(scroll,text='OE (Esquerdo)').grid(row=8,column=0,padx=5,pady=5)
        self.oe_esf=self.simple(scroll,8,1); self.oe_cil=self.simple(scroll,8,2); self.oe_eixo=self.simple(scroll,8,3); self.oe_add=self.simple(scroll,8,4)

        ctk.CTkLabel(scroll,text='MEDIDAS DA MONTAGEM',font=ctk.CTkFont(size=20,weight='bold')).grid(row=10,column=0,columnspan=4,sticky='w',padx=10,pady=(15,5))
        ctk.CTkLabel(scroll,text='Medida').grid(row=11,column=0,padx=5,pady=3); ctk.CTkLabel(scroll,text='OD').grid(row=11,column=1,padx=5,pady=3); ctk.CTkLabel(scroll,text='OE').grid(row=11,column=2,padx=5,pady=3)
        for r,(lab,a,b) in enumerate([('DNP','dnp_od','dnp_oe'),('Altura','altura_od','altura_oe')],12):
            ctk.CTkLabel(scroll,text=lab).grid(row=r,column=0,padx=5,pady=5,sticky='w')
            setattr(self,a,self.simple(scroll,r,1)); setattr(self,b,self.simple(scroll,r,2))
        self.med_a=self.entry(scroll,'A',14,0); self.ponte=self.entry(scroll,'Ponte',14,1); self.diagonal_maior=self.entry(scroll,'Diagonal maior',14,2); self.vertical=self.entry(scroll,'Vertical',14,3)

        ctk.CTkLabel(scroll,text='LENTES E ARMAÇÃO',font=ctk.CTkFont(size=20,weight='bold')).grid(row=18,column=0,columnspan=4,sticky='w',padx=10,pady=(15,5))
        self.tipo_lente=self.entry(scroll,'Tipo de lente',19,0); self.indice=self.entry(scroll,'Índice',19,1); self.material=self.entry(scroll,'Material',19,2); self.tratamento=self.entry(scroll,'Tratamento',19,3)
        self.arm_marca=self.entry(scroll,'Marca da armação',21,0); self.arm_modelo=self.entry(scroll,'Modelo',21,1); self.arm_cor=self.entry(scroll,'Cor',21,2); self.arm_codigo=self.entry(scroll,'Código',21,3)

        ctk.CTkLabel(scroll,text='VALORES',font=ctk.CTkFont(size=20,weight='bold')).grid(row=23,column=0,columnspan=4,sticky='w',padx=10,pady=(15,5))
        self.valor=self.entry(scroll,'Valor',24,0); self.desconto=self.entry(scroll,'Desconto',24,1); self.entrada=self.entry(scroll,'Entrada',24,2)
        self.forma=self.entry(scroll,'Forma de pagamento',24,3)
        self.obs=self.textbox(scroll,'Observações',26,0,4)
        botoes=ctk.CTkFrame(scroll,fg_color='transparent'); botoes.grid(row=28,column=0,columnspan=4,pady=15)
        ctk.CTkButton(botoes,text='Salvar e Imprimir PDF',command=self.salvar,width=160).pack(side='left',padx=5)
        ctk.CTkButton(botoes,text='Gerar PDF',command=lambda: self.gerar_e_abrir_pdf(self.os_id),width=100).pack(side='left',padx=5)
        ctk.CTkButton(botoes,text='Limpar',command=self.nova_os,width=100).pack(side='left',padx=5)

    def simple(self,parent,row,col):
        e=ctk.CTkEntry(parent,width=120); e.grid(row=row,column=col,padx=5,pady=4,sticky='ew'); return e

    def textbox(self,parent,label,row,col,span=1):
        ctk.CTkLabel(parent,text=label).grid(row=row,column=col,columnspan=span,padx=5,pady=(5,0),sticky='w')
        t=ctk.CTkTextbox(parent,height=65); t.grid(row=row+1,column=col,columnspan=span,padx=5,pady=5,sticky='ew'); return t

    def montar_lista(self,parent):
        top=ctk.CTkFrame(parent,fg_color='transparent'); top.pack(fill='x',padx=10,pady=10)
        ctk.CTkButton(top,text='Atualizar',command=self.carregar_os,width=100).pack(side='left')
        self.lista=ctk.CTkScrollableFrame(parent); self.lista.pack(fill='both',expand=True,padx=10,pady=5)

    def carregar_clientes(self):
        conn=conectar(); rows=conn.execute('SELECT id,nome FROM clientes ORDER BY nome').fetchall(); conn.close()
        self.clientes=rows
        nomes=[f'{r["id"]} - {r["nome"]}' for r in rows] if rows else ['Nenhum cliente cadastrado']
        self.cliente_combo.configure(values=nomes); self.cliente_combo.set(nomes[0])

    def carregar_os(self):
        if not hasattr(self,'lista'): return
        for w in self.lista.winfo_children(): w.destroy()
        conn=conectar(); rows=conn.execute('''SELECT os.id,os.data,os.previsao_entrega,os.tipo_servico,os.total,os.status,c.nome cliente
            FROM ordens_servico os LEFT JOIN clientes c ON c.id=os.cliente_id ORDER BY os.id DESC''').fetchall(); conn.close()
        for r in rows:
            f=ctk.CTkFrame(self.lista); f.pack(fill='x',pady=4)
            ctk.CTkLabel(f,text=f'OS #{r["id"]}').pack(side='left',padx=10); ctk.CTkLabel(f,text=r['cliente'] or 'Sem cliente').pack(side='left',padx=10); ctk.CTkLabel(f,text=r['data']).pack(side='left',padx=10); ctk.CTkLabel(f,text=r['status']).pack(side='left',padx=10)
            ctk.CTkButton(f,text='Abrir',width=70,command=lambda oid=r['id']:self.abrir_os(oid)).pack(side='right',padx=5)
            ctk.CTkButton(f,text='PDF',width=70,command=lambda oid=r['id']:self.gerar_e_abrir_pdf(oid)).pack(side='right',padx=5)

    def get_text(self,t): return t.get('1.0','end').strip()
    def set_text(self,t,v): t.delete('1.0','end'); t.insert('1.0',v or '')
    def val(self,e): return e.get().strip()

    def cliente_id(self):
        s=self.cliente_combo.get()
        try: return int(s.split(' - ')[0])
        except: return None

    def salvar(self):
        cid=self.cliente_id()
        if not cid:
            messagebox.showwarning('OS','Selecione um cliente válido.'); return
        try:
            valor=float(self.val(self.valor).replace(',','.')) if self.val(self.valor) else 0.0
            desconto=float(self.val(self.desconto).replace(',','.')) if self.val(self.desconto) else 0.0
            entrada=float(self.val(self.entrada).replace(',','.')) if self.val(self.entrada) else 0.0
        except Exception:
            messagebox.showerror('OS','Confira os valores numéricos digitados (Valor, Desconto e Entrada).')
            return
            
        total=max(0.0, valor-desconto)
        saldo=max(0.0, total-entrada)
        
        campos=['cliente_id','data','previsao_entrega','tipo_servico','descricao','od_esferico','od_cilindrico','od_eixo','od_adicao','oe_esferico','oe_cilindrico','oe_eixo','oe_adicao','dnp_od','dnp_oe','altura_od','altura_oe','medida_a','ponte','diagonal_maior','vertical','tipo_lente','indice','material','tratamento','armacao_marca','armacao_modelo','armacao_cor','armacao_codigo','valor','desconto','total','entrada','saldo','forma_pagamento','observacoes','status']
        vals=[cid,self.val(self.data),self.val(self.previsao),self.val(self.tipo),self.get_text(self.descricao),self.val(self.od_esf),self.val(self.od_cil),self.val(self.od_eixo),self.val(self.od_add),self.val(self.oe_esf),self.val(self.oe_cil),self.val(self.oe_eixo),self.val(self.oe_add),self.val(self.dnp_od),self.val(self.dnp_oe),self.val(self.altura_od),self.val(self.altura_oe),self.val(self.med_a),self.val(self.ponte),self.val(self.diagonal_maior),self.val(self.vertical),self.val(self.tipo_lente),self.val(self.indice),self.val(self.material),self.val(self.tratamento),self.val(self.arm_marca),self.val(self.arm_modelo),self.val(self.arm_cor),self.val(self.arm_codigo),valor,desconto,total,entrada,saldo,self.val(self.forma),self.get_text(self.obs),'Aberta']
        
        conn=conectar()
        try:
            if self.os_id:
                sets=', '.join(f'{c}=?' for c in campos)
                conn.execute(f'UPDATE ordens_servico SET {sets} WHERE id=?', vals + [self.os_id])
                oid=self.os_id
            else:
                qs=','.join('?' for _ in campos)
                cur=conn.execute(f'INSERT INTO ordens_servico ({",".join(campos)}) VALUES ({qs})', vals)
                oid=cur.lastrowid
                
            conn.commit()
            self.os_id=oid
            self.carregar_os()
            
            # Gera e abre o PDF logo após salvar com sucesso
            self.gerar_e_abrir_pdf(oid)
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror('Erro no Banco de Dados', f'Não foi possível salvar a OS:\n{str(e)}')
        finally:
            conn.close()

    def nova_os(self):
        self.os_id=None
        self.tabs.set('Cadastro / Impressão')
        for name in ['data','previsao','tipo','od_esf','od_cil','od_eixo','od_add','oe_esf','oe_cil','oe_eixo','oe_add','dnp_od','dnp_oe','altura_od','altura_oe','med_a','ponte','diagonal_maior','vertical','tipo_lente','indice','material','tratamento','arm_marca','arm_modelo','arm_cor','arm_codigo','valor','desconto','entrada','forma']:
            e=getattr(self,name); e.delete(0,'end')
        self.data.insert(0,datetime.now().strftime('%d/%m/%Y'))
        self.previsao.insert(0,(datetime.now()+timedelta(days=3)).strftime('%d/%m/%Y'))
        self.set_text(self.descricao,'')
        self.set_text(self.obs,'')
        if self.clientes: 
            self.cliente_combo.set(f'{self.clientes[0]["id"]} - {self.clientes[0]["nome"]}')

    def abrir_os(self,oid):
        conn=conectar()
        r=conn.execute('SELECT * FROM ordens_servico WHERE id=?',(oid,)).fetchone()
        conn.close()
        if not r: return
        self.os_id=oid
        self.tabs.set('Cadastro / Impressão')
        cid=r['cliente_id']
        for x in self.clientes:
            if x['id']==cid: 
                self.cliente_combo.set(f'{x["id"]} - {x["nome"]}')
                break
        mapping={'data':'data','previsao':'previsao_entrega','tipo':'tipo_servico','od_esf':'od_esferico','od_cil':'od_cilindrico','od_eixo':'od_eixo','od_add':'od_adicao','oe_esf':'oe_esferico','oe_cil':'oe_cilindrico','oe_eixo':'oe_eixo','oe_add':'oe_adicao','dnp_od':'dnp_od','dnp_oe':'dnp_oe','altura_od':'altura_od','altura_oe':'altura_oe','med_a':'medida_a','ponte':'ponte','diagonal_maior':'diagonal_maior','vertical':'vertical','tipo_lente':'tipo_lente','indice':'indice','material':'material','tratamento':'tratamento','arm_marca':'armacao_marca','arm_modelo':'armacao_modelo','arm_cor':'armacao_cor','arm_codigo':'armacao_codigo','valor':'valor','desconto':'desconto','entrada':'entrada','forma':'forma_pagamento'}
        for a,b in mapping.items():
            e=getattr(self,a)
            e.delete(0,'end')
            e.insert(0,str(r[b] if r[b] is not None else ''))
        self.set_text(self.descricao,r['descricao'])
        self.set_text(self.obs,r['observacoes'])

    def gerar_e_abrir_pdf(self, oid=None):
        if oid is None:
            if not self.os_id:
                messagebox.showwarning('OS', 'Salve a OS antes de gerar o PDF.')
                return
            oid = self.os_id

        conn = conectar()
        r = conn.execute('''SELECT os.*, c.nome cliente, c.cpf, c.telefone, c.whatsapp 
                            FROM ordens_servico os 
                            LEFT JOIN clientes c ON c.id=os.cliente_id 
                            WHERE os.id=?''', (oid,)).fetchone()
        conn.close()
        if not r:
            return

        caminho_pdf = os.path.join(tempfile.gettempdir(), f'OS_{oid}.pdf')
        m = lambda x: str(r[x] if r[x] is not None else '-')

        # Construção do documento PDF
        doc = SimpleDocTemplate(caminho_pdf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=10)
        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=12, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor('#1A365D'))
        normal_style = styles['Normal']

        # Cabeçalho
        elements.append(Paragraph("<b>ÓTICA</b>", title_style))
        elements.append(Paragraph(f"<b>ORDEM DE SERVIÇO Nº {r['id']}</b>", ParagraphStyle('OSNum', parent=styles['Heading2'], alignment=1, spaceAfter=15)))

        # Informações do Cliente e OS
        info_cliente = [
            [Paragraph(f"<b>Cliente:</b> {m('cliente')}", normal_style), Paragraph(f"<b>CPF:</b> {m('cpf')}", normal_style)],
            [Paragraph(f"<b>Telefone:</b> {m('telefone') or m('whatsapp')}", normal_style), Paragraph(f"<b>Data:</b> {m('data')}", normal_style)],
            [Paragraph(f"<b>Serviço:</b> {m('tipo_servico')}", normal_style), Paragraph(f"<b>Previsão:</b> {m('previsao_entrega')}", normal_style)]
        ]
        t_info = Table(info_cliente, colWidths=[300, 220])
        t_info.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_info)
        elements.append(Spacer(1, 10))

        # Tabela Receita / Grau
        elements.append(Paragraph("<b>RECEITA / GRAU</b>", subtitle_style))
        dados_receita = [
            ['Olho', 'ESF', 'CIL', 'EIXO', 'ADD'],
            ['OD (Direito)', m('od_esferico'), m('od_cilindrico'), m('od_eixo'), m('od_adicao')],
            ['OE (Esquerdo)', m('oe_esferico'), m('oe_cilindrico'), m('oe_eixo'), m('oe_adicao')]
        ]
        t_receita = Table(dados_receita, colWidths=[100, 105, 105, 105, 105])
        t_receita.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        elements.append(t_receita)
        elements.append(Spacer(1, 10))

        # Medidas da Montagem
        elements.append(Paragraph("<b>MEDIDAS DA MONTAGEM</b>", subtitle_style))
        dados_medidas = [
            [f"DNP OD: {m('dnp_od')}", f"DNP OE: {m('dnp_oe')}", f"Altura OD: {m('altura_od')}", f"Altura OE: {m('altura_oe')}"],
            [f"Medida A: {m('medida_a')}", f"Ponte: {m('ponte')}", f"Diag. Maior: {m('diagonal_maior')}", f"Vertical: {m('vertical')}"]
        ]
        t_medidas = Table(dados_medidas, colWidths=[130, 130, 130, 130])
        t_medidas.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
        elements.append(t_medidas)
        elements.append(Spacer(1, 10))

        # Lentes e Armação
        elements.append(Paragraph("<b>LENTES E ARMAÇÃO</b>", subtitle_style))
        dados_lentes = [
            [f"Tipo Lente: {m('tipo_lente')}", f"Índice: {m('indice')}", f"Material: {m('material')}", f"Tratamento: {m('tratamento')}"],
            [f"Marca: {m('armacao_marca')}", f"Modelo: {m('armacao_modelo')}", f"Cor: {m('armacao_cor')}", f"Código: {m('armacao_codigo')}"]
        ]
        t_lentes = Table(dados_lentes, colWidths=[130, 130, 130, 130])
        t_lentes.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
        elements.append(t_lentes)
        elements.append(Spacer(1, 10))

        # Valores
        elements.append(Paragraph("<b>VALORES</b>", subtitle_style))
        dados_valores = [
            [f"Valor: R$ {r['valor'] or 0:.2f}", f"Desconto: R$ {r['desconto'] or 0:.2f}", f"Total: R$ {r['total'] or 0:.2f}"],
            [f"Entrada: R$ {r['entrada'] or 0:.2f}", f"Saldo: R$ {r['saldo'] or 0:.2f}", f"Pagamento: {m('forma_pagamento')}"]
        ]
        t_valores = Table(dados_valores, colWidths=[170, 170, 180])
        t_valores.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_valores)
        
        if r['observacoes']:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Observações:</b> {m('observacoes')}", normal_style))

        # Assinatura
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("________________________________________", ParagraphStyle('Ass1', alignment=1)))
        elements.append(Paragraph("Assinatura do Cliente", ParagraphStyle('Ass2', alignment=1)))

        doc.build(elements)

        # Abre o PDF gerado no leitor padrão do Windows/Linux/Mac para impressão
        try:
            os.startfile(caminho_pdf)
        except AttributeError:
            import subprocess
            subprocess.run(['open' if os.name == 'posix' else 'xdg-open', caminho_pdf])