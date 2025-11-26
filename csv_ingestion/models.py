"""
Modelos e estruturas de dados para o sistema de ingestão.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class IfExistsStrategy(str, Enum):
    """Estratégias para lidar com tabelas existentes."""
    FAIL = "fail"
    REPLACE = "replace"
    APPEND = "append"


class ErrorStrategy(str, Enum):
    """Estratégias para lidar com erros de validação."""
    FAIL_FAST = "fail_fast"
    COLLECT_ERRORS = "collect_errors"


@dataclass
class ColumnAnalysis:
    """
    Análise detalhada de uma coluna do CSV.
    
    Attributes:
        name: Nome da coluna
        pandas_dtype: Tipo detectado pelo Pandas
        sql_type_suggested: Tipo SQL sugerido
        null_count: Quantidade de valores nulos
        null_percentage: Percentual de valores nulos
        total_rows: Total de linhas analisadas
        unique_count: Quantidade de valores únicos (cardinalidade)
        sample_values: Amostra de valores da coluna
        min_value: Valor mínimo (se numérico)
        max_value: Valor máximo (se numérico)
        avg_length: Comprimento médio (se string)
        max_length: Comprimento máximo (se string)
    """
    name: str
    pandas_dtype: str
    sql_type_suggested: str
    null_count: int
    null_percentage: float
    total_rows: int
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_length: Optional[float] = None
    max_length: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "pandas_dtype": self.pandas_dtype,
            "sql_type_suggested": self.sql_type_suggested,
            "null_count": self.null_count,
            "null_percentage": round(self.null_percentage, 2),
            "total_rows": self.total_rows,
            "unique_count": self.unique_count,
            "sample_values": self.sample_values[:5],
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_length": round(self.avg_length, 2) if self.avg_length else None,
            "max_length": self.max_length,
        }


@dataclass
class ValidationError:
    """
    Representa um erro de validação encontrado.
    
    Attributes:
        row_index: Índice da linha com erro
        column: Nome da coluna
        value: Valor que causou o erro
        expected_type: Tipo esperado
        error_message: Mensagem de erro
    """
    row_index: int
    column: str
    value: Any
    expected_type: str
    error_message: str

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "row_index": self.row_index,
            "column": self.column,
            "value": str(self.value),
            "expected_type": self.expected_type,
            "error_message": self.error_message,
        }


@dataclass
class ValidationResult:
    """
    Resultado da validação de dados.
    
    Attributes:
        is_valid: Se todos os dados passaram na validação
        errors: Lista de erros encontrados
        valid_rows_count: Quantidade de linhas válidas
        invalid_rows_count: Quantidade de linhas inválidas
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    valid_rows_count: int = 0
    invalid_rows_count: int = 0

    def add_error(self, error: ValidationError):
        """Adiciona um erro à lista."""
        self.errors.append(error)
        self.invalid_rows_count += 1
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "is_valid": self.is_valid,
            "valid_rows_count": self.valid_rows_count,
            "invalid_rows_count": self.invalid_rows_count,
            "total_errors": len(self.errors),
            "errors": [e.to_dict() for e in self.errors[:100]],  # Limita a 100 erros no output
        }


@dataclass
class IngestionReport:
    """
    Relatório completo de uma operação de ingestão.
    
    Attributes:
        timestamp: Data/hora da ingestão
        csv_path: Caminho do arquivo CSV
        schema: Schema do banco de dados
        table_name: Nome da tabela
        total_rows_csv: Total de linhas no CSV
        rows_inserted: Linhas inseridas com sucesso
        rows_failed: Linhas que falharam
        duration_seconds: Duração da operação em segundos
        column_analyses: Análises das colunas
        validation_result: Resultado da validação
        ddl_generated: DDL gerado (se aplicável)
        dry_run: Se foi executado em modo dry-run
    """
    timestamp: datetime
    csv_path: str
    schema: str
    table_name: str
    total_rows_csv: int
    rows_inserted: int = 0
    rows_failed: int = 0
    duration_seconds: float = 0.0
    column_analyses: List[ColumnAnalysis] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    ddl_generated: Optional[str] = None
    dry_run: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "csv_path": self.csv_path,
            "schema": self.schema,
            "table_name": self.table_name,
            "total_rows_csv": self.total_rows_csv,
            "rows_inserted": self.rows_inserted,
            "rows_failed": self.rows_failed,
            "duration_seconds": round(self.duration_seconds, 2),
            "dry_run": self.dry_run,
            "column_analyses": [c.to_dict() for c in self.column_analyses],
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
            "ddl_generated": self.ddl_generated,
            "warnings": self.warnings,
        }


@dataclass
class IngestionConfig:
    """
    Configuração para operação de ingestão.
    
    Attributes:
        csv_path: Caminho do arquivo CSV
        schema: Schema do banco de dados
        table_name: Nome da tabela
        if_exists: Estratégia se a tabela existir
        chunk_size: Tamanho dos chunks para inserção
        error_strategy: Estratégia de tratamento de erros
        csv_separator: Separador do CSV
        csv_encoding: Encoding do CSV
        create_table: Se deve criar a tabela automaticamente
        dedup_columns: Colunas para deduplicação (opcional)
        validate_types: Se deve validar tipos antes de inserir
    """
    csv_path: str
    schema: str
    table_name: str
    if_exists: IfExistsStrategy = IfExistsStrategy.APPEND
    chunk_size: int = 10000
    error_strategy: ErrorStrategy = ErrorStrategy.FAIL_FAST
    csv_separator: str = ","
    csv_encoding: str = "utf-8"
    create_table: bool = False
    dedup_columns: Optional[List[str]] = None
    validate_types: bool = True
