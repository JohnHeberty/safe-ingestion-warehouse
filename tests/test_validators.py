"""
Testes para o módulo de validação.
"""

import pytest
import pandas as pd
from csv_ingestion.validators import DataValidator
from csv_ingestion.models import ColumnAnalysis, ErrorStrategy, ValidationError


class TestDataValidator:
    """Testes para DataValidator."""
    
    def test_validate_integer_success(self):
        """Testa validação bem-sucedida de inteiros."""
        series = pd.Series([1, 2, 3, 4, 5])
        errors = DataValidator._validate_integer(series, "test_col", "INTEGER")
        assert len(errors) == 0
    
    def test_validate_integer_with_null(self):
        """Testa que nulls são permitidos."""
        series = pd.Series([1, 2, None, 4, 5])
        errors = DataValidator._validate_integer(series, "test_col", "INTEGER")
        assert len(errors) == 0
    
    def test_validate_integer_fail(self):
        """Testa validação que deve falhar."""
        series = pd.Series([1, 2, "abc", 4, 5])
        errors = DataValidator._validate_integer(series, "test_col", "INTEGER")
        assert len(errors) == 1
        assert errors[0].value == "abc"
    
    def test_validate_integer_range_smallint(self):
        """Testa validação de range para SMALLINT."""
        # Dentro do range
        series_ok = pd.Series([100, -100, 32767, -32768])
        errors = DataValidator._validate_integer(series_ok, "test_col", "SMALLINT")
        assert len(errors) == 0
        
        # Fora do range
        series_fail = pd.Series([100000])
        errors = DataValidator._validate_integer(series_fail, "test_col", "SMALLINT")
        assert len(errors) == 1
    
    def test_validate_float_success(self):
        """Testa validação de floats."""
        series = pd.Series([1.5, 2.7, 3.14])
        errors = DataValidator._validate_float(series, "test_col", "DOUBLE PRECISION")
        assert len(errors) == 0
    
    def test_validate_float_fail(self):
        """Testa validação de float que deve falhar."""
        series = pd.Series([1.5, "not_a_number", 3.14])
        errors = DataValidator._validate_float(series, "test_col", "DOUBLE PRECISION")
        assert len(errors) == 1
    
    def test_validate_boolean_success(self):
        """Testa validação de booleanos."""
        series = pd.Series([True, False, 1, 0, "true", "false"])
        errors = DataValidator._validate_boolean(series, "test_col", "BOOLEAN")
        assert len(errors) == 0
    
    def test_validate_boolean_fail(self):
        """Testa validação de boolean que deve falhar."""
        series = pd.Series([True, False, "maybe"])
        errors = DataValidator._validate_boolean(series, "test_col", "BOOLEAN")
        assert len(errors) == 1
        assert errors[0].value == "maybe"
    
    def test_validate_timestamp_success(self):
        """Testa validação de timestamps."""
        series = pd.Series(["2024-01-01", "2024-12-31", "2024-06-15 10:30:00"])
        errors = DataValidator._validate_timestamp(series, "test_col", "TIMESTAMP")
        assert len(errors) == 0
    
    def test_validate_timestamp_fail(self):
        """Testa validação de timestamp que deve falhar."""
        series = pd.Series(["2024-01-01", "not_a_date"])
        errors = DataValidator._validate_timestamp(series, "test_col", "TIMESTAMP")
        assert len(errors) == 1
    
    def test_validate_varchar_length(self):
        """Testa validação de tamanho de VARCHAR."""
        series = pd.Series(["abc", "def", "ghi"])
        errors = DataValidator._validate_string(series, "test_col", "VARCHAR(3)")
        assert len(errors) == 0
        
        # String muito longa
        series_long = pd.Series(["abcdefghij"])
        errors = DataValidator._validate_string(series_long, "test_col", "VARCHAR(5)")
        assert len(errors) == 1
    
    def test_validate_dataframe_fail_fast(self):
        """Testa validação de DataFrame com estratégia fail_fast."""
        df = pd.DataFrame({
            "col1": [1, 2, "invalid", 4],
            "col2": ["a", "b", "c", "d"]
        })
        
        analyses = {
            "col1": ColumnAnalysis(
                name="col1",
                pandas_dtype="int64",
                sql_type_suggested="INTEGER",
                null_count=0,
                null_percentage=0.0,
                total_rows=4,
                unique_count=4,
            ),
            "col2": ColumnAnalysis(
                name="col2",
                pandas_dtype="object",
                sql_type_suggested="TEXT",
                null_count=0,
                null_percentage=0.0,
                total_rows=4,
                unique_count=4,
            ),
        }
        
        result, df_valid, df_invalid = DataValidator.validate_dataframe(
            df, analyses, ErrorStrategy.FAIL_FAST
        )
        
        assert not result.is_valid
        assert len(df_valid) == 0  # Nenhuma linha válida no fail_fast
        assert len(df_invalid) == 4  # Todas inválidas
    
    def test_validate_dataframe_collect_errors(self):
        """Testa validação de DataFrame com estratégia collect_errors."""
        df = pd.DataFrame({
            "col1": [1, 2, "invalid", 4],
            "col2": ["a", "b", "c", "d"]
        })
        
        analyses = {
            "col1": ColumnAnalysis(
                name="col1",
                pandas_dtype="int64",
                sql_type_suggested="INTEGER",
                null_count=0,
                null_percentage=0.0,
                total_rows=4,
                unique_count=4,
            ),
            "col2": ColumnAnalysis(
                name="col2",
                pandas_dtype="object",
                sql_type_suggested="TEXT",
                null_count=0,
                null_percentage=0.0,
                total_rows=4,
                unique_count=4,
            ),
        }
        
        result, df_valid, df_invalid = DataValidator.validate_dataframe(
            df, analyses, ErrorStrategy.COLLECT_ERRORS
        )
        
        assert not result.is_valid
        assert len(df_valid) == 3  # 3 linhas válidas
        assert len(df_invalid) == 1  # 1 linha inválida
        assert len(result.errors) == 1
