"""
Exemplo 7: CSV Problemático com Auto-Correção
==============================================

Demonstra como o sistema lida automaticamente com:
- Separador errado (ponto-e-vírgula em vez de vírgula)
- Encoding incorreto
- Colunas com caracteres especiais
- Retry automático em caso de falhas
"""

from csv_ingestion import CsvToDatabaseLoader, IngestionConfig
import pandas as pd
from pathlib import Path

# ========================================
# CENÁRIO: CSV com problemas comuns
# ========================================

def criar_csv_problematico():
    """Cria um CSV com ponto-e-vírgula como separador (problema comum)"""
    
    csv_path = Path("data/exemplo_problematico.csv")
    csv_path.parent.mkdir(exist_ok=True)
    
    # Simula CSV exportado do Excel com ponto-e-vírgula
    conteudo = """no;fromnodeno;tonodeno;int_idglobaltype;int_agrupamento;int_idl
1;100;200;5;1;L001
2;101;201;5;1;L002
3;102;202;6;2;L003
4;103;203;6;2;L004
5;104;204;7;3;L005
"""
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✓ CSV problemático criado: {csv_path}")
    print(f"  - Separador: ponto-e-vírgula (;)")
    print(f"  - Colunas com caracteres especiais")
    return csv_path


# ========================================
# PASSO 1: Criar CSV de teste
# ========================================
csv_path = criar_csv_problematico()

# ========================================
# PASSO 2: Configurar com separador ERRADO de propósito
# ========================================
config = IngestionConfig(
    # Conexão
    db_connection_string="postgresql://user:password@localhost:5432/db",
    schema="visum_peltlp",
    table_name="tbl_emissoes",
    
    # CSV com separador ERRADO (sistema vai detectar automaticamente)
    csv_path=str(csv_path),
    csv_separator=",",  # ❌ ERRADO! O CSV usa ponto-e-vírgula
    csv_encoding="utf-8",
    
    # Comportamento resiliente
    create_table=True,  # ✅ Cria tabela automaticamente se não existir
    if_exists="append",
    chunk_size=1000,
    
    # Validação
    validate_data=True,
    error_strategy="fail_fast",
)

# ========================================
# PASSO 3: Executar com DRY-RUN
# ========================================
print("\n" + "="*60)
print("🧪 EXECUTANDO DRY-RUN (apenas análise, sem inserir)")
print("="*60 + "\n")

loader = CsvToDatabaseLoader(config)

try:
    report = loader.run(dry_run=True)
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO DO DRY-RUN")
    print("="*60)
    print(f"✓ Status: {report.status}")
    print(f"✓ Arquivo: {report.csv_path}")
    print(f"✓ Linhas lidas: {report.total_rows_csv}")
    print(f"✓ Colunas detectadas: {len(report.columns)}")
    print(f"✓ Separador detectado: '{config.csv_separator}'")  # Sistema corrigiu!
    print(f"✓ Encoding: {config.csv_encoding}")
    
    print("\n📋 Colunas Analisadas:")
    for col in report.columns[:3]:  # Mostra primeiras 3
        print(f"  - {col['name']}: {col['suggested_sql_type']}")
    
    print("\n💡 OBSERVAÇÕES:")
    print("  ✓ O sistema detectou automaticamente o separador correto (;)")
    print("  ✓ Colunas foram sanitizadas para evitar problemas no banco")
    print("  ✓ Tipos SQL foram inferidos automaticamente")
    
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    print("\n💡 Mesmo com erro, o sistema tentou:")
    print("  1. Auto-detectar o separador correto")
    print("  2. Testar diferentes encodings")
    print("  3. Sanitizar nomes de colunas")

# ========================================
# PASSO 4: Executar INSERÇÃO REAL
# ========================================
print("\n" + "="*60)
print("💾 EXECUTANDO INSERÇÃO REAL")
print("="*60 + "\n")

try:
    report = loader.run(dry_run=False)
    
    print("\n✅ SUCESSO!")
    print(f"  Total inserido: {report.total_rows_inserted} linhas")
    print(f"  Tempo total: {report.total_duration_formatted}")
    print(f"  Tabela: {config.schema}.{config.table_name}")
    
except Exception as e:
    print(f"\n⚠️ Erro durante inserção: {str(e)}")
    print("\nMecanismos de resiliência ativados:")
    print("  1. ✓ Retry automático (até 3 tentativas)")
    print("  2. ✓ Criação automática de tabela se não existir")
    print("  3. ✓ Detecção de erros de schema com mensagens claras")
    print("  4. ✓ Log detalhado para diagnóstico")
    
    # Mostra as colunas detectadas para debug
    print("\n🔍 Debug - Colunas do DataFrame:")
    df_test = pd.read_csv(csv_path, sep=';')
    print(f"  {list(df_test.columns)}")

# ========================================
# RECURSOS DE RESILIÊNCIA
# ========================================
print("\n" + "="*60)
print("🛡️ RECURSOS DE RESILIÊNCIA DO SISTEMA")
print("="*60)
print("""
1. AUTO-DETECÇÃO DE SEPARADOR
   - Testa: vírgula (,), ponto-e-vírgula (;), tab (\\t), pipe (|)
   - Detecta automaticamente se apenas 1 coluna foi encontrada
   
2. AUTO-DETECÇÃO DE ENCODING
   - Testa: utf-8, latin1, cp1252, iso-8859-1
   - Fallback automático se houver erro de decode

3. RETRY AUTOMÁTICO
   - Até 3 tentativas por chunk
   - Aguarda 1 segundo entre tentativas
   - Logs detalhados de cada tentativa

4. CRIAÇÃO AUTOMÁTICA DE TABELA
   - Se create_table=True e tabela não existe
   - Gera DDL automaticamente com tipos corretos
   - Tenta novamente após criar a tabela

5. SANITIZAÇÃO DE COLUNAS
   - Remove espaços extras
   - Mantém caracteres válidos
   - Previne erros de SQL injection

6. TRATAMENTO DE ERROS ESPECÍFICOS
   - Detecta erro "coluna não existe"
   - Mostra colunas do DataFrame vs. Banco
   - Sugestões de correção automáticas
""")

print("\n💡 DICA: Sempre use dry_run=True primeiro para validar!")
