import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "banco"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "otica.db"

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            nascimento TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            endereco TEXT,
            numero TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            observacoes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nome TEXT NOT NULL,
            categoria TEXT,
            marca TEXT,
            modelo TEXT,
            cor TEXT,
            tamanho TEXT,
            custo REAL DEFAULT 0,
            preco REAL DEFAULT 0,
            estoque INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_receita TEXT,
            medico TEXT,
            crm TEXT,
            od_esferico TEXT,
            od_cilindrico TEXT,
            od_eixo TEXT,
            od_dnp TEXT,
            od_altura TEXT,
            od_prisma TEXT,
            oe_esferico TEXT,
            oe_cilindrico TEXT,
            oe_eixo TEXT,
            oe_dnp TEXT,
            oe_altura TEXT,
            oe_prisma TEXT,
            adicao TEXT,
            observacoes TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)

    cur.execute("""
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
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS venda_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER,
            descricao TEXT NOT NULL,
            quantidade INTEGER DEFAULT 1,
            valor_unitario REAL DEFAULT 0,
            subtotal REAL DEFAULT 0,
            FOREIGN KEY(venda_id) REFERENCES vendas(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            cliente_id INTEGER,
            parcela INTEGER,
            vencimento TEXT,
            valor REAL,
            pago INTEGER DEFAULT 0,
            data_pagamento TEXT,
            FOREIGN KEY(venda_id) REFERENCES vendas(id),
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO usuarios (nome, usuario, senha)
        VALUES ('Administrador', 'admin', '1234')
    """)

    conn.commit()
    conn.close()
# --- ADICIONE ESTE BLOCO AO FINAL DO SEU DATABASE.PY ---

def criar_tabelas_caixa():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela para controlar a Abertura e Fechamento de cada Turno/Dia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TEXT DEFAULT CURRENT_TIMESTAMP,
            data_fechamento TEXT,
            saldo_inicial REAL DEFAULT 0,
            saldo_final REAL DEFAULT 0,
            status TEXT DEFAULT 'Aberto',
            usuario TEXT
        )
    """)

    # Tabela para Entradas (Suprimento) e Saídas (Sangria)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            motivo TEXT,
            data TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (caixa_id) REFERENCES caixa (id)
        )
    """)

    conn.commit()
    conn.close()