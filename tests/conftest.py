"""
Configuração para pytest.
"""

import pytest


def pytest_configure(config):
    """Configuração do pytest."""
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
