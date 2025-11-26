"""
Módulo de validação de dados antes da inserção.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .models import ValidationResult, ValidationError, ColumnAnalysis, ErrorStrategy
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Classe responsável por validar dados antes da inserção no banco.
    """

    @classmethod
    def validate_dataframe(
        cls,
        df: pd.DataFrame,
        column_analyses: Dict[str, ColumnAnalysis],
        error_strategy: ErrorStrategy = ErrorStrategy.FAIL_FAST
    ) -> Tuple[ValidationResult, pd.DataFrame, pd.DataFrame]:
        """
        Valida um DataFrame completo contra os tipos esperados.
        
        Args:
            df: DataFrame a ser validado
            column_analyses: Análises de colunas com tipos esperados
            error_strategy: Estratégia de tratamento de erros
            
        Returns:
            Tupla com (ValidationResult, df_valid, df_invalid)
        """
        validation_result = ValidationResult(
            is_valid=True,
            valid_rows_count=0,
            invalid_rows_count=0
        )
        
        invalid_row_indices = set()
        
        # Valida cada coluna
        for col_name, analysis in column_analyses.items():
            if col_name not in df.columns:
                logger.warning(f"Coluna '{col_name}' esperada mas não encontrada no DataFrame")
                continue
            
            series = df[col_name]
            errors = cls._validate_column(series, col_name, analysis)
            
            for error in errors:
                validation_result.add_error(error)
                invalid_row_indices.add(error.row_index)
                
                # Se fail_fast, para no primeiro erro
                if error_strategy == ErrorStrategy.FAIL_FAST:
                    logger.error(f"Erro de validação (fail_fast): {error.error_message}")
                    # Retorna tudo como inválido
                    return validation_result, pd.DataFrame(), df
        
        # Separa linhas válidas e inválidas
        if invalid_row_indices:
            mask = df.index.isin(invalid_row_indices)
            df_invalid = df[mask].copy()
            df_valid = df[~mask].copy()
            validation_result.valid_rows_count = len(df_valid)
            validation_result.invalid_rows_count = len(df_invalid)
        else:
            df_valid = df.copy()
            df_invalid = pd.DataFrame()
            validation_result.valid_rows_count = len(df_valid)
            validation_result.is_valid = True
        
        return validation_result, df_valid, df_invalid

    @classmethod
    def _validate_column(
        cls,
        series: pd.Series,
        column_name: str,
        analysis: ColumnAnalysis
    ) -> List[ValidationError]:
        """
        Valida uma coluna específica.
        
        Args:
            series: Série a ser validada
            column_name: Nome da coluna
            analysis: Análise da coluna com tipo esperado
            
        Returns:
            Lista de erros de validação encontrados
        """
        errors = []
        sql_type = analysis.sql_type_suggested.upper()
        
        # Remove espaços e pega o tipo base
        sql_type_base = sql_type.split("(")[0].strip()
        
        # Valida baseado no tipo SQL esperado
        if sql_type_base in ["BIGINT", "INTEGER", "SMALLINT"]:
            errors.extend(cls._validate_integer(series, column_name, sql_type))
        elif sql_type_base in ["DOUBLE PRECISION", "REAL", "NUMERIC", "DECIMAL"]:
            errors.extend(cls._validate_float(series, column_name, sql_type))
        elif sql_type_base == "BOOLEAN":
            errors.extend(cls._validate_boolean(series, column_name, sql_type))
        elif sql_type_base == "TIMESTAMP":
            errors.extend(cls._validate_timestamp(series, column_name, sql_type))
        elif sql_type_base in ["VARCHAR", "TEXT"]:
            errors.extend(cls._validate_string(series, column_name, sql_type))
        
        return errors

    @classmethod
    def _validate_integer(
        cls,
        series: pd.Series,
        column_name: str,
        sql_type: str
    ) -> List[ValidationError]:
        """Valida coluna inteira."""
        errors = []
        
        for idx, value in series.items():
            if pd.isna(value):
                continue  # Null é permitido (a menos que seja NOT NULL, mas isso é checado no DB)
            
            try:
                # Tenta converter para inteiro
                int_value = int(value)
                
                # Verifica se não perdeu informação (ex: 3.5 -> 3)
                if float(value) != float(int_value):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        value=value,
                        expected_type=sql_type,
                        error_message=f"Valor '{value}' não é um inteiro válido (tem parte decimal)"
                    ))
                    continue
                
                # Verifica limites baseado no tipo
                if "SMALLINT" in sql_type:
                    if not (-32768 <= int_value <= 32767):
                        errors.append(ValidationError(
                            row_index=idx,
                            column=column_name,
                            value=value,
                            expected_type=sql_type,
                            error_message=f"Valor {value} fora do range de SMALLINT (-32768 a 32767)"
                        ))
                elif "INTEGER" in sql_type and "BIG" not in sql_type:
                    if not (-2147483648 <= int_value <= 2147483647):
                        errors.append(ValidationError(
                            row_index=idx,
                            column=column_name,
                            value=value,
                            expected_type=sql_type,
                            error_message=f"Valor {value} fora do range de INTEGER"
                        ))
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    row_index=idx,
                    column=column_name,
                    value=value,
                    expected_type=sql_type,
                    error_message=f"Não foi possível converter '{value}' para {sql_type}"
                ))
        
        return errors

    @classmethod
    def _validate_float(
        cls,
        series: pd.Series,
        column_name: str,
        sql_type: str
    ) -> List[ValidationError]:
        """Valida coluna float."""
        errors = []
        
        for idx, value in series.items():
            if pd.isna(value):
                continue
            
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    row_index=idx,
                    column=column_name,
                    value=value,
                    expected_type=sql_type,
                    error_message=f"Não foi possível converter '{value}' para {sql_type}"
                ))
        
        return errors

    @classmethod
    def _validate_boolean(
        cls,
        series: pd.Series,
        column_name: str,
        sql_type: str
    ) -> List[ValidationError]:
        """Valida coluna booleana."""
        errors = []
        valid_bool_values = {
            True, False, 1, 0, "1", "0",
            "true", "false", "True", "False",
            "t", "f", "T", "F",
            "yes", "no", "Yes", "No"
        }
        
        for idx, value in series.items():
            if pd.isna(value):
                continue
            
            if value not in valid_bool_values:
                errors.append(ValidationError(
                    row_index=idx,
                    column=column_name,
                    value=value,
                    expected_type=sql_type,
                    error_message=f"Valor '{value}' não é um boolean válido"
                ))
        
        return errors

    @classmethod
    def _validate_timestamp(
        cls,
        series: pd.Series,
        column_name: str,
        sql_type: str
    ) -> List[ValidationError]:
        """Valida coluna timestamp."""
        errors = []
        
        for idx, value in series.items():
            if pd.isna(value):
                continue
            
            try:
                pd.to_datetime(value)
            except:
                errors.append(ValidationError(
                    row_index=idx,
                    column=column_name,
                    value=value,
                    expected_type=sql_type,
                    error_message=f"Não foi possível converter '{value}' para TIMESTAMP"
                ))
        
        return errors

    @classmethod
    def _validate_string(
        cls,
        series: pd.Series,
        column_name: str,
        sql_type: str
    ) -> List[ValidationError]:
        """Valida coluna string."""
        errors = []
        
        # Extrai o tamanho máximo se for VARCHAR
        max_length = None
        if "VARCHAR" in sql_type:
            try:
                max_length = int(sql_type.split("(")[1].split(")")[0])
            except:
                pass
        
        if max_length:
            for idx, value in series.items():
                if pd.isna(value):
                    continue
                
                str_value = str(value)
                if len(str_value) > max_length:
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        value=value,
                        expected_type=sql_type,
                        error_message=f"String de tamanho {len(str_value)} excede máximo de {max_length}"
                    ))
        
        return errors
