"""
CSV to Database Ingestion System
==================================

Um sistema robusto e profissional para ingestão de dados CSV em bancos de dados,
com validação de tipos, geração de DDL, e tratamento de erros.

Author: Sistema de Ingestão Profissional
Version: 1.0.0
"""

from .loader import CsvToDatabaseLoader
from .models import (
    ColumnAnalysis,
    ValidationResult,
    IngestionReport,
    IngestionConfig,
)

__version__ = "1.0.0"
__all__ = [
    "CsvToDatabaseLoader",
    "ColumnAnalysis",
    "ValidationResult",
    "IngestionReport",
    "IngestionConfig",
]
