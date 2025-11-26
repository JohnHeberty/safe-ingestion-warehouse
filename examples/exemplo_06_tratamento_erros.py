"""
Exemplo 6: Tratamento de erros
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("EXEMPLO 6: TRATAMENTO DE ERROS")
print("=" * 80)

# Cenário A: Fail Fast (para no primeiro erro)
print("\n📌 Cenário A: FAIL FAST\n")

loader_fail_fast = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/dados_com_erros.csv",
    schema="test",
    table_name="teste_fail_fast",
    error_strategy="fail_fast",  # ← Para no primeiro erro
)

try:
    report = loader_fail_fast.run(dry_run=True)
except ValueError as e:
    print(f"❌ Erro capturado (esperado): {e}")


# Cenário B: Collect Errors (coleta todos os erros)
print("\n\n📌 Cenário B: COLLECT ERRORS\n")

loader_collect = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/dados_com_erros.csv",
    schema="test",
    table_name="teste_collect_errors",
    error_strategy="collect_errors",  # ← Coleta todos os erros
)

report = loader_collect.run(dry_run=True)

if report.validation_result and not report.validation_result.is_valid:
    print(f"\n⚠️  Erros encontrados:")
    print(f"   Total de erros: {len(report.validation_result.errors)}")
    print(f"   Linhas válidas: {report.validation_result.valid_rows_count}")
    print(f"   Linhas inválidas: {report.validation_result.invalid_rows_count}")
    
    print(f"\n   Primeiros 5 erros:")
    for error in report.validation_result.errors[:5]:
        print(f"   - Linha {error.row_index}, coluna '{error.column}': {error.error_message}")
    
    print(f"\n   💡 As linhas válidas seriam inseridas.")
    print(f"   💡 As linhas inválidas seriam salvas em: dados_com_erros_invalid_rows.csv")
