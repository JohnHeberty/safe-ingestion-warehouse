"""
Exemplo 3: Replace (substituir dados) com validação
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("EXEMPLO 3: REPLACE (TRUNCATE + INSERT)")
print("=" * 80)

loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/matriz_cargas.csv",
    schema="matriz_cargas_codemge",
    table_name="id_matriz_duto_comprimento_uf",
    if_exists="replace",        # ← TRUNCA antes de inserir
    chunk_size=10000,
    validate_types=True,        # Valida tipos
    error_strategy="collect_errors",  # Coleta erros em vez de falhar imediatamente
)

print("\n⚠️  ATENÇÃO: Modo REPLACE irá TRUNCAR a tabela antes de inserir!\n")

# Executar
report = loader.run(dry_run=False)

print(f"\n✅ Dados substituídos com sucesso!")
print(f"   Linhas inseridas: {report.rows_inserted}")

if report.validation_result and not report.validation_result.is_valid:
    print(f"\n⚠️  Avisos de validação:")
    print(f"   Linhas válidas: {report.validation_result.valid_rows_count}")
    print(f"   Linhas inválidas: {report.validation_result.invalid_rows_count}")
    print(f"   (Linhas inválidas foram salvas em arquivo separado)")
