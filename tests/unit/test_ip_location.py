import pytest
import httpx
import socket
from unittest.mock import AsyncMock, patch, MagicMock
from mailcerto.checks.network.ip_location import check_ip_location, _resolve_target_to_ip
from mailcerto.core.models import CheckResult, CheckStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ipapi_success_response():
    """Simulates a successful ipapi.co JSON response for 8.8.8.8."""
    return {
        "ip": "8.8.8.8",
        "city": "Mountain View",
        "region": "California",
        "country": "US",
        "country_name": "United States",
        "country_code": "US",
        "postal": "94043",
        "latitude": 37.4056,
        "longitude": -122.0775,
        "timezone": "America/Los_Angeles",
        "org": "Google LLC",
        "asn": "AS15169",
        "currency": "USD",
        "languages": "en-US,en;q=0.9",
    }


@pytest.fixture
def mock_ipapi_error_response():
    """Simulates an ipapi.co error response (e.g. rate-limited or invalid IP)."""
    return {
        "error": True,
        "reason": "Rate limit exceeded",
        "message": "Rate limit exceeded",
    }


# ---------------------------------------------------------------------------
# Success cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_ip_location_success_with_ip(mock_ipapi_success_response):
    """Test successful geo-location lookup using a raw IP address."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, CheckResult)
    assert result.check_id == "ip_location"
    assert result.category == "Rede"
    assert result.title == "Localização Geográfica"
    assert result.status == CheckStatus.SUCCESS
    assert "Mountain View" in result.summary
    assert "California" in result.summary
    assert "United States" in result.summary
    assert "8.8.8.8" in result.details
    assert "Google LLC" in result.details
    assert result.response_time_ms is not None
    assert result.response_time_ms >= 0


@pytest.mark.asyncio
async def test_check_ip_location_success_with_domain(mock_ipapi_success_response):
    """Test successful geo-location lookup using a domain name (requires DNS resolution)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("socket.gethostbyname", return_value="8.8.8.8") as mock_dns, \
         patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("dns.google")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.SUCCESS
    assert "8.8.8.8" in result.details
    assert "Domínio consultado: dns.google" in result.details
    mock_dns.assert_called_once_with("dns.google")
    mock_client.get.assert_called_once_with("https://ipapi.co/8.8.8.8/json/")


@pytest.mark.asyncio
async def test_check_ip_location_contains_all_expected_fields(mock_ipapi_success_response):
    """Verify that all expected fields from the API response are present in the result details."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    details = results[0].details
    assert "IP Analisado: 8.8.8.8" in details
    assert "Cidade: Mountain View" in details
    assert "Estado/Região: California" in details
    assert "País: United States (US)" in details
    assert "CEP/Postal: 94043" in details
    assert "Coordenadas GPS: Lat 37.4056, Lon -122.0775" in details
    assert "Fuso Horário: America/Los_Angeles" in details
    assert "Provedor (ISP): Google LLC" in details
    assert "ASN: AS15169" in details
    assert "Moeda: USD" in details
    assert "Idiomas: en-US,en;q=0.9" in details


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_ip_location_dns_resolution_failure():
    """Test that a DNS resolution failure returns a WARNING result."""
    with patch("socket.gethostbyname", side_effect=socket.gaierror("Name or service not known")):
        results = await check_ip_location("nonexistent.invalid.domain.xyz")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.WARNING
    assert "Não foi possível resolver" in result.summary
    assert result.response_time_ms is not None


@pytest.mark.asyncio
async def test_check_ip_location_falls_back_on_http_429():
    """Em HTTP 429 da ipapi.co, deve consultar ip-api.com com o IP já resolvido."""
    ipapi_response = MagicMock()
    ipapi_response.status_code = 429
    ipapi_response.json.return_value = {
        "error": True,
        "reason": "RateLimited",
        "message": "Visit https://ipapi.co/ratelimited/ for details",
    }

    ip_api_response = MagicMock()
    ip_api_response.status_code = 200
    ip_api_response.json.return_value = {
        "status": "success",
        "query": "8.8.8.8",
        "country": "United States",
        "countryCode": "US",
        "regionName": "Virginia",
        "city": "Ashburn",
        "zip": "20149",
        "lat": 39.03,
        "lon": -77.5,
        "timezone": "America/New_York",
        "isp": "Google LLC",
        "org": "Google Public DNS",
        "as": "AS15169 Google LLC",
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=[ipapi_response, ip_api_response])

    with patch("socket.gethostbyname", return_value="8.8.8.8"), \
         patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("dns.google")

    result = results[0]
    assert result.status == CheckStatus.SUCCESS
    assert "Ashburn" in result.summary
    assert "IP Analisado: 8.8.8.8" in result.details
    assert "Fonte da consulta: ip-api.com" in result.details
    assert mock_client.get.call_args_list[0].args[0] == "https://ipapi.co/8.8.8.8/json/"
    assert "8.8.8.8" in mock_client.get.call_args_list[1].args[0]


@pytest.mark.asyncio
async def test_check_ip_location_api_error_response():
    """Erros que não são rate limit não devem acionar fallback."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": True,
        "reason": "Invalid IP address",
        "message": "Invalid IP address",
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.WARNING
    assert "Invalid IP address" in result.summary
    assert "8.8.8.8" in result.details
    assert "conversão domínio → IP foi concluída" in result.details
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_check_ip_location_non_200_status():
    """Test handling of a non-200 HTTP status code from the API."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.WARNING
    assert "404" in result.summary
    assert "8.8.8.8" in result.details


@pytest.mark.asyncio
async def test_check_ip_location_network_error():
    """Test handling of a network/connection error when calling the API."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.ERROR
    assert "Erro ao conectar" in result.summary
    assert result.response_time_ms is not None


