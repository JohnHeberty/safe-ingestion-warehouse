# 🚀 Sistema Profissional de Ingestão de CSV em Banco de Dados

Um micro-sistema robusto e de nível empresarial para ingestão de dados CSV em bancos de dados, com validação de tipos, geração de DDL, tratamento de erros e logging estruturado.

---

## ✨ Funcionalidades

✅ **Análise automática de CSV**
- Detecção inteligente de tipos de dados
- Inferência de tipos SQL (otimizado para PostgreSQL)
- Estatísticas detalhadas de cada coluna

✅ **Geração de DDL**
- CREATE TABLE automático baseado na estrutura do CSV
- Sugestão de tipos SQL adequados
- Suporte a NOT NULL baseado em análise

✅ **Validação robusta**
- Validação de tipos antes da inserção
- Duas estratégias: fail_fast ou collect_errors
- Relatório detalhado de erros
- Salvamento de linhas inválidas em arquivo separado

✅ **Inserção confiável**
- Inserção em chunks configuráveis
- Controle transacional
- Suporte a if_exists: fail/replace/append
- Tratamento elegante de erros

✅ **Deduplicação**
- Remoção de duplicatas por colunas configuráveis
- Manutenção do primeiro registro

✅ **Modo Dry-Run**
- Testa todo o pipeline sem inserir dados
- Validação completa em modo seguro

✅ **Logging estruturado**
- Logs detalhados de cada etapa
- Relatórios em JSON
- Métricas de performance

---

## 📦 Instalação

### Pré-requisitos

- Python 3.8+
- Banco de dados (PostgreSQL recomendado)

### Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 🎯 Uso Rápido

### Exemplo 1: Uso básico

```python
from sqlalchemy import create_engine
from csv_ingestion import CsvToDatabaseLoader

# Conectar ao banco
engine = create_engine("postgresql+psycopg2://user:pass@localhost:5432/db")

# Criar loader
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/produtos.csv",
    schema="amb_rotas",
    table_name="jenks_produtos",
    if_exists="append",
    chunk_size=10000,
)

# Executar dry-run (análise)
loader.run(dry_run=True)

# Executar inserção real
report = loader.run(dry_run=False)
```

### Exemplo 2: Criar tabela automaticamente

```python
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/novos_dados.csv",
    schema="analytics",
    table_name="dados_novos",
    create_table=True,  # ← Cria a tabela automaticamente
)

report = loader.run(dry_run=False)
```

### Exemplo 3: Replace (TRUNCATE + INSERT)

```python
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/matriz_cargas.csv",
    schema="matriz_cargas_codemge",
    table_name="id_matriz_duto_comprimento_uf",
    if_exists="replace",  # ← Trunca antes de inserir
)

report = loader.run(dry_run=False)
```

### Exemplo 4: Deduplicação

```python
loader = CsvToDatabaseLoader(
    engine=engine,
    csv_path="data/clientes.csv",
    schema="crm",
    table_name="clientes",
    dedup_columns=["cpf", "email"],  # Remove duplicatas
)

report = loader.run(dry_run=False)
```

### Exemplo 5: Apenas análise

```python
# Analisar estrutura do CSV
column_analyses = loader.analyze_csv()

# Sugerir DDL
ddl = loader.suggest_sql_schema()
print(ddl)
```

---

## 🖥️ Uso via CLI

O sistema também oferece uma interface de linha de comando:

```bash
# Dry-run (análise)
python cli.py \
  --csv data/produtos.csv \
  --db postgresql://user:pass@localhost:5432/mydb \
  --schema public \
  --table produtos \
  --dry-run

# Inserção real
python cli.py \
  --csv data/produtos.csv \
  --db postgresql://user:pass@localhost:5432/mydb \
  --schema public \
  --table produtos \
  --if-exists append \
  --chunk-size 10000

# Criar tabela automaticamente
python cli.py \
  --csv data/novos_dados.csv \
  --db postgresql://user:pass@localhost:5432/mydb \
  --schema analytics \
  --table novos_dados \
  --create-table

# Com deduplicação
python cli.py \
  --csv data/clientes.csv \
  --db postgresql://user:pass@localhost:5432/mydb \
  --schema crm \
  --table clientes \
  --dedup-columns id email

# Apenas análise
python cli.py \
  --csv data/dados.csv \
  --db postgresql://user:pass@localhost:5432/mydb \
  --schema temp \
  --table analise \
  --analyze-only
```

---

## 📁 Estrutura do Projeto

