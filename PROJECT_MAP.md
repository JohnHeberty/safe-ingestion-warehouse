# 📁 Mapa do Projeto - Sistema de Ingestão CSV

## 🗂️ Estrutura Completa

```
SQL_INSERT/
│
├── 📦 csv_ingestion/              # Módulo principal do sistema
│   ├── __init__.py                # Exports e versão
│   ├── loader.py                  # Classe CsvToDatabaseLoader (CORE)
│   ├── models.py                  # Dataclasses e enums
│   ├── type_inference.py          # Inferência Pandas → SQL
│   ├── validators.py              # Validação de dados
│   └── utils.py                   # Funções utilitárias
│
├── 📚 examples/                   # Exemplos práticos de uso
│   ├── exemplo_01_basico.py       # Dry-run + execução real
│   ├── exemplo_02_criar_tabela.py # Criação automática de tabela
│   ├── exemplo_03_replace.py      # Modo replace com validação
│   ├── exemplo_04_deduplicacao.py # Deduplicação de registros
│   ├── exemplo_05_apenas_analise.py # Análise exploratória
│   └── exemplo_06_tratamento_erros.py # Estratégias de erro
│
├── 🧪 tests/                      # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py                # Configuração pytest
│   ├── test_type_inference.py     # Testes de inferência
│   ├── test_validators.py         # Testes de validação
│   └── test_integration.py        # Testes de integração
│
├── 📊 data/                       # Diretório para CSVs
│   └── exemplo_produtos.csv       # CSV de exemplo
│
├── 🎮 Scripts e CLIs
│   ├── cli.py                     # Interface de linha de comando
│   ├── quick_start.py             # Script de início rápido
│   └── scripts.py                 # Scripts utilitários (install, test, etc)
│
├── 📖 Documentação
│   ├── README.md                  # Documentação principal ⭐
│   ├── ARCHITECTURE.md            # Design e arquitetura
│   ├── MIGRATION_GUIDE.md         # Guia de migração do df.to_sql()
│   ├── TROUBLESHOOTING.md         # Solução de problemas
│   ├── DIAGRAMS.md                # Diagramas em ASCII
│   ├── CHANGELOG.md               # Histórico de versões
│   └── PROJECT_MAP.md             # Este arquivo
│
├── ⚙️ Configurações
│   ├── requirements.txt           # Dependências Python
│   ├── setup.cfg                  # Configuração pytest/flake8/mypy
│   └── .gitignore                 # Arquivos ignorados pelo git
│
└── 🗃️ Outros
    └── memory-bank/               # Contexto do projeto (se aplicável)
```

---

## 🎯 Começar por Onde?

### Para Iniciantes
1. ✅ Leia o [README.md](README.md)
2. ✅ Execute o [quick_start.py](quick_start.py)
3. ✅ Teste o [exemplo_01_basico.py](examples/exemplo_01_basico.py)

