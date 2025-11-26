"""
QUICK START - Script de início rápido
======================================

Este script demonstra o uso mais simples do sistema.
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

# ========================================
# CONFIGURAÇÃO - EDITE AQUI!
# ========================================

# Sua connection string do banco de dados
# Exemplos:
# - PostgreSQL: "postgresql+psycopg2://usuario:senha@localhost:5432/banco"
# - SQLite: "sqlite:///test.db"
# - MySQL: "mysql+pymysql://usuario:senha@localhost:3306/banco"
DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"

# Caminho do seu CSV
CSV_PATH = "data/exemplo_produtos.csv"

# Schema e tabela
SCHEMA = "public"
TABLE_NAME = "produtos"

# ========================================
# EXECUÇÃO
# ========================================

if __name__ == "__main__":
    print("🚀 QUICK START - Sistema de Ingestão CSV\n")
    
    # 1. Criar engine
    print(f"📦 Conectando ao banco...")
    engine = create_engine(DATABASE_URL)
    
    # 2. Criar loader
    loader = CsvToDatabaseLoader(
        engine=engine,
        csv_path=CSV_PATH,
        schema=SCHEMA,
        table_name=TABLE_NAME,
        if_exists="replace",  # Troca para "append" se preferir
        create_table=True,    # Cria a tabela automaticamente
        chunk_size=10000,
    )
    
    # 3. Executar DRY-RUN primeiro (segurança)
    print(f"\n📊 Executando DRY-RUN (análise)...\n")
    report_dry = loader.run(dry_run=True)
    
    # 4. Perguntar se quer continuar
    print("\n" + "="*80)
    resposta = input("✋ Continuar com a inserção real? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        # 5. Executar inserção real
        print(f"\n💾 Executando INSERÇÃO REAL...\n")
        report = loader.run(dry_run=False)
        
        print("\n" + "="*80)
        print("✅ SUCESSO!")
        print(f"   CSV: {report.csv_path}")
        print(f"   Tabela: {report.schema}.{report.table_name}")
        print(f"   Linhas inseridas: {report.rows_inserted}")
        print(f"   Duração: {report.duration_seconds:.2f}s")
        print("="*80 + "\n")
    else:
        print("\n⚠️  Inserção cancelada pelo usuário.\n")
