"""
Exemplo 4: Deduplicação e customização de CSV
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("EXEMPLO 4: DEDUPLICAÇÃO + CUSTOMIZAÇÃO CSV")
print("=" * 80)

loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/clientes.csv",
    schema="crm",
    table_name="clientes",
    if_exists="append",
    chunk_size=5000,
    
    # Customização do CSV
    csv_separator=";",          # Separador diferente
    csv_encoding="latin1",      # Encoding diferente
    
    # Deduplicação
    dedup_columns=["cpf", "email"],  # Remove duplicatas por CPF + Email
)

# Executar
report = loader.run(dry_run=False)

print(f"\n✅ Ingestão concluída!")
print(f"   Linhas inseridas: {report.rows_inserted}")