### Para Usuários Migrando
1. ✅ Leia o [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. ✅ Teste com [dry_run=True](examples/exemplo_01_basico.py)
3. ✅ Consulte o [TROUBLESHOOTING.md](TROUBLESHOOTING.md) se necessário

### Para Desenvolvedores
1. ✅ Leia a [ARCHITECTURE.md](ARCHITECTURE.md)
2. ✅ Estude o [loader.py](csv_ingestion/loader.py)
3. ✅ Execute os testes: `pytest`
4. ✅ Veja os [DIAGRAMS.md](DIAGRAMS.md)

---

## 📦 Descrição dos Módulos

### 1. `csv_ingestion/loader.py` (790 linhas)
**Responsabilidade**: Orquestração do pipeline de ingestão

**Classes principais**:
- `CsvToDatabaseLoader`: Classe principal

**Métodos públicos**:
- `run(dry_run)`: Executa pipeline completo
- `analyze_csv()`: Apenas análise
- `suggest_sql_schema()`: Apenas DDL

**Métodos privados**:
- `_read_csv()`: Leitura do CSV
- `_analyze_csv()`: Análise de colunas
- `_generate_ddl()`: Geração de DDL
- `_check_table_exists()`: Verificação de tabela
- `_validate_data()`: Validação de dados
- `_deduplicate()`: Deduplicação
- `_insert_data()`: Inserção em chunks

---

### 2. `csv_ingestion/type_inference.py` (240 linhas)
**Responsabilidade**: Inferência de tipos Pandas → SQL

**Classes principais**:
- `TypeInference`: Inferência estática

**Métodos principais**:
- `infer_sql_type()`: Infere tipo SQL
- `analyze_column()`: Análise completa de coluna
- `generate_ddl()`: Gera CREATE TABLE

**Suporta**:
- INTEGER (SMALLINT, INTEGER, BIGINT)
- FLOAT (REAL, DOUBLE PRECISION)
- BOOLEAN
- TIMESTAMP
- VARCHAR/TEXT
- Conversão de object para tipos específicos

---

### 3. `csv_ingestion/validators.py` (280 linhas)
**Responsabilidade**: Validação de dados antes da inserção

**Classes principais**:
- `DataValidator`: Validador principal

**Métodos principais**:
- `validate_dataframe()`: Valida DF completo
- `_validate_integer()`: Valida inteiros + range
- `_validate_float()`: Valida floats
- `_validate_boolean()`: Valida booleanos
- `_validate_timestamp()`: Valida timestamps
- `_validate_string()`: Valida strings + tamanho

**Estratégias**:
- `fail_fast`: Para no primeiro erro
- `collect_errors`: Coleta todos os erros

---

### 4. `csv_ingestion/models.py` (220 linhas)
**Responsabilidade**: Estruturas de dados

**Dataclasses**:
- `IngestionConfig`: Configuração da ingestão
- `ColumnAnalysis`: Análise de uma coluna
- `ValidationError`: Erro de validação específico
- `ValidationResult`: Resultado da validação completa
- `IngestionReport`: Relatório final

**Enums**:
- `IfExistsStrategy`: fail/replace/append
- `ErrorStrategy`: fail_fast/collect_errors

---

### 5. `csv_ingestion/utils.py` (130 linhas)
**Responsabilidade**: Funções utilitárias

**Funções principais**:
- `setup_logger()`: Configura logging
- `print_report()`: Imprime relatório JSON
- `print_column_analysis()`: Tabela de análise
- `save_report_to_file()`: Salva em JSON
- `format_duration()`: Formata tempo

---

## 🧪 Cobertura de Testes

### `tests/test_type_inference.py`
- ✅ Inferência de inteiros (SMALLINT/INTEGER/BIGINT)
- ✅ Inferência de floats
- ✅ Inferência de booleanos
- ✅ Inferência de timestamps
- ✅ Inferência de strings (VARCHAR/TEXT)
- ✅ Conversão de object para numérico
- ✅ Análise completa de coluna
- ✅ Geração de DDL

### `tests/test_validators.py`
- ✅ Validação de inteiros (sucesso/falha)
- ✅ Validação de range (SMALLINT)
- ✅ Validação de floats
- ✅ Validação de booleanos
- ✅ Validação de timestamps
- ✅ Validação de tamanho VARCHAR
- ✅ Estratégia fail_fast
- ✅ Estratégia collect_errors

### `tests/test_integration.py`
- ✅ Análise de CSV
- ✅ Geração de DDL
- ✅ Dry-run completo
- ✅ Inserção com criação de tabela
- ✅ Modo append
- ✅ Modo replace
- ✅ Deduplicação
- ✅ Inserção em chunks

---

## 📚 Documentação

### [README.md](README.md) - COMECE AQUI
- Funcionalidades completas
- Instalação
- Exemplos de uso rápido
- Uso via CLI
- Configurações disponíveis
- Testes

### [ARCHITECTURE.md](ARCHITECTURE.md)
- Objetivos de design
- Componentes principais
- Fluxo de dados
- Padrões de design
- Pontos de extensão
- Performance
- Segurança

### [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- Comparação código antigo vs novo
- Exemplos de migração
- Tabela de equivalência
- Checklist de migração
- Caso de uso completo
- FAQ

### [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Erros de instalação
- Erros de conexão
- Erros de CSV
- Erros de validação
- Erros de inserção
- Performance
- Dicas gerais

### [DIAGRAMS.md](DIAGRAMS.md)
- Fluxo principal de execução
- Fluxo de inferência de tipos
- Fluxo de validação
- Arquitetura de classes
- Pipeline de dados
- Estados do sistema

### [CHANGELOG.md](CHANGELOG.md)
- Versão 1.0.0 (atual)
- Roadmap futuro
- Tipos de mudanças

---

## 🎮 Scripts Disponíveis

### Via CLI ([cli.py](cli.py))
```bash
python cli.py --csv data.csv --db postgresql://... --schema public --table my_table
```

### Via Quick Start ([quick_start.py](quick_start.py))
```bash
python quick_start.py
```

### Via Scripts Utilitários ([scripts.py](scripts.py))
```bash
python scripts.py install       # Instala dependências
python scripts.py test          # Roda testes
python scripts.py test-cov      # Testes com cobertura
python scripts.py lint          # Roda linter
python scripts.py format        # Formata código
python scripts.py clean         # Limpa temporários
python scripts.py example 1     # Roda exemplo específico
```

---

## 🔧 Comandos Úteis

### Instalação
```bash
pip install -r requirements.txt
```

### Testes
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=csv_ingestion --cov-report=html

# Teste específico
pytest tests/test_type_inference.py::TestTypeInference::test_infer_integer_types
```

### Qualidade de Código
```bash
# Linter
flake8 csv_ingestion tests examples

# Formatter
black csv_ingestion tests examples

# Type checker
mypy csv_ingestion
```

### Executar Exemplos
```bash
python examples/exemplo_01_basico.py
python examples/exemplo_02_criar_tabela.py
# ... etc
```

---

## 📊 Métricas do Projeto

- **Linhas de código**: ~2500
- **Módulos**: 5
- **Classes**: 7
- **Funções**: ~50
- **Testes**: 25+
- **Exemplos**: 6
- **Documentos**: 7

---

## 🚀 Próximos Passos Sugeridos

1. **Primeira vez?**
   - Execute: `python scripts.py install`
   - Depois: `python quick_start.py`

2. **Quer aprender?**
   - Leia: `README.md`
   - Teste: `examples/exemplo_01_basico.py`

3. **Quer migrar?**
   - Leia: `MIGRATION_GUIDE.md`
   - Teste com dry_run primeiro

4. **Quer contribuir?**
   - Leia: `ARCHITECTURE.md`
   - Execute testes: `pytest`

---

## 📞 Suporte

- 📖 Documentação principal: [README.md](README.md)
- 🔧 Problemas comuns: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 🔄 Migração: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- 🏗️ Arquitetura: [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Última atualização**: 2024-11-26  
**Versão**: 1.0.0  
**Autor**: Sistema Profissional de Ingestão CSV
