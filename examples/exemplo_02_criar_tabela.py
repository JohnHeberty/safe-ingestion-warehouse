"""
Exemplo 2: Criar tabela automaticamente
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("EXEMPLO 2: CRIAÇÃO AUTOMÁTICA DE TABELA")
print("=" * 80)

# Configurar para criar a tabela automaticamente
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/novos_dados.csv",
    schema="analytics",
    table_name="dados_novos",
    if_exists="fail",           # Falha se já existir
    create_table=True,          # ← CRIA AUTOMATICAMENTE
    chunk_size=5000,
)

# Primeiro, ver o DDL que será usado
print("\n📋 DDL que será criado:\n")
ddl = loader.suggest_sql_schema()

input("\n✋ A tabela será criada. Pressione ENTER para continuar...")

# Executar (vai criar a tabela e inserir)
report = loader.run(dry_run=False)

print(f"\n✅ Tabela criada e dados inseridos!")
print(f"   Total: {report.rows_inserted} linhas")
