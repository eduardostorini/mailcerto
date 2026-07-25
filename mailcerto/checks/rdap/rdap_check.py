import httpx
import time
from datetime import datetime
from mailcerto.core.models import CheckResult, CheckStatus

async def check_rdap_whois(domain: str) -> list[CheckResult]:
    results = []
    t0 = time.perf_counter()
    
    # Usando API RDAP pública da IANA/RDAP org (de domínio)
    rdap_url = f"https://rdap.org/domain/{domain}"
    
    async with httpx.AsyncClient(timeout=6.0) as client:
        try:
            resp = await client.get(rdap_url)
            elapsed = (time.perf_counter() - t0) * 1000.0
            
            if resp.status_code == 200:
                data = resp.json()
                ldh_name = data.get("ldhName", domain)
                status_list = data.get("status", [])
                
                # Extraindo o dono do domínio (Registrant)
                owner_info = "Não informado no RDAP público."
                for entity in data.get("entities", []):
                    roles = entity.get("roles", [])
                    if "registrant" in roles or "registrant" in [r.lower() for r in roles]:
                        vcard = entity.get("vcardArray", [])
                        if len(vcard) > 1:
                            properties = vcard[1]
                            for prop in properties:
                                if prop[0] == "fn":
                                    owner_info = prop[3]
                                    break
                        break
                
                events = []
                for event in data.get("events", []):
                    action = event.get("eventAction", "")
                    date = event.get("eventDate", "")
                    events.append(f"- {action}: {date}")
                
                details = (
                    f"Domínio: {ldh_name}\n"
                    f"Dono/Registrante: {owner_info}\n"
                    f"Status: {', '.join(status_list)}\n\n"
                    f"Eventos:\n" + "\n".join(events)
                )
                
                results.append(CheckResult(
                    check_id="rdap_whois", category="WHOIS & RDAP", title="Consulta RDAP",
                    status=CheckStatus.SUCCESS, summary=f"Dono: {owner_info}",
                    details=details, response_time_ms=elapsed
                ))
            else:
                results.append(CheckResult(
                    check_id="rdap_whois", category="WHOIS & RDAP", title="Consulta RDAP",
                    status=CheckStatus.WARNING, summary=f"Servidor RDAP retornou status {resp.status_code}.",
                    details=resp.text[:500], response_time_ms=elapsed
                ))
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="rdap_whois", category="WHOIS & RDAP", title="Consulta RDAP",
                status=CheckStatus.ERROR, summary="Erro ao conectar ao servidor RDAP.",
                details=str(e), response_time_ms=elapsed
            ))
            
    return results
