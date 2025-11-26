# 🛠️ Scripts Úteis - CSV Ingestion System
# Execute com: python scripts.py <comando>

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Executa um comando shell."""
    print(f"\n{'='*80}")
    print(f"🔧 {description}")
    print(f"{'='*80}")
    print(f"$ {cmd}\n")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Erro ao executar: {cmd}")
        sys.exit(result.returncode)
    print(f"\n✅ Concluído!")


def install_deps():
    """Instala dependências do projeto."""
    run_command(
        "pip install -r requirements.txt",
        "Instalando dependências"
    )


def run_tests():
    """Executa todos os testes."""
    run_command(
        "pytest -v",
        "Executando testes"
    )


def run_tests_coverage():
    """Executa testes com cobertura."""
    run_command(
        "pytest --cov=csv_ingestion --cov-report=html --cov-report=term",
        "Executando testes com cobertura"
    )
    print("\n📊 Relatório de cobertura em: htmlcov/index.html")


def run_linter():
    """Executa linter (flake8)."""
    run_command(
        "flake8 csv_ingestion tests examples",
        "Executando linter"
    )


def run_formatter():
    """Formata código com black."""
    run_command(
        "black csv_ingestion tests examples",
        "Formatando código"
    )


def run_type_check():
    """Executa verificação de tipos com mypy."""
    run_command(
        "mypy csv_ingestion",
        "Verificando tipos"
    )


def run_quick_start():
    """Executa quick start."""
    run_command(
        "python quick_start.py",
        "Executando Quick Start"
    )


def run_example(num):
    """Executa um exemplo específico."""
    example_file = f"examples/exemplo_{num:02d}_*.py"
    import glob
    files = glob.glob(example_file)
    
    if not files:
        print(f"❌ Exemplo {num} não encontrado!")
        sys.exit(1)
    
    run_command(
        f"python {files[0]}",
        f"Executando exemplo {num}"
    )


def clean():
    """Limpa arquivos temporários."""
    patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        ".coverage",
        "*.egg-info",
        "dist",
        "build",
    ]
    
    print(f"\n{'='*80}")
    print("🧹 Limpando arquivos temporários")
    print(f"{'='*80}\n")
    
    for pattern in patterns:
        if os.name == 'nt':  # Windows
            cmd = f'powershell -Command "Get-ChildItem -Path . -Include {pattern} -Recurse -Force | Remove-Item -Force -Recurse"'
        else:  # Unix/Linux/Mac
            cmd = f'find . -name "{pattern}" -exec rm -rf {{}} +'
        
        print(f"Removendo: {pattern}")
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    
    print("\n✅ Limpeza concluída!")


def create_sample_csv():
    """Cria um CSV de exemplo."""
    import pandas as pd
    
    print(f"\n{'='*80}")
    print("📝 Criando CSV de exemplo")
    print(f"{'='*80}\n")
    
    df = pd.DataFrame({
        "id": range(1, 101),
        "nome": [f"Produto {i}" for i in range(1, 101)],
        "categoria": ["Eletrônicos", "Periféricos", "Hardware"] * 33 + ["Outros"],
        "preco": [round(100 + i * 10.5, 2) for i in range(1, 101)],
        "estoque": [10 + i for i in range(1, 101)],
        "ativo": [True if i % 2 == 0 else False for i in range(1, 101)],
    })
    
    output_path = "data/sample_data.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ CSV criado: {output_path}")
    print(f"   Linhas: {len(df)}")
    print(f"   Colunas: {len(df.columns)}")


def show_help():
    """Mostra ajuda."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    CSV INGESTION SYSTEM - SCRIPTS ÚTEIS                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Uso: python scripts.py <comando>

📦 INSTALAÇÃO:
  install              Instala dependências do requirements.txt

🧪 TESTES:
  test                 Executa todos os testes
  test-cov             Executa testes com cobertura
  
🔍 QUALIDADE DE CÓDIGO:
  lint                 Executa linter (flake8)
  format               Formata código com black
  type-check           Verifica tipos com mypy
  
🚀 EXECUÇÃO:
  quick-start          Executa quick_start.py
  example <num>        Executa exemplo específico (1-6)
  
🧹 MANUTENÇÃO:
  clean                Remove arquivos temporários
  create-sample        Cria CSV de exemplo
  
❓ AJUDA:
  help                 Mostra esta mensagem
  
Exemplos:
  python scripts.py install
  python scripts.py test
  python scripts.py example 1
  python scripts.py clean
  
""")


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    commands = {
        "install": install_deps,
        "test": run_tests,
        "test-cov": run_tests_coverage,
        "lint": run_linter,
        "format": run_formatter,
        "type-check": run_type_check,
        "quick-start": run_quick_start,
        "clean": clean,
        "create-sample": create_sample_csv,
        "help": show_help,
    }
    
    if command == "example":
        if len(sys.argv) < 3:
            print("❌ Especifique o número do exemplo: python scripts.py example 1")
            sys.exit(1)
        try:
            num = int(sys.argv[2])
            run_example(num)
        except ValueError:
            print("❌ Número de exemplo inválido!")
            sys.exit(1)
    elif command in commands:
        commands[command]()
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("Use 'python scripts.py help' para ver comandos disponíveis")
        sys.exit(1)


if __name__ == "__main__":
    main()
