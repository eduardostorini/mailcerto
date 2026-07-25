import socket
import struct
import time
from datetime import datetime
import asyncio
from mailcerto.core.models import CheckResult, CheckStatus

# Catálogo embutido de servidores DNSBL recomendados
DEFAULT_DNSBL_PROVIDERS = [
    {"name": "Spamhaus ZEN", "zone": "zen.spamhaus.org", "type": "ipv4"},
    {"name": "Spamcop", "zone": "bl.spamcop.net", "type": "ipv4"},
    {"name": "Barracuda BRBL", "zone": "b.barracudacentral.org", "type": "ipv4"},
    {"name": "Sorbs DUHL", "zone": "dnsbl.sorbs.net", "type": "ipv4"},
    {"name": "Abuse.ch Feodo", "zone": "badips.abuse.ch", "type": "ipv4"}
]

async def check_dnsbl_single(ip: str, zone: str, provider_name: str) -> CheckResult:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    check_id = f"dnsbl_{provider_name.lower().replace(' ', '_')}"
    
    # Para consultar DNSBL, invertemos o IP: e.g. 1.2.3.4 vira 4.3.2.1.zone
    try:
        octets = ip.split('.')
        query_host = f"{octets[3]}.{octets[2]}.{octets[1]}.{octets[0]}.{zone}"
    except Exception:
        return CheckResult(
            check_id=check_id, category="Reputação", title=provider_name,
            status=CheckStatus.ERROR, summary="IP inválido para consulta DNSBL.",
            response_time_ms=0
        )

    try:
        import dns.asyncresolver
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 3.0
        resolver.lifetime = 3.0
        
        answer = await resolver.resolve(query_host, 'A')
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        # Se retornou um registro A (geralmente na subrede 127.0.0.0/8), o IP está listado
        rdata_list = [rdata.to_text() for rdata in answer]
        
        return CheckResult(
            check_id=check_id,
            category="Reputação",
            title=provider_name,
            status=CheckStatus.CRITICAL,
            summary=f"Listado na blacklist {provider_name}!",
            details=f"Retornos da consulta: {', '.join(rdata_list)}\nEndereço de consulta: {query_host}",
            recommendation="Verifique o motivo da listagem no site oficial da blacklist para solicitar a remoção.",
            response_time_ms=elapsed
        )
    except dns.resolver.NXDOMAIN:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category="Reputação",
            title=provider_name,
            status=CheckStatus.SUCCESS,
            summary=f"Limpo na blacklist {provider_name}.",
            details=f"O servidor DNS respondeu que o IP não está listado (NXDOMAIN).",
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category="Reputação",
            title=provider_name,
            status=CheckStatus.WARNING,
            summary=f"Consulta indisponível ou falhou.",
            details=str(e),
            response_time_ms=elapsed
        )
