"""
Testes de integração para o CsvToDatabaseLoader.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from csv_ingestion import CsvToDatabaseLoader


@pytest.fixture
def sqlite_engine():
    """Cria um engine SQLite em memória para testes."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def sample_csv(tmp_path):
    """Cria um CSV de exemplo para testes."""
    csv_path = tmp_path / "test_data.csv"
    
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "nome": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "idade": [25, 30, 35, 28, 42],
        "salario": [5000.50, 6000.75, 7500.00, 5500.25, 8000.00],
        "ativo": [True, True, False, True, False],
    })
    
    df.to_csv(csv_path, index=False)
    return str(csv_path)


class TestCsvToDatabaseLoader:
    """Testes de integração para CsvToDatabaseLoader."""
    
    def test_analyze_csv(self, sqlite_engine, sample_csv):
        """Testa análise de CSV."""
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
        )
        
        analyses = loader.analyze_csv()
        
        assert len(analyses) == 5
        assert "id" in analyses
        assert "nome" in analyses
        assert analyses["id"].sql_type_suggested in ["SMALLINT", "INTEGER", "BIGINT"]
        assert "VARCHAR" in analyses["nome"].sql_type_suggested or analyses["nome"].sql_type_suggested == "TEXT"
    
    def test_suggest_sql_schema(self, sqlite_engine, sample_csv):
        """Testa geração de DDL."""
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
        )
        
        ddl = loader.suggest_sql_schema()
        
        assert "CREATE TABLE" in ddl
        assert "test_table" in ddl
        assert "id" in ddl
        assert "nome" in ddl
    
    def test_dry_run(self, sqlite_engine, sample_csv):
        """Testa execução em dry-run."""
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            create_table=True,
        )
        
        report = loader.run(dry_run=True)
        
        assert report.dry_run is True
        assert report.total_rows_csv == 5
        assert report.rows_inserted == 0
        assert len(report.column_analyses) == 5
        
        # Verifica que a tabela NÃO foi criada
        inspector = inspect(sqlite_engine)
        tables = inspector.get_table_names()
        assert "test_table" not in tables
    
    def test_insert_with_create_table(self, sqlite_engine, sample_csv):
        """Testa inserção com criação de tabela."""
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            create_table=True,
        )
        
        report = loader.run(dry_run=False)
        
        assert report.rows_inserted == 5
        
        # Verifica que a tabela foi criada
        inspector = inspect(sqlite_engine)
        tables = inspector.get_table_names()
        assert "test_table" in tables
        
        # Verifica dados
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM test_table"))
            count = result.scalar()
            assert count == 5
    
    def test_insert_append(self, sqlite_engine, sample_csv):
        """Testa inserção com modo append."""
        # Primeira inserção
        loader1 = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            if_exists="append",
            create_table=True,
        )
        loader1.run(dry_run=False)
        
        # Segunda inserção (append)
        loader2 = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            if_exists="append",
        )
        report = loader2.run(dry_run=False)
        
        # Deve ter 10 linhas (5 + 5)
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM test_table"))
            count = result.scalar()
            assert count == 10
    
    def test_insert_replace(self, sqlite_engine, sample_csv):
        """Testa inserção com modo replace."""
        # Primeira inserção
        loader1 = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            if_exists="append",
            create_table=True,
        )
        loader1.run(dry_run=False)
        
        # Segunda inserção (replace)
        loader2 = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=sample_csv,
            schema="main",
            table_name="test_table",
            if_exists="replace",
        )
        report = loader2.run(dry_run=False)
        
        # Deve ter apenas 5 linhas (substituiu)
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM test_table"))
            count = result.scalar()
            assert count == 5
    
    def test_deduplication(self, sqlite_engine, tmp_path):
        """Testa deduplicação."""
        # CSV com duplicatas
        csv_path = tmp_path / "dup_data.csv"
        df = pd.DataFrame({
            "id": [1, 1, 2, 2, 3],
            "nome": ["A", "A", "B", "B", "C"],
        })
        df.to_csv(csv_path, index=False)
        
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=str(csv_path),
            schema="main",
            table_name="test_dedup",
            create_table=True,
            dedup_columns=["id"],
        )
        
        report = loader.run(dry_run=False)
        
        # Deve ter apenas 3 linhas (removeu duplicatas)
        assert report.rows_inserted == 3
    
    def test_chunk_insertion(self, sqlite_engine, tmp_path):
        """Testa inserção em chunks."""
        # CSV maior
        csv_path = tmp_path / "large_data.csv"
        df = pd.DataFrame({
            "id": range(1, 101),
            "valor": range(100, 200),
        })
        df.to_csv(csv_path, index=False)
        
        loader = CsvToDatabaseLoader(
            engine=sqlite_engine,
            csv_path=str(csv_path),
            schema="main",
            table_name="test_chunks",
            create_table=True,
            chunk_size=25,  # 4 chunks
        )
        
        report = loader.run(dry_run=False)
        
        assert report.rows_inserted == 100
        
        # Verifica dados
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM test_chunks"))
            count = result.scalar()
            assert count == 100
