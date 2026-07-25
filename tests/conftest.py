"""Configurações globais de teste para o MailCerto."""
import pytest


@pytest.fixture(scope="session")
def qapp():
    """Cria uma instância QApplication para testes que utilizam Qt.

    O fixture é *session-scoped* para que a QApplication seja criada apenas
    uma vez durante toda a sessão de testes, evitando múltiplas instâncias.
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
