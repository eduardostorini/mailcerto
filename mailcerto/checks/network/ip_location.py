import httpx
import ipaddress
import socket
import time
from urllib.parse import urlparse

from mailcerto.core.models import CheckResult, CheckStatus

IPAPI_URL = "https://ipapi.co/{ip}/json/"
IP_API_COM_URL = (
    "http://ip-api.com/json/{ip}"
    "?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
)


def _resolve_target_to_ip(target: str) -> tuple[str, str]:
    """Normaliza o alvo e resolve domínios para IPv4 antes da consulta na API."""
    cleaned = target.strip()
    if not cleaned:
        raise ValueError("Alvo vazio")

    host = cleaned
    if host.lower().startswith(("http://", "https://")):
        parsed = urlparse(host)
        if not parsed.hostname:
            raise ValueError(f"URL inválida: {target}")
        host = parsed.hostname
    elif "/" in host:
        host = host.split("/")[0]

    host = host.rstrip(".")

    try:
        ip = str(ipaddress.ip_address(host))
    except ValueError:
        ip = socket.gethostbyname(host)

    return ip, host


def _normalize_geolocation_data(data: dict, ip: str, source: str) -> dict:
    """Unifica o formato das respostas das APIs de geolocalização."""
    if source == "ipapi.co":
        return {"ip": ip, **data}

    return {
        "ip": ip,
        "city": data.get("city"),
        "region": data.get("regionName"),
        "country_name": data.get("country"),
        "country_code": data.get("countryCode"),
        "postal": data.get("zip"),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
        "timezone": data.get("timezone"),
        "org": data.get("org") or data.get("isp"),
        "asn": data.get("as"),
    }


def _is_rate_limited(status_code: int, data: dict | None) -> bool:
    if status_code == 429:
        return True
    if not data:
        return False
    reason = str(data.get("reason", "")).lower()
    return data.get("error") and "ratelimit" in reason.replace(" ", "")


def _build_location_details(ip: str, host: str, data: dict, api_source: str) -> tuple[str, str]:
    city = data.get("city") or "N/A"
    region = data.get("region") or "N/A"
    country = data.get("country_name") or "N/A"
    country_code = data.get("country_code") or ""
    isp = data.get("org") or "N/A"
    latitude = data.get("latitude", "N/A")
    longitude = data.get("longitude", "N/A")
    timezone = data.get("timezone") or "N/A"
    postal = data.get("postal") or "N/A"

    summary = f"Localizado em: {city}, {region} - {country}"
    domain_line = f"Domínio consultado: {host}\n" if host != ip else ""
    details = (
        f"{domain_line}"
        f"IP Analisado: {ip}\n"
        f"Fonte da consulta: {api_source}\n"
        f"Cidade: {city}\n"
        f"Estado/Região: {region}\n"
        f"País: {country} ({country_code})\n"
        f"CEP/Postal: {postal}\n"
        f"Coordenadas GPS: Lat {latitude}, Lon {longitude}\n"
        f"Fuso Horário: {timezone}\n"
        f"Provedor (ISP): {isp}\n"
        f"ASN: {data.get('asn', 'N/A')}\n"
        f"Moeda: {data.get('currency', 'N/A')}\n"
        f"Idiomas: {data.get('languages', 'N/A')}"
    )
    return summary, details


async def _fetch_from_ipapi(client: httpx.AsyncClient, ip: str) -> tuple[int, dict]:
    resp = await client.get(IPAPI_URL.format(ip=ip))
    try:
        data = resp.json()
    except Exception:
        data = {}
    return resp.status_code, data


async def _fetch_from_ip_api_com(client: httpx.AsyncClient, ip: str) -> tuple[int, dict]:
    resp = await client.get(IP_API_COM_URL.format(ip=ip))
    try:
        data = resp.json()
    except Exception:
        data = {}
    return resp.status_code, data


async def _query_geolocation(client: httpx.AsyncClient, ip: str) -> tuple[str | None, dict | None, str | None]:
    """Consulta geolocalização. Tenta ipapi.co e usa ip-api.com se houver rate limit."""
    status_code, data = await _fetch_from_ipapi(client, ip)

    if status_code == 200 and not data.get("error"):
        return "ipapi.co", _normalize_geolocation_data(data, ip, "ipapi.co"), None

    if not _is_rate_limited(status_code, data):
        if status_code == 200 and data.get("error"):
            return None, None, data.get("reason", "Erro desconhecido")
        return None, None, f"HTTP {status_code}"

    fallback_status, fallback_data = await _fetch_from_ip_api_com(client, ip)
    if fallback_status == 200 and fallback_data.get("status") == "success":
        return "ip-api.com", _normalize_geolocation_data(fallback_data, ip, "ip-api.com"), None

    if fallback_status == 200 and fallback_data.get("status") != "success":
        return None, None, fallback_data.get("message", "Erro na API alternativa")

    return None, None, (
        "Limite de requisições da ipapi.co (HTTP 429) e falha na API alternativa "
        f"(HTTP {fallback_status})."
    )


async def check_ip_location(target: str) -> list[CheckResult]:
    """
    Obtém a localização geográfica de um IP ou domínio.

    Domínios são convertidos para IP antes da consulta. Usa ipapi.co e,
    em caso de rate limit (429), recorre automaticamente ao ip-api.com.
    """
    t0 = time.perf_counter()

    try:
        ip, host = _resolve_target_to_ip(target)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return [CheckResult(
            check_id="ip_location", category="Rede", title="Localização Geográfica",
            status=CheckStatus.WARNING, summary="Não foi possível resolver o IP para geo-localização.",
            details=str(e), response_time_ms=elapsed
        )]

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            api_source, data, error = await _query_geolocation(client, ip)
            elapsed = (time.perf_counter() - t0) * 1000.0
            domain_line = f"Domínio consultado: {host}\n" if host != ip else ""

            if data:
                summary, details = _build_location_details(ip, host, data, api_source)
                return [CheckResult(
                    check_id="ip_location", category="Rede", title="Localização Geográfica",
                    status=CheckStatus.SUCCESS, summary=summary,
                    details=details, response_time_ms=elapsed,
                    raw_data={"ip": ip, "resolved_host": host, "api_source": api_source, **data}
                )]

            if error and ("429" in error or "Limite" in error):
                summary = "Limite de requisições da API de geolocalização atingido."
            else:
                summary = f"API retornou erro: {error}"

            return [CheckResult(
                check_id="ip_location", category="Rede", title="Localização Geográfica",
                status=CheckStatus.WARNING, summary=summary,
                details=(
                    f"{domain_line}"
                    f"IP Analisado: {ip}\n"
                    f"Erro: {error}\n\n"
                    "A conversão domínio → IP foi concluída. "
                    "O erro veio da API externa, não da resolução DNS."
                ),
                response_time_ms=elapsed,
                raw_data={"ip": ip, "resolved_host": host}
            )]

        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            domain_line = f"Domínio consultado: {host}\n" if host != ip else ""
            return [CheckResult(
                check_id="ip_location", category="Rede", title="Localização Geográfica",
                status=CheckStatus.ERROR,
                summary="Erro ao conectar à API de geolocalização.",
                details=f"{domain_line}IP Analisado: {ip}\n{str(e)}",
                response_time_ms=elapsed,
                raw_data={"ip": ip, "resolved_host": host}
            )]
