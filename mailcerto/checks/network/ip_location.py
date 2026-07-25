import httpx
import socket
import time
from mailcerto.core.models import CheckResult, CheckStatus

async def check_ip_location(target: str) -> list[CheckResult]:
    results = []
    t0 = time.perf_counter()
    
    # 1. Resolve host to IP
    try:
        ip = socket.gethostbyname(target)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return [CheckResult(
            check_id="ip_location", category="Rede", title="Localização Geográfica",
            status=CheckStatus.WARNING, summary="Não foi possível resolver o IP para geo-localização.",
            details=str(e), response_time_ms=elapsed
        )]
        
    # 2. Query public ip-api.com API
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url)
            elapsed = (time.perf_counter() - t0) * 1000.0
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    city = data.get("city", "N/A")
                    region = data.get("regionName", "N/A")
                    country = data.get("country", "N/A")
                    isp = data.get("isp", "N/A")
                    asn = data.get("as", "N/A")
                    lat = data.get("lat", "N/A")
                    lon = data.get("lon", "N/A")
                    
                    summary = f"Localizado em: {city}, {region} - {country}"
                    details = (
                        f"IP Analisado: {ip}\n"
                        f"Cidade: {city}\n"
                        f"Estado/Região: {region}\n"
                        f"País: {country} ({data.get('countryCode', '')})\n"
                        f"Coordenadas: Lat {lat}, Lon {lon}\n"
                        f"Fuso Horário: {data.get('timezone', '')}\n"
                        f"Provedor (ISP): {isp}\n"
                        f"Organização: {data.get('org', '')}\n"
                        f"ASN: {asn}"
                    )
                    
                    results.append(CheckResult(
                        check_id="ip_location", category="Rede", title="Localização Geográfica",
                        status=CheckStatus.SUCCESS, summary=summary,
                        details=details, response_time_ms=elapsed
                    ))
                else:
                    msg = data.get("message", "Erro desconhecido da API")
                    results.append(CheckResult(
                        check_id="ip_location", category="Rede", title="Localização Geográfica",
                        status=CheckStatus.WARNING, summary=f"API de Geolocalização retornou erro: {msg}",
                        details=f"IP: {ip}\nErro: {msg}", response_time_ms=elapsed
                    ))
            else:
                results.append(CheckResult(
                    check_id="ip_location", category="Rede", title="Localização Geográfica",
                    status=CheckStatus.WARNING, summary=f"API externa respondeu com status {resp.status_code}",
                    details=f"IP: {ip}\nCódigo HTTP: {resp.status_code}", response_time_ms=elapsed
                ))
                
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="ip_location", category="Rede", title="Localização Geográfica",
                status=CheckStatus.ERROR, summary="Erro ao conectar à API de geolocalização.",
                details=str(e), response_time_ms=elapsed
            ))
            
    return results
