"""
Testes para o módulo de inferência de tipos.
"""

import pytest
import pandas as pd
import numpy as np
from csv_ingestion.type_inference import TypeInference


class TestTypeInference:
    """Testes para TypeInference."""
    
    def test_infer_integer_types(self):
        """Testa inferência de tipos inteiros."""
        # SMALLINT range
        series_small = pd.Series([1, 100, -100, 32767])
        assert TypeInference.infer_sql_type(series_small, "test") == "SMALLINT"
        
        # INTEGER range
        series_int = pd.Series([1, 100000, -100000, 2147483647])
        assert TypeInference.infer_sql_type(series_int, "test") == "INTEGER"
        
        # BIGINT range
        series_big = pd.Series([1, 10000000000, -10000000000])
        assert TypeInference.infer_sql_type(series_big, "test") == "BIGINT"
    
    def test_infer_float_types(self):
        """Testa inferência de tipos float."""
        series = pd.Series([1.5, 2.7, 3.14159, -5.5])
        sql_type = TypeInference.infer_sql_type(series, "test")
        assert sql_type == "DOUBLE PRECISION"
    
    def test_infer_boolean_types(self):
        """Testa inferência de tipos booleanos."""
        series = pd.Series([True, False, True, False])
        assert TypeInference.infer_sql_type(series, "test") == "BOOLEAN"
    
    def test_infer_datetime_types(self):
        """Testa inferência de tipos datetime."""
        series = pd.Series(pd.date_range("2024-01-01", periods=5))
        assert TypeInference.infer_sql_type(series, "test") == "TIMESTAMP"
    
    def test_infer_string_types(self):
        """Testa inferência de tipos string."""
        # String curta -> VARCHAR
        series_short = pd.Series(["abc", "def", "ghi"])
        sql_type = TypeInference.infer_sql_type(series_short, "test")
        assert "VARCHAR" in sql_type
        
        # String longa -> TEXT
        series_long = pd.Series(["x" * 300, "y" * 400])
        sql_type = TypeInference.infer_sql_type(series_long, "test", max_varchar_length=255)
        assert sql_type == "TEXT"
    
    def test_infer_numeric_from_object(self):
        """Testa inferência de numéricos que vêm como object."""
        # Inteiros como string
        series_int = pd.Series(["1", "2", "3", "100"])
        sql_type = TypeInference.infer_sql_type(series_int, "test")
        assert sql_type in ["SMALLINT", "INTEGER", "BIGINT"]
        
        # Floats como string
        series_float = pd.Series(["1.5", "2.7", "3.14"])
        sql_type = TypeInference.infer_sql_type(series_float, "test")
        assert sql_type == "DOUBLE PRECISION"
    
    def test_analyze_column(self):
        """Testa análise completa de coluna."""
        series = pd.Series([1, 2, 3, None, 5, 6, 7, 8, 9, 10])
        analysis = TypeInference.analyze_column(series, "test_col")
        
        assert analysis.name == "test_col"
        assert analysis.total_rows == 10
        assert analysis.null_count == 1
        assert analysis.null_percentage == 10.0
        assert analysis.unique_count == 9  # 9 valores únicos (excluindo None)
        assert analysis.min_value == 1.0
        assert analysis.max_value == 10.0
    
    def test_generate_ddl(self):
        """Testa geração de DDL."""
        # Cria análises fictícias
        from csv_ingestion.models import ColumnAnalysis
        
        analyses = {
            "id": ColumnAnalysis(
                name="id",
                pandas_dtype="int64",
                sql_type_suggested="INTEGER",
                null_count=0,
                null_percentage=0.0,
                total_rows=100,
                unique_count=100,
            ),
            "nome": ColumnAnalysis(
                name="nome",
                pandas_dtype="object",
                sql_type_suggested="VARCHAR(50)",
                null_count=5,
                null_percentage=5.0,
                total_rows=100,
                unique_count=95,
            ),
        }
        
        ddl = TypeInference.generate_ddl("test_table", "public", analyses)
        
        assert "CREATE TABLE" in ddl
        assert '"public"."test_table"' in ddl
        assert '"id" INTEGER NOT NULL' in ddl
        assert '"nome" VARCHAR(50) NULL' in ddl
