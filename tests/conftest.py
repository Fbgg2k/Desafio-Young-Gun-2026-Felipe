import pytest

from ledger import CreditLedger


@pytest.fixture
def database_path(tmp_path):
    """Caminho para um banco novo e isolado por teste."""
    return str(tmp_path / "ledger.db")


@pytest.fixture
def ledger(database_path):
    return CreditLedger(database_path)
