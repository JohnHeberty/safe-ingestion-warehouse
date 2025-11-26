"""
Exemplo 1: Uso básico com dry-run e execução real
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

# Configurar conexão com o banco
# Substitua com suas credenciais reais
DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"

# Criar engine
engine = create_engine(DATABASE_URL)

# Criar loader
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/jenks_produtos.csv",
    schema="amb_rotas",
    table_name="jenks_produtos",
    if_exists="append",        # ou "replace" ou "fail"
    chunk_size=10000,
)

print("=" * 80)
print("EXEMPLO 1: DRY-RUN + EXECUÇÃO REAL")
print("=" * 80)

# Etapa 1: Executar dry-run para análise
print("\n📊 Executando DRY-RUN para análise...\n")
report_dry = loader.run(dry_run=True)

# O dry-run mostra:
# - Análise das colunas
# - DDL sugerido
# - Validações
# Mas NÃO insere dados

input("\n✋ Pressione ENTER para continuar com a inserção real...")

# Etapa 2: Executar inserção real
print("\n💾 Executando INSERÇÃO REAL...\n")
report = loader.run(dry_run=False)

print(f"\n✅ Inserção concluída!")
print(f"   Linhas inseridas: {report.rows_inserted}")
print(f"   Duração: {report.duration_seconds:.2f}s")
