# 🏗️ Arquitetura do Sistema de Ingestão

## Visão Geral

Este documento descreve a arquitetura do sistema profissional de ingestão de CSV em banco de dados.

---

## 🎯 Objetivos de Design

1. **Robustez**: Zero erros em produção através de validação extensiva
2. **Modularidade**: Componentes independentes e testáveis
3. **Extensibilidade**: Fácil adicionar novos tipos e validadores
4. **Observabilidade**: Logging e relatórios detalhados
5. **Usabilidade**: API simples e intuitiva

---

## 📦 Componentes Principais

### 1. **Models** (`models.py`)
Define estruturas de dados usando `dataclasses`:
- `IngestionConfig`: Configuração da ingestão
- `ColumnAnalysis`: Análise de uma coluna
- `ValidationError`: Erro de validação
- `ValidationResult`: Resultado da validação
- `IngestionReport`: Relatório completo

**Responsabilidades**:
- Estruturar dados
- Validação básica de tipos
- Conversão para dict/JSON

### 2. **Type Inference** (`type_inference.py`)
Inferência inteligente de tipos Pandas → SQL.

**Classes**:
- `TypeInference`: Classe principal com métodos estáticos

**Funcionalidades**:
- Mapeamento Pandas → SQL
- Análise estatística de colunas
- Geração de DDL
- Otimização de tipos (ex: SMALLINT vs INTEGER vs BIGINT)

**Algoritmo de Inferência**:
```
1. Detectar dtype do Pandas
2. Se object → tentar converter para numérico/datetime/boolean
3. Se numérico → otimizar tipo baseado em range
4. Se string → calcular tamanho e sugerir VARCHAR ou TEXT
5. Retornar tipo SQL otimizado
```

### 3. **Validators** (`validators.py`)
Validação de dados antes da inserção.

**Classes**:
- `DataValidator`: Validador principal

**Estratégias**:
- `fail_fast`: Para no primeiro erro
- `collect_errors`: Coleta todos os erros

**Validações por Tipo**:
- Integer: Conversão + range check
- Float: Conversão numérica
- Boolean: Valores válidos
- Timestamp: Conversão datetime
- String: Tamanho máximo (VARCHAR)

### 4. **Loader** (`loader.py`)
Classe principal orquestradora.

**Classe**: `CsvToDatabaseLoader`

**Pipeline de Execução**:
```
run() → 
  ├─ 1. _read_csv()
  ├─ 2. _analyze_csv()
  ├─ 3. _generate_ddl()
  ├─ 4. _check_table_exists()
  │    ├─ Se existe → _validate_against_db_schema()
  │    └─ Se não existe → _create_table() (se configurado)
  ├─ 5. _validate_data() (se habilitado)
  ├─ 6. _deduplicate() (se configurado)
  └─ 7. _insert_data() (se não dry-run)
```

**Responsabilidades**:
- Orquestração do pipeline
- Logging estruturado
- Controle de transações
- Geração de relatórios

### 5. **Utils** (`utils.py`)
Funções utilitárias.

**Funções**:
- `setup_logger()`: Configuração de logging
- `print_report()`: Impressão formatada
- `print_column_analysis()`: Tabela de análise
- `save_report_to_file()`: Salvar em JSON
- `format_duration()`: Formatação de tempo

### 6. **CLI** (`cli.py`)
Interface de linha de comando.

**Funcionalidades**:
- Parsing de argumentos
- Validação de parâmetros
- Tratamento de exceções
- Help text detalhado

---

## 🔄 Fluxo de Dados

```
CSV File
   ↓
[Leitura] → Pandas DataFrame
   ↓
[Análise] → ColumnAnalysis (para cada coluna)
   ↓
[Inferência] → Tipos SQL sugeridos
   ↓
[DDL] → CREATE TABLE statement
   ↓
[Validação] → ValidationResult + DataFrame válido/inválido
   ↓
[Deduplicação] → DataFrame único
   ↓
[Inserção em Chunks] → Database
   ↓
[Relatório] → IngestionReport
```

