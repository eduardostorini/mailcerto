import httpx
import time
from datetime import datetime
from mailcerto.core.models import CheckResult, CheckStatus

async def check_rdap_whois(domain: str) -> list[CheckResult]:
    results = []
    t0 = time.perf_counter()
    
    # Usando API RDAP pública da IANA/RDAP org (de domínio)
    rdap_url = f"https://rdap.org/domain/{domain}"
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.get(rdap_url)
            elapsed = (time.perf_counter() - t0) * 1000.0
            
            if resp.status_code == 200:
                data = resp.json()
                ldh_name = data.get("ldhName", domain)
                status_list = data.get("status", [])
                
                # Extraindo o dono do domínio (Registrant) - múltiplos métodos
                owner_info = "Não informado no RDAP público."
                registrar = "Não informado"
                
                # Método 1: Buscar em entities com role registrant
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
                                elif prop[0] == "org":
                                    owner_info = prop[3]
                                    break
                        if owner_info != "Não informado no RDAP público.":
                            break
                
                # Método 2: Se não encontrou, buscar em todas as entities
                if owner_info == "Não informado no RDAP público.":
                    for entity in data.get("entities", []):
                        vcard = entity.get("vcardArray", [])
                        if len(vcard) > 1:
                            properties = vcard[1]
                            for prop in properties:
                                if prop[0] == "fn":
                                    owner_info = prop[3]
                                    break
                                elif prop[0] == "org":
                                    owner_info = prop[3]
                                    break
                        if owner_info != "Não informado no RDAP público.":
                            break
                
                # Método 3: Buscar informações do registrar
                for entity in data.get("entities", []):
                    roles = entity.get("roles", [])
                    if "registrar" in roles or "registrar" in [r.lower() for r in roles]:
                        vcard = entity.get("vcardArray", [])
                        if len(vcard) > 1:
                            properties = vcard[1]
                            for prop in properties:
                                if prop[0] == "fn":
                                    registrar = prop[3]
                                    break
                                elif prop[0] == "org":
                                    registrar = prop[3]
                                    break
                        break
                
                # Método 4: Buscar em handle se ainda não encontrou
                if owner_info == "Não informado no RDAP público.":
                    for entity in data.get("entities", []):
                        handle = entity.get("handle", "")
                        if handle and "registrant" in handle.lower():
                            owner_info = handle
                            break
                
                events = []
                for event in data.get("events", []):
                    action = event.get("eventAction", "")
                    date = event.get("eventDate", "")
                    events.append(f"- {action}: {date}")
                
                details = (
                    f"Domínio: {ldh_name}\n"
                    f"Dono/Registrante: {owner_info}\n"
                    f"Registrar: {registrar}\n"
                    f"Status: {', '.join(status_list)}\n\n"
                    f"Eventos:\n" + "\n".join(events)
                )
                
                summary = f"Dono: {owner_info}"
                if registrar != "Não informado":
                    summary += f" | Registrar: {registrar}"
                
                results.append(CheckResult(
                    check_id="rdap_whois", category="WHOIS & RDAP", title="Consulta RDAP",
                    status=CheckStatus.SUCCESS, summary=summary,
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