```
SQL_INSERT/
├── csv_ingestion/          # Módulo principal
│   ├── __init__.py
│   ├── loader.py           # Classe CsvToDatabaseLoader
│   ├── models.py           # Modelos de dados
│   ├── type_inference.py   # Inferência de tipos
│   ├── validators.py       # Validação de dados
│   └── utils.py            # Utilitários
├── examples/               # Exemplos de uso
│   ├── exemplo_01_basico.py
│   ├── exemplo_02_criar_tabela.py
│   ├── exemplo_03_replace.py
│   ├── exemplo_04_deduplicacao.py
│   ├── exemplo_05_apenas_analise.py
│   └── exemplo_06_tratamento_erros.py
├── tests/                  # Testes unitários e integração
│   ├── conftest.py
│   ├── test_type_inference.py
│   ├── test_validators.py
│   └── test_integration.py
├── data/                   # Diretório para CSVs
├── cli.py                  # Interface CLI
├── requirements.txt        # Dependências
└── README.md              # Este arquivo
```

---

## ⚙️ Configurações Disponíveis

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `engine` | Engine | - | SQLAlchemy engine (obrigatório) |
| `csv_path` | str | - | Caminho do CSV (obrigatório) |
| `schema` | str | - | Schema do banco (obrigatório) |
| `table_name` | str | - | Nome da tabela (obrigatório) |
| `if_exists` | str | "append" | fail/replace/append |
| `chunk_size` | int | 10000 | Tamanho dos chunks |
| `error_strategy` | str | "fail_fast" | fail_fast/collect_errors |
| `csv_separator` | str | "," | Separador do CSV |
| `csv_encoding` | str | "utf-8" | Encoding do CSV |
| `create_table` | bool | False | Criar tabela automaticamente |
| `dedup_columns` | List[str] | None | Colunas para deduplicação |
| `validate_types` | bool | True | Validar tipos antes de inserir |

---

## 🧪 Testes

Execute os testes com pytest:

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=csv_ingestion --cov-report=html

# Apenas testes específicos
pytest tests/test_type_inference.py
pytest tests/test_validators.py
pytest tests/test_integration.py
```

---

## 📊 Relatórios

O sistema gera relatórios detalhados em formato JSON:

```json
{
  "timestamp": "2024-11-26T10:30:00",
  "csv_path": "data/produtos.csv",
  "schema": "public",
  "table_name": "produtos",
  "total_rows_csv": 10000,
  "rows_inserted": 9950,
  "rows_failed": 50,
  "duration_seconds": 5.42,
  "column_analyses": [...],
  "validation_result": {...},
  "ddl_generated": "CREATE TABLE ...",
  "warnings": [...]
}
```

---

## 🔧 Inferência de Tipos

O sistema mapeia tipos Pandas para SQL:

| Pandas | SQL (PostgreSQL) |
|--------|------------------|
| int64 (pequeno) | SMALLINT |
| int64 (médio) | INTEGER |
| int64 (grande) | BIGINT |
| float64 | DOUBLE PRECISION |
| bool | BOOLEAN |
| datetime64 | TIMESTAMP |
| object (string curta) | VARCHAR(n) |
| object (string longa) | TEXT |

---

## ⚠️ Tratamento de Erros

### Estratégia: fail_fast
- Para no primeiro erro encontrado
- Lança exceção imediatamente
- Nenhum dado é inserido

### Estratégia: collect_errors
- Coleta todos os erros
- Insere apenas linhas válidas
- Salva linhas inválidas em CSV separado
- Gera relatório detalhado de erros

---

## 🎓 Exemplos Avançados

Confira a pasta `examples/` para casos de uso completos:

1. **exemplo_01_basico.py** - Uso básico com dry-run
2. **exemplo_02_criar_tabela.py** - Criação automática de tabela
3. **exemplo_03_replace.py** - Modo replace com validação
4. **exemplo_04_deduplicacao.py** - Deduplicação de registros
5. **exemplo_05_apenas_analise.py** - Análise exploratória
6. **exemplo_06_tratamento_erros.py** - Estratégias de erro

---

## 🤝 Contribuindo

Este é um projeto profissional pronto para uso em produção. Sugestões de melhoria:

- Suporte a outros bancos (MySQL, SQL Server, Oracle)
- Suporte a UPSERT (INSERT ... ON CONFLICT)
- Detecção automática de chaves primárias
- Parallel loading para grandes volumes
- Integração com Airflow/Prefect

---

## 📝 Licença

Este projeto é fornecido como exemplo de código profissional para engenharia de dados.

---

## 👨‍💻 Autor

Desenvolvido como sistema de ingestão de nível empresarial para pipelines de dados.

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os exemplos na pasta `examples/`
2. Consulte os testes em `tests/`
3. Revise a documentação inline (docstrings)

---

**🎯 Zero erros em produção!**