---

## 🧩 Padrões de Design

### 1. **Strategy Pattern**
Usado para estratégias de erro:
```python
ErrorStrategy.FAIL_FAST
ErrorStrategy.COLLECT_ERRORS
```

### 2. **Factory Pattern**
Criação de análises de colunas:
```python
TypeInference.analyze_column(series, name)
```

### 3. **Builder Pattern**
Configuração do loader:
```python
CsvToDatabaseLoader(
    engine=engine,
    csv_path=path,
    ...
)
```

### 4. **Template Method**
Pipeline de execução no `run()`:
```python
def run(self, dry_run):
    self._read_csv()
    self._analyze_csv()
    ...
```

---

## 🔌 Pontos de Extensão

### Adicionar novo tipo SQL
Em `type_inference.py`:
```python
PANDAS_TO_SQL_MAPPING = {
    "novo_tipo_pandas": "NOVO_TIPO_SQL",
    ...
}
```

### Adicionar nova validação
Em `validators.py`:
```python
@classmethod
def _validate_novo_tipo(cls, series, column_name, sql_type):
    # Implementar validação
    return errors
```

### Adicionar novo database
Driver específico em `requirements.txt`:
```txt
# Oracle
cx_Oracle>=8.0.0
```

---

## 📊 Diagrama de Classes

```
┌─────────────────────┐
│ CsvToDatabaseLoader │
└──────────┬──────────┘
           │
           ├───uses──→ ┌──────────────┐
           │           │TypeInference │
           │           └──────────────┘
           │
           ├───uses──→ ┌──────────────┐
           │           │DataValidator │
           │           └──────────────┘
           │
           └───uses──→ ┌──────────────────┐
                       │ Models (dataclass)│
                       └──────────────────┘
```

---

## 🚀 Performance

### Otimizações Implementadas
1. **Chunked Insertion**: Evita memory overflow
2. **Type Optimization**: Usa tipos menores quando possível
3. **Lazy Validation**: Só valida se configurado
4. **Batch Operations**: SQLAlchemy method='multi'

### Benchmarks Esperados
- **10k rows**: ~1-2 segundos
- **100k rows**: ~10-15 segundos
- **1M rows**: ~90-120 segundos

(Varia conforme hardware e latência de rede)

---

## 🔒 Segurança

### Práticas Implementadas
1. **Prepared Statements**: SQLAlchemy protege contra SQL injection
2. **Validation**: Todos os dados validados antes de inserção
3. **Transaction Control**: Rollback automático em caso de erro
4. **Schema Validation**: Verifica compatibilidade com tabela existente

---

## 📝 Logging

### Níveis de Log
- `INFO`: Progresso normal (padrão)
- `WARNING`: Avisos não-críticos
- `ERROR`: Erros de execução
- `DEBUG`: Informações detalhadas (desenvolvimento)

### Estrutura de Log
```
YYYY-MM-DD HH:MM:SS | module | LEVEL | message
```

---

## 🧪 Testabilidade

### Estratégia de Testes
1. **Unit Tests**: Cada componente isolado
2. **Integration Tests**: Pipeline completo
3. **Fixtures**: SQLite em memória para testes

### Cobertura Alvo
- Mínimo: 80%
- Ideal: 90%+

---

## 🔮 Melhorias Futuras

1. **Parallel Loading**: Inserção paralela para grandes volumes
2. **UPSERT Support**: INSERT ... ON CONFLICT
3. **Primary Key Detection**: Detecção automática de PKs
4. **Schema Evolution**: Detectar mudanças e sugerir ALTER TABLE
5. **Cloud Storage**: Suporte a S3, GCS, Azure Blob
6. **Streaming**: Processamento de CSVs maiores que memória
7. **Compression**: Suporte a CSV.gz, CSV.zip
8. **Multi-file**: Ingestão de múltiplos CSVs em batch

---

## 📚 Referências

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Última atualização**: 2024-11-26
