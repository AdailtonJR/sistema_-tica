import os
import sqlite3
from datetime import datetime
from tkinter import messagebox

def encontrar_banco_automatico(db_padrao="sistema_otica.db"):
    """Procura o arquivo do banco de dados na pasta atual ou subpastas se não achar de primeira."""
    if os.path.exists(db_padrao):
        return db_padrao
    
    # Lista de nomes comuns que o banco pode ter
    nomes_possiveis = [db_padrao, "banco.db", "sistema.db", "otica.db", "dados.db"]
    for nome in nomes_possiveis:
        if os.path.exists(nome):
            return nome
            
    # Varredura ampla na pasta e subpastas por arquivos .db
    for raiz, _, arquivos in os.walk("."):
        for arquivo in arquivos:
            if arquivo.endswith(".db") and "backup" not in arquivo.lower():
                return os.path.join(raiz, arquivo)
                
    return None

def realizar_backup_sqlite(db_path="sistema_otica.db", pasta_backup="backups", max_backups=10):
    """Cria cópia de segurança do SQLite de forma segura, mantendo os mais recentes e avisando na tela."""
    
    # Garante que acha o banco de dados correto
    db_real = encontrar_banco_automatico(db_path)
    
    if not db_real or not os.path.exists(db_real):
        print(f"[Backup] Arquivo de banco de dados não encontrado para backup.")
        return

    if not os.path.exists(pasta_backup):
        os.makedirs(pasta_backup)

    # Nomeia o arquivo com data e hora exatas
    data_hora = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    nome_base = os.path.splitext(os.path.basename(db_real))[0]
    nome_backup = f"backup_{nome_base}_{data_hora}.db"
    caminho_destino = os.path.join(pasta_backup, nome_backup)

    try:
        # Cópia segura usando a biblioteca nativa do SQLite
        conn_origem = sqlite3.connect(db_real)
        conn_destino = sqlite3.connect(caminho_destino)

        with conn_destino:
            conn_origem.backup(conn_destino)

        conn_destino.close()
        conn_origem.close()

        # Limpa backups antigos para não encher o HD
        _limpar_backups_antigos(pasta_backup, max_backups)

        # Aviso visual confirmando que o backup ocorreu
        messagebox.showinfo(
            "Backup Concluído",
            f"Cópia de segurança gerada com sucesso!\nSalvo em: {caminho_destino}"
        )

    except Exception as e:
        messagebox.showerror("Erro no Backup", f"Não foi possível gerar o backup:\n{e}")

def _limpar_backups_antigos(pasta_backup, max_backups):
    try:
        arquivos = [
            os.path.join(pasta_backup, f) 
            for f in os.listdir(pasta_backup) 
            if f.startswith("backup_") and f.endswith(".db")
        ]
        arquivos.sort(key=os.path.getmtime)

        while len(arquivos) > max_backups:
            arquivo_antigo = arquivos.pop(0)
            os.remove(arquivo_antigo)
    except Exception as e:
        print(f"Erro ao limpar backups: {e}")