@pytest.mark.asyncio
async def test_check_ip_location_timeout_error():
    """Test handling of a timeout error when calling the API."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.ERROR
    assert "Erro ao conectar" in result.summary


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_ip_location_missing_optional_fields():
    """Test that the function handles API responses with missing optional fields gracefully."""
    partial_response = {
        "ip": "8.8.8.8",
        "country_name": "United States",
        # Missing: city, region, postal, latitude, longitude, timezone, org, etc.
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = partial_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    assert len(results) == 1
    result = results[0]
    assert result.status == CheckStatus.SUCCESS
    assert "N/A" in result.details  # Missing fields should show as N/A


@pytest.mark.asyncio
async def test_check_ip_location_url_is_correct():
    """Verify that the correct API URL is constructed with the resolved IP."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ip": "1.1.1.1",
        "country_name": "Australia",
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await check_ip_location("1.1.1.1")

    # Verify the correct URL was called
    mock_client.get.assert_called_once_with("https://ipapi.co/1.1.1.1/json/")


@pytest.mark.asyncio
async def test_check_ip_location_skips_dns_for_raw_ip(mock_ipapi_success_response):
    """IPs válidos devem ir direto para a API, sem resolver DNS."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("socket.gethostbyname") as mock_dns, \
         patch("httpx.AsyncClient", return_value=mock_client):
        await check_ip_location("8.8.8.8")

    mock_dns.assert_not_called()
    mock_client.get.assert_called_once_with("https://ipapi.co/8.8.8.8/json/")


@pytest.mark.asyncio
async def test_check_ip_location_resolves_url_hostname_before_api(mock_ipapi_success_response):
    """URLs devem ter o hostname extraído, resolvido para IP e só então consultados."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("socket.gethostbyname", return_value="8.8.8.8") as mock_dns, \
         patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("https://dns.google/")

    mock_dns.assert_called_once_with("dns.google")
    mock_client.get.assert_called_once_with("https://ipapi.co/8.8.8.8/json/")
    assert "Domínio consultado: dns.google" in results[0].details


class TestResolveTargetToIp:
    def test_returns_ip_directly_for_ipv4(self):
        ip, host = _resolve_target_to_ip("8.8.8.8")
        assert ip == "8.8.8.8"
        assert host == "8.8.8.8"

    def test_resolves_domain_via_dns(self):
        with patch("socket.gethostbyname", return_value="142.250.185.78"):
            ip, host = _resolve_target_to_ip("google.com")
        assert ip == "142.250.185.78"
        assert host == "google.com"

    def test_extracts_hostname_from_url(self):
        with patch("socket.gethostbyname", return_value="8.8.8.8"):
            ip, host = _resolve_target_to_ip("https://dns.google/path")
        assert ip == "8.8.8.8"
        assert host == "dns.google"


# ---------------------------------------------------------------------------
# raw_data verification — IP Analisado e CEP/Postal no raw_data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_ip_location_raw_data_populated_on_success(mock_ipapi_success_response):
    """Verifica que raw_data é populado com os dados completos da API no caso de sucesso."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_success_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    result = results[0]
    assert result.raw_data is not None
    assert result.raw_data.get("ip") == "8.8.8.8"
    assert result.raw_data.get("postal") == "94043"
    assert result.raw_data.get("city") == "Mountain View"
    assert result.raw_data.get("org") == "Google LLC"


@pytest.mark.asyncio
async def test_check_ip_location_raw_data_contains_ip_on_api_error(mock_ipapi_error_response):
    """Verifica que raw_data contém o IP mesmo quando a API retorna um erro."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ipapi_error_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    result = results[0]
    assert result.raw_data is not None
    assert result.raw_data.get("ip") == "8.8.8.8"


@pytest.mark.asyncio
async def test_check_ip_location_raw_data_contains_ip_on_non_200():
    """Verifica que raw_data contém o IP quando a API retorna status não-200."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    result = results[0]
    assert result.raw_data is not None
    assert result.raw_data.get("ip") == "8.8.8.8"


@pytest.mark.asyncio
async def test_check_ip_location_raw_data_contains_ip_on_network_error():
    """Verifica que raw_data contém o IP em caso de erro de conexão."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        results = await check_ip_location("8.8.8.8")

    result = results[0]
    assert result.raw_data is not None
    assert result.raw_data.get("ip") == "8.8.8.8"


@pytest.mark.asyncio
async def test_check_ip_location_raw_data_empty_on_dns_failure():
    """Verifica que raw_data é um dict vazio quando a resolução DNS falha."""
    with patch("socket.gethostbyname", side_effect=socket.gaierror("Name or service not known")):
        results = await check_ip_location("nonexistent.invalid.domain.xyz")

    result = results[0]
    assert result.raw_data == {}
