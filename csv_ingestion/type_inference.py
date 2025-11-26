"""
Módulo para inferência de tipos Pandas -> SQL.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from .models import ColumnAnalysis


class TypeInference:
    """
    Classe responsável por inferir tipos SQL a partir de tipos Pandas.
    """

    # Mapeamento básico de tipos Pandas para SQL (Postgres)
    PANDAS_TO_SQL_MAPPING = {
        "int64": "BIGINT",
        "int32": "INTEGER",
        "int16": "SMALLINT",
        "int8": "SMALLINT",
        "float64": "DOUBLE PRECISION",
        "float32": "REAL",
        "bool": "BOOLEAN",
        "datetime64[ns]": "TIMESTAMP",
        "datetime64[ns, UTC]": "TIMESTAMP WITH TIME ZONE",
        "timedelta64[ns]": "INTERVAL",
        "object": "TEXT",
        "string": "TEXT",
        "category": "TEXT",
    }

    @classmethod
    def infer_sql_type(
        cls,
        series: pd.Series,
        column_name: str,
        max_varchar_length: int = 255
    ) -> str:
        """
        Infere o tipo SQL mais adequado para uma coluna.
        
        Args:
            series: Série do Pandas para análise
            column_name: Nome da coluna
            max_varchar_length: Tamanho máximo para VARCHAR antes de usar TEXT
            
        Returns:
            Tipo SQL sugerido como string
        """
        dtype_str = str(series.dtype)
        
        # Se for object, tenta inferir melhor
        if dtype_str == "object":
            return cls._infer_object_type(series, max_varchar_length)
        
        # Se for datetime
        if "datetime64" in dtype_str:
            return "TIMESTAMP"
        
        # Se for timedelta
        if "timedelta64" in dtype_str:
            return "INTERVAL"
        
        # Se for numérico inteiro, verifica se pode ser menor
        if dtype_str.startswith("int"):
            return cls._infer_integer_type(series)
        
        # Se for float, verifica precisão
        if dtype_str.startswith("float"):
            return cls._infer_float_type(series)
        
        # Se for boolean
        if dtype_str == "bool":
            return "BOOLEAN"
        
        # Fallback para o mapeamento padrão
        return cls.PANDAS_TO_SQL_MAPPING.get(dtype_str, "TEXT")

    @classmethod
    def _infer_object_type(cls, series: pd.Series, max_varchar_length: int) -> str:
        """
        Infere tipo SQL para colunas object (string ou misto).
        """
        # Remove nulos para análise
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return "TEXT"
        
        # Tenta converter para numérico
        try:
            numeric_converted = pd.to_numeric(non_null, errors="coerce")
            if numeric_converted.notna().all():
                # É numérico
                if (numeric_converted % 1 == 0).all():
                    # É inteiro
                    return cls._infer_integer_type(numeric_converted)
                else:
                    # É float
                    return "DOUBLE PRECISION"
        except:
            pass
        
        # Tenta converter para datetime
        try:
            datetime_converted = pd.to_datetime(non_null, errors="coerce")
            if datetime_converted.notna().all():
                return "TIMESTAMP"
        except:
            pass
        
        # Tenta converter para boolean
        if set(non_null.unique()).issubset({"True", "False", "true", "false", "T", "F", "1", "0", True, False, 1, 0}):
            return "BOOLEAN"
        
        # É string - calcula comprimento máximo
        max_len = non_null.astype(str).str.len().max()
        
        if max_len <= max_varchar_length:
            return f"VARCHAR({max_len})"
        else:
            return "TEXT"

    @classmethod
    def _infer_integer_type(cls, series: pd.Series) -> str:
        """
        Infere o melhor tipo inteiro baseado no range de valores.
        """
        min_val = series.min()
        max_val = series.max()
        
        # SMALLINT: -32768 to 32767
        if -32768 <= min_val and max_val <= 32767:
            return "SMALLINT"
        # INTEGER: -2147483648 to 2147483647
        elif -2147483648 <= min_val and max_val <= 2147483647:
            return "INTEGER"
        else:
            return "BIGINT"

    @classmethod
    def _infer_float_type(cls, series: pd.Series) -> str:
        """
        Infere o melhor tipo float baseado na precisão.
        """
        # Verifica se há valores com precisão alta
        # Para simplificar, sempre usa DOUBLE PRECISION
        return "DOUBLE PRECISION"

    @classmethod
    def analyze_column(cls, series: pd.Series, column_name: str) -> ColumnAnalysis:
        """
        Faz uma análise completa de uma coluna.
        
        Args:
            series: Série do Pandas
            column_name: Nome da coluna
            
        Returns:
            Objeto ColumnAnalysis com todas as informações
        """
        total_rows = len(series)
        null_count = series.isna().sum()
        null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
        unique_count = series.nunique()
        
        # Infere tipo SQL
        sql_type = cls.infer_sql_type(series, column_name)
        
        # Amostra de valores (não-nulos)
        sample_values = series.dropna().head(10).tolist()
        
        # Estatísticas específicas por tipo
        min_value = None
        max_value = None
        avg_length = None
        max_length = None
        
        non_null = series.dropna()
        
        if len(non_null) > 0:
            # Para numéricos
            if pd.api.types.is_numeric_dtype(series):
                try:
                    min_value = float(non_null.min())
                    max_value = float(non_null.max())
                except:
                    pass
            
            # Para strings
            elif series.dtype == "object" or series.dtype == "string":
                try:
                    str_series = non_null.astype(str)
                    lengths = str_series.str.len()
                    avg_length = float(lengths.mean())
                    max_length = int(lengths.max())
                except:
                    pass
        
        return ColumnAnalysis(
            name=column_name,
            pandas_dtype=str(series.dtype),
            sql_type_suggested=sql_type,
            null_count=int(null_count),
            null_percentage=float(null_percentage),
            total_rows=total_rows,
            unique_count=int(unique_count),
            sample_values=sample_values,
            min_value=min_value,
            max_value=max_value,
            avg_length=avg_length,
            max_length=max_length,
        )

    @classmethod
    def generate_ddl(
        cls,
        table_name: str,
        schema: str,
        column_analyses: Dict[str, ColumnAnalysis],
        primary_key: Optional[str] = None
    ) -> str:
        """
        Gera DDL (CREATE TABLE) baseado nas análises de coluna.
        
        Args:
            table_name: Nome da tabela
            schema: Schema do banco
            column_analyses: Dicionário de análises de colunas
            primary_key: Nome da coluna de chave primária (opcional)
            
        Returns:
            String com o SQL de CREATE TABLE
        """
        full_table_name = f'"{schema}"."{table_name}"'
        
        lines = [f"CREATE TABLE {full_table_name} ("]
        
        column_defs = []
        for col_name, analysis in column_analyses.items():
            null_clause = "NOT NULL" if analysis.null_count == 0 else "NULL"
            col_def = f'    "{col_name}" {analysis.sql_type_suggested} {null_clause}'
            column_defs.append(col_def)
        
        lines.append(",\n".join(column_defs))
        
        if primary_key:
            lines.append(f',\n    PRIMARY KEY ("{primary_key}")')
        
        lines.append("\n);")
        
        return "".join(lines)
