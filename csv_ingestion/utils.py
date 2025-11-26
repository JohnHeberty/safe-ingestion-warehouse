"""
Funções utilitárias para o sistema de ingestão.
"""

import logging
import json
from typing import Dict, Any
from pathlib import Path


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configura um logger estruturado.
    
    Args:
        name: Nome do logger
        level: Nível de logging
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Formato estruturado
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def print_report(report_dict: Dict[str, Any], title: str = "RELATÓRIO DE INGESTÃO"):
    """
    Imprime um relatório formatado.
    
    Args:
        report_dict: Dicionário com dados do relatório
        title: Título do relatório
    """
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)
    
    print(json.dumps(report_dict, indent=2, ensure_ascii=False, default=str))
    
    print("=" * 80 + "\n")


def print_column_analysis(analyses: list):
    """
    Imprime análise de colunas de forma tabular.
    
    Args:
        analyses: Lista de análises de colunas
    """
    print("\n" + "-" * 120)
    print(f"{'COLUNA':<25} | {'TIPO PANDAS':<15} | {'TIPO SQL':<20} | {'NULOS':<8} | {'ÚNICOS':<8} | {'SAMPLE'}")
    print("-" * 120)
    
    for analysis in analyses:
        null_pct = f"{analysis['null_percentage']:.1f}%"
        sample = str(analysis['sample_values'][:3])[:30]
        
        print(
            f"{analysis['name']:<25} | "
            f"{analysis['pandas_dtype']:<15} | "
            f"{analysis['sql_type_suggested']:<20} | "
            f"{null_pct:<8} | "
            f"{analysis['unique_count']:<8} | "
            f"{sample}"
        )
    
    print("-" * 120 + "\n")


def save_report_to_file(report_dict: Dict[str, Any], output_path: str):
    """
    Salva relatório em arquivo JSON.
    
    Args:
        report_dict: Dicionário com dados do relatório
        output_path: Caminho do arquivo de saída
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Relatório salvo em: {output_path}")


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.1f}s"
    
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    
    return f"{hours}h {remaining_minutes}m {remaining_seconds:.0f}s"
