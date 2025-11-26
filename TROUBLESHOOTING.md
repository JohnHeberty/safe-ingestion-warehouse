# 🔧 Guia de Troubleshooting

Soluções para problemas comuns ao usar o sistema de ingestão.

---

## 📚 Índice

1. [Erros de Instalação](#erros-de-instalação)
2. [Erros de Conexão](#erros-de-conexão)
3. [Erros de CSV](#erros-de-csv)
4. [Erros de Validação](#erros-de-validação)
5. [Erros de Inserção](#erros-de-inserção)
6. [Performance](#performance)
7. [Dicas Gerais](#dicas-gerais)

---

## 🔴 Erros de Instalação

### Erro: "No module named 'sqlalchemy'"

**Problema**: Dependências não instaladas.

**Solução**:
```bash
pip install -r requirements.txt
```

### Erro: "psycopg2 installation error"

**Problema**: Compilador C++ não encontrado (Windows).

**Solução**: Use a versão binary:
```bash
pip install psycopg2-binary
```

### Erro: "Microsoft Visual C++ required"

**Problema**: Visual C++ não instalado (Windows).

**Solução**:
1. Instale [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Ou use versões binary dos pacotes

---

## 🔴 Erros de Conexão

### Erro: "could not connect to server"

**Problema**: Banco de dados não acessível.

**Checklist**:
- [ ] Banco está rodando?
- [ ] Host/porta corretos?
- [ ] Firewall bloqueando?
- [ ] Credenciais corretas?

**Solução**:
```python
# Teste a conexão primeiro
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://user:pass@host:port/db")

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexão OK!")
except Exception as e:
    print(f"❌ Erro: {e}")
```

### Erro: "authentication failed"

**Problema**: Credenciais incorretas.

**Solução**:
- Verifique usuário e senha
- Use URL encoding para caracteres especiais:
  ```python
  from urllib.parse import quote_plus
  password = quote_plus("senha@com#caracteres")
  url = f"postgresql://user:{password}@host/db"
  ```

### Erro: "database does not exist"

**Problema**: Banco de dados não existe.

**Solução**:
```sql
-- Crie o banco primeiro
CREATE DATABASE meu_banco;
```

---

## 🔴 Erros de CSV

### Erro: "FileNotFoundError"

**Problema**: Arquivo CSV não encontrado.

**Solução**:
```python
from pathlib import Path

csv_path = Path("data/arquivo.csv")
if not csv_path.exists():
    print(f"❌ Arquivo não encontrado: {csv_path.absolute()}")
else:
    loader = CsvToDatabaseLoader(csv_path=str(csv_path), ...)
```

### Erro: "UnicodeDecodeError"

**Problema**: Encoding incorreto.

**Solução**:
```python
# Tente diferentes encodings
loader = CsvToDatabaseLoader(
    csv_encoding="latin1",  # ou "cp1252", "iso-8859-1"
    ...
)
```

**Detectar encoding automaticamente**:
```python
import chardet

with open("arquivo.csv", "rb") as f:
    result = chardet.detect(f.read(10000))
    print(f"Encoding detectado: {result['encoding']}")
```

### Erro: "ParserError: Error tokenizing data"

**Problema**: Separador incorreto ou CSV malformado.

**Soluções**:
```python
# 1. Tente outro separador
loader = CsvToDatabaseLoader(
    csv_separator=";",  # ou "\t" para TSV
    ...
)

# 2. Inspecione o CSV manualmente
with open("arquivo.csv", "r") as f:
    print(f.read(500))  # Primeiros 500 caracteres
```

### Erro: "CSV com colunas vazias"

**Problema**: CSV tem colunas sem nome.

**Solução**:
```python
# Pré-processe o CSV
import pandas as pd

df = pd.read_csv("arquivo.csv")
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove colunas Unnamed
df.to_csv("arquivo_limpo.csv", index=False)
```

---

## 🔴 Erros de Validação

### Erro: "Validation failed (fail_fast)"

**Problema**: Dados inválidos no CSV.

**Solução**:
```python
# Use collect_errors para ver todos os erros
loader = CsvToDatabaseLoader(
    error_strategy="collect_errors",
    ...
)

report = loader.run(dry_run=True)

if not report.validation_result.is_valid:
    print(f"Erros encontrados: {len(report.validation_result.errors)}")
    for error in report.validation_result.errors[:10]:
        print(f"  Linha {error.row_index}: {error.error_message}")
```

### Erro: "Não foi possível converter 'abc' para INTEGER"

**Problema**: Dados numéricos como string.

**Soluções**:
```python
# 1. Pré-processe o CSV
import pandas as pd

df = pd.read_csv("arquivo.csv")
df['coluna_numerica'] = pd.to_numeric(df['coluna_numerica'], errors='coerce')
df.to_csv("arquivo_limpo.csv", index=False)

# 2. Ou desabilite validação (não recomendado)
loader = CsvToDatabaseLoader(
    validate_types=False,
    ...
)
```

### Erro: "String de tamanho X excede máximo de Y"

**Problema**: String maior que VARCHAR sugerido.

**Solução**:
```python
# O sistema vai sugerir TEXT automaticamente
# Mas você pode forçar sem validação:
loader = CsvToDatabaseLoader(
    validate_types=False,
    ...
)
```

---

## 🔴 Erros de Inserção

### Erro: "duplicate key value violates unique constraint"

**Problema**: Tentando inserir chave primária duplicada.

**Soluções**:
```python
# 1. Use deduplicação
loader = CsvToDatabaseLoader(
    dedup_columns=["id"],
    ...
)

# 2. Ou use replace
loader = CsvToDatabaseLoader(
    if_exists="replace",
    ...
)
```

### Erro: "relation does not exist"

**Problema**: Tabela não existe.

**Solução**:
```python
# Crie a tabela automaticamente
loader = CsvToDatabaseLoader(
    create_table=True,
    ...
)
```

### Erro: "permission denied for schema"

**Problema**: Usuário sem permissão no schema.

**Solução**:
```sql
-- Execute como admin do banco
GRANT ALL ON SCHEMA meu_schema TO meu_usuario;
GRANT ALL ON ALL TABLES IN SCHEMA meu_schema TO meu_usuario;
```

### Erro: "column does not exist"

**Problema**: Colunas do CSV não batem com tabela.

**Solução**:
```python
# Execute dry-run para ver warnings
loader.run(dry_run=True)

# O sistema vai mostrar:
# ⚠ Colunas no CSV mas não na tabela: {...}
# ⚠ Colunas na tabela mas não no CSV: {...}
```

---

## 🔴 Performance

### Problema: Inserção muito lenta

**Soluções**:

**1. Aumente chunk_size**:
```python
loader = CsvToDatabaseLoader(
    chunk_size=50000,  # Default é 10000
    ...
)
```

**2. Desabilite validação temporariamente**:
```python
loader = CsvToDatabaseLoader(
    validate_types=False,
    ...
)
```

**3. Use UNLOGGED tables (PostgreSQL)**:
```sql
-- Crie a tabela como UNLOGGED (mais rápido, mas sem WAL)
CREATE UNLOGGED TABLE minha_tabela (...);
```

**4. Desabilite índices temporariamente**:
```sql
-- Antes da inserção
DROP INDEX IF EXISTS idx_coluna;

-- Depois da inserção
CREATE INDEX idx_coluna ON tabela(coluna);
```

### Problema: Memory overflow

**Solução**:
```python
# Reduza chunk_size
loader = CsvToDatabaseLoader(
    chunk_size=1000,  # Menor
    ...
)
```

---

## 🔴 Dicas Gerais

### 1. Use sempre dry-run primeiro

```python
# Sempre teste antes!
report = loader.run(dry_run=True)

# Veja o que vai acontecer
print(f"Vai inserir {report.total_rows_csv} linhas")
print(f"DDL: {report.ddl_generated}")

# Só depois insira
if input("OK? (s/n): ").lower() == 's':
    loader.run(dry_run=False)
```

### 2. Habilite logging detalhado

```python
import logging

loader = CsvToDatabaseLoader(
    log_level=logging.DEBUG,  # Muito detalhado
    ...
)
```

### 3. Salve relatórios

```python
from csv_ingestion.utils import save_report_to_file

report = loader.run(dry_run=False)
save_report_to_file(report.to_dict(), "report.json")
```

### 4. Verifique dados inseridos

```python
from sqlalchemy import text

with engine.connect() as conn:
    # Conta linhas
    result = conn.execute(text("SELECT COUNT(*) FROM minha_tabela"))
    count = result.scalar()
    print(f"Linhas na tabela: {count}")
    
    # Amostra
    result = conn.execute(text("SELECT * FROM minha_tabela LIMIT 5"))
    for row in result:
        print(row)
```

### 5. Backup antes de REPLACE

```bash
# PostgreSQL
pg_dump -t schema.tabela database > backup.sql

# Restaurar se necessário
psql database < backup.sql
```

---

## 📞 Precisa de Mais Ajuda?

1. ✅ Verifique os [exemplos](examples/)
2. ✅ Leia a [documentação](README.md)
3. ✅ Veja o [guia de migração](MIGRATION_GUIDE.md)
4. ✅ Execute com `dry_run=True` primeiro
5. ✅ Habilite logging detalhado

---

## 🐛 Reportar Bug

Se encontrou um bug:

1. Verifique se não está neste guia
2. Execute com logging detalhado
3. Capture o stack trace completo
4. Prepare exemplo mínimo reproduzível
5. Abra uma issue com todas as informações

---

**Última atualização**: 2024-11-26
