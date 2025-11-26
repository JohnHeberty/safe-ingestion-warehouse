"""
Interface de linha de comando (CLI) para o sistema de ingestão.
"""

import argparse
import sys
from pathlib import Path
from sqlalchemy import create_engine

from csv_ingestion import CsvToDatabaseLoader


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema robusto de ingestão de CSV em banco de dados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Análise dry-run (não insere dados)
  python cli.py \\
    --csv data/produtos.csv \\
    --db postgresql://user:pass@localhost:5432/mydb \\
    --schema public \\
    --table produtos \\
    --dry-run

  # Inserção real com replace
  python cli.py \\
    --csv data/produtos.csv \\
    --db postgresql://user:pass@localhost:5432/mydb \\
    --schema public \\
    --table produtos \\
    --if-exists replace \\
    --chunk-size 5000

  # Criar tabela automaticamente
  python cli.py \\
    --csv data/novos_dados.csv \\
    --db postgresql://user:pass@localhost:5432/mydb \\
    --schema analytics \\
    --table novos_dados \\
    --create-table

  # Com deduplicação
  python cli.py \\
    --csv data/clientes.csv \\
    --db postgresql://user:pass@localhost:5432/mydb \\
    --schema crm \\
    --table clientes \\
    --dedup-columns id email
        """
    )
    
    # Argumentos obrigatórios
    parser.add_argument(
        "--csv",
        required=True,
        help="Caminho do arquivo CSV"
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Connection string do banco (ex: postgresql://user:pass@host:port/db)"
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Schema do banco de dados"
    )
    parser.add_argument(
        "--table",
        required=True,
        help="Nome da tabela"
    )
    
    # Argumentos opcionais
    parser.add_argument(
        "--if-exists",
        choices=["fail", "replace", "append"],
        default="append",
        help="Estratégia se a tabela existir (default: append)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10000,
        help="Tamanho dos chunks para inserção (default: 10000)"
    )
    parser.add_argument(
        "--error-strategy",
        choices=["fail_fast", "collect_errors"],
        default="fail_fast",
        help="Estratégia de tratamento de erros (default: fail_fast)"
    )
    parser.add_argument(
        "--csv-separator",
        default=",",
        help="Separador do CSV (default: ,)"
    )
    parser.add_argument(
        "--csv-encoding",
        default="utf-8",
        help="Encoding do CSV (default: utf-8)"
    )
    parser.add_argument(
        "--create-table",
        action="store_true",
        help="Criar tabela automaticamente se não existir"
    )
    parser.add_argument(
        "--dedup-columns",
        nargs="+",
        help="Colunas para deduplicação (ex: --dedup-columns id email)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Desabilitar validação de tipos"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executar em modo dry-run (não insere dados)"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Apenas analisar o CSV e sugerir schema"
    )
    
    args = parser.parse_args()
    
    # Valida se o CSV existe
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ Erro: Arquivo CSV não encontrado: {args.csv}")
        sys.exit(1)
    
    try:
        # Cria engine do SQLAlchemy
        print(f"🔌 Conectando ao banco de dados...")
        engine = create_engine(args.db)
        
        # Testa conexão
        with engine.connect() as conn:
            print(f"✓ Conexão estabelecida com sucesso\n")
        
        # Cria o loader
        loader = CsvToDatabaseLoader(
            engine=engine,
            csv_path=args.csv,
            schema=args.schema,
            table_name=args.table,
            if_exists=args.if_exists,
            chunk_size=args.chunk_size,
            error_strategy=args.error_strategy,
            csv_separator=args.csv_separator,
            csv_encoding=args.csv_encoding,
            create_table=args.create_table,
            dedup_columns=args.dedup_columns,
            validate_types=not args.no_validate,
        )
        
        # Executa conforme modo
        if args.analyze_only:
            print("📊 Modo: ANÁLISE APENAS\n")
            loader.analyze_csv()
            loader.suggest_sql_schema()
        else:
            report = loader.run(dry_run=args.dry_run)
            
            # Salva relatório
            if not args.dry_run:
                report_path = csv_path.parent / f"{args.table}_ingestion_report.json"
                from csv_ingestion.utils import save_report_to_file
                save_report_to_file(report.to_dict(), str(report_path))
        
        print("\n✅ Processo concluído com sucesso!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
