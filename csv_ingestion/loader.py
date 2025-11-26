"""
Classe principal para ingestão de CSV em banco de dados.
"""

import pandas as pd
import time
import re
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from .models import (
    IngestionConfig,
    IngestionReport,
    ColumnAnalysis,
    ValidationResult,
    IfExistsStrategy,
    ErrorStrategy,
)
from .type_inference import TypeInference
from .validators import DataValidator
from .utils import setup_logger, print_report, print_column_analysis, format_duration

import logging


class CsvToDatabaseLoader:
    """
    Classe principal para carga robusta de CSV em banco de dados.
    
    Funcionalidades:
    - Análise de CSV e inferência de tipos
    - Geração de DDL (CREATE TABLE)
    - Validação de dados
    - Inserção em chunks com controle transacional
    - Modo dry-run
    - Logging estruturado
    - Relatórios detalhados
    
    Example:
        ```python
        from sqlalchemy import create_engine
        from csv_ingestion import CsvToDatabaseLoader
        
        engine = create_engine("postgresql://user:pass@host:port/db")
        
        loader = CsvToDatabaseLoader(
            engine=engine,
            csv_path="data/produtos.csv",
            schema="amb_rotas",
            table_name="jenks_produtos",
            if_exists="append",
            chunk_size=10000
        )
        
        # Dry-run para análise
        loader.run(dry_run=True)
        
        # Execução real
        report = loader.run(dry_run=False)
        ```
    """

    def __init__(
        self,
        engine: Engine,
        csv_path: str,
        schema: str,
        table_name: str,
        if_exists: str = "append",
        chunk_size: int = 10000,
        error_strategy: str = "fail_fast",
        csv_separator: str = ",",
        csv_encoding: str = "utf-8",
        create_table: bool = False,
        dedup_columns: Optional[List[str]] = None,
        validate_types: bool = True,
        log_level: int = logging.INFO,
    ):
        """
        Inicializa o loader.
        
        Args:
            engine: SQLAlchemy engine
            csv_path: Caminho do arquivo CSV
            schema: Schema do banco de dados
            table_name: Nome da tabela
            if_exists: Estratégia se tabela existir ("fail", "replace", "append")
            chunk_size: Tamanho dos chunks para inserção
            error_strategy: Estratégia de erros ("fail_fast", "collect_errors")
            csv_separator: Separador do CSV
            csv_encoding: Encoding do CSV
            create_table: Se deve criar tabela automaticamente
            dedup_columns: Colunas para deduplicação
            validate_types: Se deve validar tipos
            log_level: Nível de logging
        """
        self.engine = engine
        self.config = IngestionConfig(
            csv_path=csv_path,
            schema=schema,
            table_name=table_name,
            if_exists=IfExistsStrategy(if_exists),
            chunk_size=chunk_size,
            error_strategy=ErrorStrategy(error_strategy),
            csv_separator=csv_separator,
            csv_encoding=csv_encoding,
            create_table=create_table,
            dedup_columns=dedup_columns,
            validate_types=validate_types,
        )
        
        self.logger = setup_logger(__name__, log_level)
        self.df: Optional[pd.DataFrame] = None
        self.column_analyses: Dict[str, ColumnAnalysis] = {}
        self.ddl_generated: Optional[str] = None
        self.validation_result: Optional[ValidationResult] = None

    def run(self, dry_run: bool = False) -> IngestionReport:
        """
        Executa o processo completo de ingestão.
        
        Args:
            dry_run: Se True, executa tudo exceto a inserção real
            
        Returns:
            IngestionReport com detalhes da execução
        """
        start_time = time.time()
        
        self.logger.info("=" * 80)
        self.logger.info(f"INICIANDO INGESTÃO {'(DRY-RUN)' if dry_run else '(EXECUÇÃO REAL)'}")
        self.logger.info(f"CSV: {self.config.csv_path}")
        self.logger.info(f"Destino: {self.config.schema}.{self.config.table_name}")
        self.logger.info("=" * 80)
        
        report = IngestionReport(
            timestamp=datetime.now(),
            csv_path=self.config.csv_path,
            schema=self.config.schema,
            table_name=self.config.table_name,
            total_rows_csv=0,
            dry_run=dry_run,
        )
        
        try:
            # Etapa 1: Ler e analisar CSV
            self.logger.info("\n[1/6] Lendo e analisando CSV...")
            self._read_csv()
            self._analyze_csv()
            
            report.total_rows_csv = len(self.df)
            report.column_analyses = list(self.column_analyses.values())
            
            self.logger.info(f"✓ CSV lido: {len(self.df)} linhas, {len(self.df.columns)} colunas")
            
            # Etapa 2: Gerar DDL
            self.logger.info("\n[2/6] Gerando DDL sugerido...")
            self._generate_ddl()
            report.ddl_generated = self.ddl_generated
            
            print("\n" + "=" * 80)
            print("DDL SUGERIDO:")
            print("=" * 80)
            print(self.ddl_generated)
            print("=" * 80 + "\n")
            
            # Etapa 3: Verificar tabela existente
            self.logger.info("\n[3/6] Verificando tabela no banco...")
            table_exists = self._check_table_exists()
            
            if table_exists:
                self.logger.info(f"✓ Tabela {self.config.schema}.{self.config.table_name} já existe")
                self._validate_against_db_schema()
            else:
                self.logger.info(f"ℹ Tabela {self.config.schema}.{self.config.table_name} não existe")
                
                if self.config.create_table and not dry_run:
                    self.logger.info("  Criando tabela...")
                    self._create_table()
                    self.logger.info("✓ Tabela criada com sucesso")
                elif dry_run:
                    self.logger.info("  (dry-run) Tabela seria criada na execução real")
                else:
                    report.warnings.append("Tabela não existe e create_table=False")
                    self.logger.warning("⚠ Tabela não existe. Configure create_table=True ou crie manualmente")
            
            # Etapa 4: Validar dados (se habilitado)
            if self.config.validate_types:
                self.logger.info("\n[4/6] Validando tipos de dados...")
                self._validate_data()
                report.validation_result = self.validation_result
                
                if self.validation_result.is_valid:
                    self.logger.info(f"✓ Validação OK: {self.validation_result.valid_rows_count} linhas válidas")
                else:
                    self.logger.warning(
                        f"⚠ Validação com erros: {self.validation_result.valid_rows_count} válidas, "
                        f"{self.validation_result.invalid_rows_count} inválidas"
                    )
                    
                    if self.config.error_strategy == ErrorStrategy.FAIL_FAST:
                        raise ValueError(
                            f"Validação falhou (fail_fast): {len(self.validation_result.errors)} erros encontrados"
                        )
            else:
                self.logger.info("\n[4/6] Validação de tipos desabilitada (pulando...)")
            
            # Etapa 5: Deduplicação (se configurado)
            if self.config.dedup_columns:
                self.logger.info(f"\n[5/6] Deduplicando por {self.config.dedup_columns}...")
                original_count = len(self.df)
                self._deduplicate()
                dedup_count = original_count - len(self.df)
                self.logger.info(f"✓ Removidas {dedup_count} linhas duplicadas")
            else:
                self.logger.info("\n[5/6] Deduplicação não configurada (pulando...)")
            
            # Etapa 6: Inserir dados
            if not dry_run:
                self.logger.info(f"\n[6/6] Inserindo dados no banco...")
                rows_inserted = self._insert_data()
                report.rows_inserted = rows_inserted
                self.logger.info(f"✓ {rows_inserted} linhas inseridas com sucesso")
            else:
                self.logger.info(f"\n[6/6] DRY-RUN: Não inserindo dados")
                self.logger.info(f"  Seriam inseridas {len(self.df)} linhas em modo real")
            
            # Finalização
            duration = time.time() - start_time
            report.duration_seconds = duration
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"✅ INGESTÃO CONCLUÍDA {'(DRY-RUN)' if dry_run else 'COM SUCESSO'}")
            self.logger.info(f"Duração: {format_duration(duration)}")
            self.logger.info("=" * 80)
            
            # Imprime relatório resumido
            self._print_summary(report)
            
            return report
            
        except Exception as e:
            duration = time.time() - start_time
            report.duration_seconds = duration
            
            self.logger.error("\n" + "=" * 80)
            self.logger.error(f"❌ ERRO NA INGESTÃO")
            self.logger.error(f"Erro: {str(e)}")
            self.logger.error(f"Duração até falha: {format_duration(duration)}")
            self.logger.error("=" * 80)
            
            raise

    def _read_csv(self):
        """Lê o arquivo CSV com auto-detecção de separador."""
        csv_path = Path(self.config.csv_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {self.config.csv_path}")
        
        try:
            # Tenta com o separador configurado
            self.df = pd.read_csv(
                csv_path,
                sep=self.config.csv_separator,
                encoding=self.config.csv_encoding,
            )
            
            # Se tiver apenas 1 coluna, pode ser separador errado
            if len(self.df.columns) == 1:
                self.logger.warning(f"Apenas 1 coluna detectada com separador '{self.config.csv_separator}'. Tentando auto-detectar...")
                
                # Tenta detectar o separador correto
                separadores = [';', '\t', '|', ',']
                for sep in separadores:
                    try:
                        df_test = pd.read_csv(
                            csv_path,
                            sep=sep,
                            encoding=self.config.csv_encoding,
                            nrows=5
                        )
                        if len(df_test.columns) > 1:
                            self.logger.info(f"✓ Separador correto detectado: '{sep}'")
                            self.df = pd.read_csv(
                                csv_path,
                                sep=sep,
                                encoding=self.config.csv_encoding,
                            )
                            self.config.csv_separator = sep
                            break
                    except:
                        continue
            
            # Sanitiza nomes de colunas
            self.df.columns = self._sanitize_column_names(self.df.columns)
            
        except UnicodeDecodeError as e:
            # Tenta outros encodings
            self.logger.warning(f"Erro de encoding com '{self.config.csv_encoding}'. Tentando outros...")
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for enc in encodings:
                try:
                    self.df = pd.read_csv(
                        csv_path,
                        sep=self.config.csv_separator,
                        encoding=enc,
                    )
                    self.logger.info(f"✓ Encoding correto: '{enc}'")
                    self.config.csv_encoding = enc
                    break
                except:
                    continue
            else:
                raise ValueError(f"Não foi possível ler o CSV com nenhum encoding testado: {str(e)}")
        
        except Exception as e:
            raise ValueError(f"Erro ao ler CSV: {str(e)}")
    
    def _sanitize_column_names(self, columns):
        """Sanitiza nomes de colunas para evitar problemas no banco."""
        sanitized = []
        for col in columns:
            # Remove espaços extras
            col = str(col).strip()
            # Remove caracteres especiais problemáticos
            # Mas mantém underscore e hífen
            # col = re.sub(r'[^\w\s-]', '', col)
            sanitized.append(col)
        return sanitized

    def _analyze_csv(self):
        """Analisa o CSV e infere tipos."""
        self.column_analyses = {}
        
        for col_name in self.df.columns:
            analysis = TypeInference.analyze_column(self.df[col_name], col_name)
            self.column_analyses[col_name] = analysis

    def _generate_ddl(self):
        """Gera DDL para criar a tabela."""
        self.ddl_generated = TypeInference.generate_ddl(
            table_name=self.config.table_name,
            schema=self.config.schema,
            column_analyses=self.column_analyses,
        )

    def _check_table_exists(self) -> bool:
        """Verifica se a tabela existe no banco."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(schema=self.config.schema)
        return self.config.table_name in tables

    def _validate_against_db_schema(self):
        """Valida o schema do CSV contra o schema da tabela no banco."""
        try:
            metadata = MetaData()
            table = Table(
                self.config.table_name,
                metadata,
                autoload_with=self.engine,
                schema=self.config.schema
            )
            
            db_columns = {col.name: str(col.type) for col in table.columns}
            csv_columns = set(self.df.columns)
            
            # Colunas que existem no CSV mas não no DB
            extra_in_csv = csv_columns - set(db_columns.keys())
            if extra_in_csv:
                self.logger.warning(f"  ⚠ Colunas no CSV mas não na tabela: {extra_in_csv}")
            
            # Colunas que existem no DB mas não no CSV
            missing_in_csv = set(db_columns.keys()) - csv_columns
            if missing_in_csv:
                self.logger.warning(f"  ⚠ Colunas na tabela mas não no CSV: {missing_in_csv}")
            
            # Compara tipos (simplificado)
            for col_name in csv_columns.intersection(set(db_columns.keys())):
                csv_type = self.column_analyses[col_name].sql_type_suggested
                db_type = db_columns[col_name]
                
                if csv_type.split("(")[0] != db_type.split("(")[0]:
                    self.logger.warning(
                        f"  ⚠ Tipo diferente em '{col_name}': CSV={csv_type}, DB={db_type}"
                    )
        
        except Exception as e:
            self.logger.warning(f"  ⚠ Não foi possível validar schema: {str(e)}")

    def _create_table(self):
        """Cria a tabela no banco usando o DDL gerado."""
        with self.engine.begin() as conn:
            conn.execute(text(self.ddl_generated))

    def _validate_data(self):
        """Valida os dados antes da inserção."""
        self.validation_result, df_valid, df_invalid = DataValidator.validate_dataframe(
            df=self.df,
            column_analyses=self.column_analyses,
            error_strategy=self.config.error_strategy
        )
        
        # Se collect_errors, mantém apenas as linhas válidas
        if self.config.error_strategy == ErrorStrategy.COLLECT_ERRORS:
            if len(df_invalid) > 0:
                # Salva linhas inválidas para análise
                invalid_path = Path(self.config.csv_path).parent / f"{self.config.table_name}_invalid_rows.csv"
                df_invalid.to_csv(invalid_path, index=False)
                self.logger.warning(f"  Linhas inválidas salvas em: {invalid_path}")
            
            self.df = df_valid

    def _deduplicate(self):
        """Remove duplicatas baseado nas colunas configuradas."""
        if not self.config.dedup_columns:
            return
        
        # Verifica se todas as colunas existem
        missing_cols = set(self.config.dedup_columns) - set(self.df.columns)
        if missing_cols:
            self.logger.warning(f"  Colunas de dedup não encontradas: {missing_cols}")
            return
        
        self.df = self.df.drop_duplicates(subset=self.config.dedup_columns, keep='first')

    def _insert_data(self) -> int:
        """
        Insere dados no banco em chunks com retry automático.
        
        Returns:
            Número de linhas inseridas
        """
        total_inserted = 0
        total_chunks = (len(self.df) + self.config.chunk_size - 1) // self.config.chunk_size
        
        # Trata if_exists
        if self.config.if_exists == IfExistsStrategy.REPLACE:
            # Trunca a tabela primeiro
            self.logger.info(f"  Truncando tabela {self.config.schema}.{self.config.table_name}...")
            try:
                with self.engine.begin() as conn:
                    conn.execute(
                        text(f'TRUNCATE TABLE "{self.config.schema}"."{self.config.table_name}"')
                    )
            except Exception as e:
                self.logger.warning(f"  Erro ao truncar (tabela pode não existir): {str(e)}")
        
        # Insere em chunks
        for i, chunk_start in enumerate(range(0, len(self.df), self.config.chunk_size)):
            chunk_end = min(chunk_start + self.config.chunk_size, len(self.df))
            chunk_df = self.df.iloc[chunk_start:chunk_end]
            
            # Tenta inserir com retry
            max_retries = 3
            for retry in range(max_retries):
                try:
                    chunk_df.to_sql(
                        name=self.config.table_name,
                        schema=self.config.schema,
                        con=self.engine,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                    
                    total_inserted += len(chunk_df)
                    
                    self.logger.info(
                        f"  Chunk {i+1}/{total_chunks}: {len(chunk_df)} linhas "
                        f"({total_inserted}/{len(self.df)} total)"
                    )
                    break  # Sucesso, sai do retry loop
                    
                except ProgrammingError as e:
                    error_msg = str(e)
                    
                    # Erro de coluna não existente
                    if "não existe a coluna" in error_msg or "column" in error_msg.lower():
                        self.logger.error(f"  ❌ Erro de schema: {error_msg}")
                        self.logger.error(f"  💡 Colunas do DataFrame: {list(chunk_df.columns)}")
                        
                        # Se create_table está habilitado, tenta criar
                        if self.config.create_table:
                            self.logger.info("  🔧 Tentando criar tabela automaticamente...")
                            try:
                                self._create_table()
                                self.logger.info("  ✓ Tabela criada. Tentando inserir novamente...")
                                continue  # Retry
                            except Exception as create_error:
                                self.logger.error(f"  ❌ Erro ao criar tabela: {str(create_error)}")
                                raise
                        else:
                            raise
                    else:
                        # Outro erro de programação
                        if retry < max_retries - 1:
                            self.logger.warning(f"  ⚠️ Tentativa {retry+1}/{max_retries} falhou. Tentando novamente...")
                            time.sleep(1)  # Aguarda 1 segundo
                        else:
                            self.logger.error(f"  ❌ Erro no chunk {i+1} após {max_retries} tentativas: {error_msg}")
                            raise
                            
                except SQLAlchemyError as e:
                    if retry < max_retries - 1:
                        self.logger.warning(f"  ⚠️ Tentativa {retry+1}/{max_retries} falhou: {str(e)}")
                        time.sleep(1)
                    else:
                        self.logger.error(f"  ❌ Erro no chunk {i+1} após {max_retries} tentativas: {str(e)}")
                        raise
        
        return total_inserted

    def _print_summary(self, report: IngestionReport):
        """Imprime resumo do relatório."""
        print("\n" + "=" * 80)
        print(" RESUMO DA INGESTÃO")
        print("=" * 80)
        print(f"Timestamp:        {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"CSV:              {report.csv_path}")
        print(f"Destino:          {report.schema}.{report.table_name}")
        print(f"Total linhas CSV: {report.total_rows_csv}")
        print(f"Linhas inseridas: {report.rows_inserted}")
        print(f"Linhas falhadas:  {report.rows_failed}")
        print(f"Duração:          {format_duration(report.duration_seconds)}")
        print(f"Dry-run:          {'Sim' if report.dry_run else 'Não'}")
        
        if report.warnings:
            print(f"\n⚠ AVISOS ({len(report.warnings)}):")
            for warning in report.warnings:
                print(f"  - {warning}")
        
        print("=" * 80 + "\n")
        
        # Imprime análise de colunas
        print_column_analysis([c.to_dict() for c in report.column_analyses])

    # ========== Métodos de conveniência ==========

    def analyze_csv(self) -> Dict[str, ColumnAnalysis]:
        """
        Apenas analisa o CSV sem inserir dados.
        
        Returns:
            Dicionário de análises de colunas
        """
        self._read_csv()
        self._analyze_csv()
        
        print_column_analysis([c.to_dict() for c in self.column_analyses.values()])
        
        return self.column_analyses

    def suggest_sql_schema(self) -> str:
        """
        Apenas sugere o DDL sem executar nada.
        
        Returns:
            String com o DDL sugerido
        """
        if not self.column_analyses:
            self.analyze_csv()
        
        self._generate_ddl()
        
        print("\n" + "=" * 80)
        print("DDL SUGERIDO:")
        print("=" * 80)
        print(self.ddl_generated)
        print("=" * 80 + "\n")
        
        return self.ddl_generated
