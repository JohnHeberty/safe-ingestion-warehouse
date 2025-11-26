# 🚨 FIX: Erro "não existe a coluna" com nome gigante

## ❌ Erro que você teve

```
UndefinedColumn: ERRO: não existe a coluna "no;fromnodeno;tonodeno;int_idglobaltype;int_agrupamento;int_idl" da relação "tbl_emissoes"
```

## 🔍 Causa Raiz

O CSV usa **ponto-e-vírgula (`;`)** como separador, mas o código está configurado para usar **vírgula (`,`)**.

Resultado: O Pandas trata a primeira linha inteira como UMA única coluna em vez de dividir em colunas separadas.

---

## ✅ SOLUÇÃO 1: Deixar o Sistema Auto-Detectar (RECOMENDADO)

A versão atualizada do sistema **detecta automaticamente** o separador correto!

```python
from csv_ingestion import CsvToDatabaseLoader, IngestionConfig

config = IngestionConfig(
    db_connection_string="postgresql://user:pass@localhost/db",
    schema="visum_peltlp",
    table_name="tbl_emissoes",
    csv_path="seu_arquivo.csv",
    
    # Deixe vírgula ou qualquer separador - o sistema vai detectar!
    csv_separator=",",  # ← Sistema corrige automaticamente
    
    create_table=True,  # ← Cria tabela se não existir
    validate_data=True,
)

loader = CsvToDatabaseLoader(config)

# SEMPRE faça dry-run primeiro!
report = loader.run(dry_run=True)

# Se tudo OK, insere de verdade
report = loader.run(dry_run=False)
```

### Como funciona a auto-detecção?

1. Se detectar apenas 1 coluna, testa outros separadores: `;`, `\t`, `|`, `,`
2. Lê as primeiras 5 linhas com cada separador
3. Escolhe o que resulta em mais de 1 coluna
4. Atualiza `config.csv_separator` automaticamente

---

## ✅ SOLUÇÃO 2: Especificar o Separador Correto

Se souber que é ponto-e-vírgula:

```python
config = IngestionConfig(
    # ... outras configs ...
    csv_separator=";",  # ← Especifica o correto
)
```

---

## ✅ SOLUÇÃO 3: Verificar o CSV Manualmente

```python
import pandas as pd

# Testa diferentes separadores
for sep in [',', ';', '\t', '|']:
    try:
        df = pd.read_csv("seu_arquivo.csv", sep=sep, nrows=5)
        print(f"Separador '{sep}': {len(df.columns)} colunas")
        print(f"  Colunas: {list(df.columns)}\n")
    except:
        print(f"Separador '{sep}': ERRO\n")
```

---

## 🛡️ Proteções Adicionadas

### 1. **Retry Automático** (3 tentativas)
Se falhar, tenta novamente automaticamente

### 2. **Criação de Tabela**
Se `create_table=True` e a tabela não existir, cria automaticamente

### 3. **Logs Detalhados**
```
⚠️ Apenas 1 coluna detectada com separador ','. Tentando auto-detectar...
✓ Separador correto detectado: ';'
```

### 4. **Tratamento de Erro Específico**
Detecta erro de "coluna não existe" e mostra:
- ✓ Colunas do DataFrame
- ✓ Colunas esperadas no banco
- ✓ Sugestão de criar tabela

---

## 📋 Checklist de Debug

1. ✅ Abra o CSV no editor de texto (não Excel!)
2. ✅ Veja qual caractere separa as colunas na primeira linha
3. ✅ Configure `csv_separator` ou deixe o sistema detectar
4. ✅ **SEMPRE** rode com `dry_run=True` primeiro
5. ✅ Verifique os logs - eles mostram o separador detectado
6. ✅ Se necessário, ajuste manualmente e rode novamente

---

## 🎯 Exemplo Completo (Seu Caso)

```python
from csv_ingestion import CsvToDatabaseLoader, IngestionConfig

# Configuração completa
config = IngestionConfig(
    # Banco de dados
    db_connection_string="postgresql://postgres:senha@localhost:5432/database",
    schema="visum_peltlp",
    table_name="tbl_emissoes",
    
    # CSV (sistema detecta o separador automaticamente)
    csv_path="C:/dados/emissoes.csv",
    csv_separator=",",  # Não importa - será auto-detectado
    csv_encoding="utf-8",
    
    # Comportamento
    create_table=True,  # ← IMPORTANTE: cria se não existir
    if_exists="append",
    chunk_size=5000,
    
    # Validação
    validate_data=True,
    error_strategy="collect_errors",  # Coleta todos os erros
)

loader = CsvToDatabaseLoader(config)

# PASSO 1: Análise (não insere nada)
print("🧪 Analisando CSV...")
report = loader.run(dry_run=True)

print(f"✓ Separador detectado: '{config.csv_separator}'")
print(f"✓ Total de linhas: {report.total_rows_csv}")
print(f"✓ Colunas encontradas: {len(report.columns)}")

# Mostra primeiras colunas
for col in report.columns[:5]:
    print(f"  - {col['name']}: {col['suggested_sql_type']}")

# PASSO 2: Se tudo OK, insere
input("\nPressione ENTER para inserir os dados...")
report = loader.run(dry_run=False)

print(f"\n✅ Sucesso! {report.total_rows_inserted} linhas inseridas")
```

---

## 📞 Se ainda tiver problemas

Execute este script de diagnóstico:

```python
import pandas as pd

csv_path = "seu_arquivo.csv"

print("🔍 DIAGNÓSTICO DO CSV\n")

# 1. Primeiras linhas do arquivo
print("1. Primeiras linhas (texto puro):")
with open(csv_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 3:
            print(f"   Linha {i+1}: {repr(line)}")

# 2. Testa separadores
print("\n2. Teste de separadores:")
for sep in [',', ';', '\t', '|']:
    try:
        df = pd.read_csv(csv_path, sep=sep, nrows=3)
        print(f"   Separador '{sep}':")
        print(f"      - Colunas: {len(df.columns)}")
        print(f"      - Nomes: {list(df.columns)[:5]}")
    except Exception as e:
        print(f"   Separador '{sep}': ERRO - {str(e)[:50]}")

print("\n✓ Use o separador que resultou em MAIS colunas")
```

---

## 💡 Dica Final

**SEMPRE use `dry_run=True` primeiro!** Isso evita problemas e mostra exatamente o que será feito.

O sistema agora é **resiliente** e **auto-corrige** a maioria dos problemas comuns!
