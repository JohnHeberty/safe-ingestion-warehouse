"""
Exemplo 5: Apenas análise (sem inserção)
"""

from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("EXEMPLO 5: ANÁLISE EXPLORATÓRIA (SEM INSERÇÃO)")
print("=" * 80)

loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/dados_desconhecidos.csv",
    schema="temp",
    table_name="analise",
)

# Método 1: Analisar CSV
print("\n📊 ANÁLISE DAS COLUNAS:\n")
column_analyses = loader.analyze_csv()

# Mostra informações detalhadas
for col_name, analysis in column_analyses.items():
    print(f"\nColuna: {col_name}")
    print(f"  Tipo Pandas:     {analysis.pandas_dtype}")
    print(f"  Tipo SQL:        {analysis.sql_type_suggested}")
    print(f"  Nulos:           {analysis.null_count} ({analysis.null_percentage:.1f}%)")
    print(f"  Valores únicos:  {analysis.unique_count}")
    print(f"  Amostra:         {analysis.sample_values[:3]}")

# Método 2: Sugerir DDL
print("\n\n📋 DDL SUGERIDO:\n")
ddl = loader.suggest_sql_schema()

# Não executa inserção - apenas análise!
print("\n✅ Análise concluída. Nenhum dado foi inserido.")
