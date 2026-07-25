"""Testes para o IPLocationResultsModel — modelo de tabela com colunas
de IP, Cidade, Estado e CEP."""
import pytest
from PySide6.QtCore import Qt
from mailcerto.core.models import CheckResult, CheckStatus
from mailcerto.ui.models import IPLocationResultsModel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_success_result():
    """CheckResult de sucesso com raw_data populado (caso típico)."""
    return CheckResult(
        check_id="ip_location",
        category="Rede",
        title="Localização Geográfica",
        status=CheckStatus.SUCCESS,
        summary="Localizado em: Mountain View, California - United States",
        details="IP Analisado: 8.8.8.8\nCidade: Mountain View\nCEP/Postal: 94043",
        response_time_ms=42.5,
        raw_data={
            "ip": "8.8.8.8",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
            "country_name": "United States",
            "postal": "94043",
            "latitude": 37.4056,
            "longitude": -122.0775,
            "timezone": "America/Los_Angeles",
            "org": "Google LLC",
            "asn": "AS15169",
            "currency": "USD",
            "languages": "en-US,en;q=0.9",
        },
    )


@pytest.fixture
def sample_error_result():
    """CheckResult de erro com raw_data contendo apenas o IP."""
    return CheckResult(
        check_id="ip_location",
        category="Rede",
        title="Localização Geográfica",
        status=CheckStatus.ERROR,
        summary="Erro ao conectar à API de geolocalização.",
        details="Connection refused",
        response_time_ms=100.0,
        raw_data={"ip": "8.8.8.8"},
    )


# ---------------------------------------------------------------------------
# Estrutura do modelo
# ---------------------------------------------------------------------------

class TestIPLocationResultsModelStructure:
    """Verifica a estrutura básica do modelo."""

    def test_model_has_six_columns(self, qapp):
        model = IPLocationResultsModel()
        assert model.columnCount() == 6

    def test_model_has_correct_headers(self, qapp):
        model = IPLocationResultsModel()
        expected = ["IP", "Cidade", "Estado", "CEP", "Status", "Tempo (ms)"]
        for i, header in enumerate(expected):
            assert model.headerData(i, Qt.Horizontal, Qt.DisplayRole) == header

    def test_model_row_count_with_results(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.rowCount() == 1

    def test_model_row_count_empty(self, qapp):
        model = IPLocationResultsModel()
        assert model.rowCount() == 0

    def test_model_update_results(self, qapp, sample_success_result, sample_error_result):
        model = IPLocationResultsModel()
        assert model.rowCount() == 0
        model.update_results([sample_success_result, sample_error_result])
        assert model.rowCount() == 2


# ---------------------------------------------------------------------------
# Dados exibidos na tabela
# ---------------------------------------------------------------------------

class TestIPLocationResultsModelData:
    """Verifica que os dados corretos são exibidos em cada coluna."""

    def test_shows_ip_in_column_0(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "8.8.8.8"

    def test_shows_city_in_column_1(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 1), Qt.DisplayRole) == "Mountain View"

    def test_shows_state_in_column_2(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 2), Qt.DisplayRole) == "California"

    def test_shows_postal_code_in_column_3(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 3), Qt.DisplayRole) == "94043"

    def test_shows_status_in_column_4(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 4), Qt.DisplayRole) == "SUCCESS"

    def test_shows_response_time_in_column_5(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 5), Qt.DisplayRole) == "42.5"

    def test_shows_ip_in_error_result(self, qapp, sample_error_result):
        """Mesmo em erro, o IP deve aparecer na tabela."""
        model = IPLocationResultsModel([sample_error_result])
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "8.8.8.8"

    def test_shows_na_for_missing_ip(self, qapp):
        """Quando raw_data está vazio, IP deve mostrar 'N/A'."""
        result = CheckResult(
            check_id="ip_location", category="Rede", title="Localização Geográfica",
            status=CheckStatus.WARNING, summary="Não foi possível resolver.",
            details="error", response_time_ms=10.0,
        )
        model = IPLocationResultsModel([result])
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "N/A"

    def test_shows_na_for_missing_city(self, qapp, sample_error_result):
        """Quando raw_data não tem cidade, deve mostrar 'N/A'."""
        model = IPLocationResultsModel([sample_error_result])
        assert model.data(model.index(0, 1), Qt.DisplayRole) == "N/A"

    def test_shows_na_for_missing_state(self, qapp, sample_error_result):
        """Quando raw_data não tem estado, deve mostrar 'N/A'."""
        model = IPLocationResultsModel([sample_error_result])
        assert model.data(model.index(0, 2), Qt.DisplayRole) == "N/A"

    def test_shows_na_for_missing_postal(self, qapp):
        """Quando raw_data tem IP mas não CEP, CEP deve mostrar 'N/A'."""
        result = CheckResult(
            check_id="ip_location", category="Rede", title="Localização Geográfica",
            status=CheckStatus.WARNING, summary="Não foi possível resolver.",
            details="error", response_time_ms=10.0,
            raw_data={"ip": "8.8.8.8"},
        )
        model = IPLocationResultsModel([result])
        assert model.data(model.index(0, 3), Qt.DisplayRole) == "N/A"

    def test_shows_dash_for_missing_response_time(self, qapp, sample_success_result):
        """Quando response_time_ms é None, deve mostrar '-'."""
        result = CheckResult(
            check_id="ip_location", category="Rede", title="Localização Geográfica",
            status=CheckStatus.SUCCESS, summary="OK",
            raw_data={"ip": "1.2.3.4"},
        )
        model = IPLocationResultsModel([result])
        assert model.data(model.index(0, 5), Qt.DisplayRole) == "-"


# ---------------------------------------------------------------------------
# Alinhamento
# ---------------------------------------------------------------------------

class TestIPLocationResultsModelAlignment:
    """Verifica o alinhamento das células: todas as colunas são alinhadas
    igualmente (esquerda + centro vertical) para consistência visual."""

    def test_all_columns_are_equally_left_aligned(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        expected = Qt.AlignLeft | Qt.AlignVCenter
        for col in range(model.columnCount()):
            assert model.data(model.index(0, col), Qt.TextAlignmentRole) == expected


# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------

class TestIPLocationResultsModelEdgeCases:
    """Testes de borda."""

    def test_invalid_index_returns_none(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(-1, 0), Qt.DisplayRole) is None
        assert model.data(model.index(0, -1), Qt.DisplayRole) is None
        assert model.data(model.index(99, 99), Qt.DisplayRole) is None

    def test_non_display_role_returns_none(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.data(model.index(0, 0), Qt.EditRole) is None

    def test_vertical_header_returns_none(self, qapp, sample_success_result):
        model = IPLocationResultsModel([sample_success_result])
        assert model.headerData(0, Qt.Vertical, Qt.DisplayRole) is None
