import socket
import time
from datetime import datetime
import asyncio
from mailcerto.core.models import CheckResult, CheckStatus

async def check_network_diagnostics(domain: str) -> list[CheckResult]:
    results = []
    t0 = time.perf_counter()

    # 1. Host resolution
    try:
        ip = socket.gethostbyname(domain)
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="net_resolve", category="Rede", title="Resolução de Host",
            status=CheckStatus.SUCCESS, summary=f"Domínio {domain} resolvido para o IP {ip}.",
            details=f"IP resolvido: {ip}", response_time_ms=elapsed
        ))
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return [CheckResult(
            check_id="net_resolve", category="Rede", title="Resolução de Host",
            status=CheckStatus.CRITICAL, summary=f"Não foi possível resolver o IP de {domain}.",
            details=str(e), response_time_ms=elapsed
        )]

    # 2. Ping test (TCP connection test on standard ports like 80/443 as generic ping fallback)
    t1 = time.perf_counter()
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        def _ping_tcp():
            s = socket.create_connection((ip, 443), timeout=3.0)
            s.close()
        await loop.run_in_executor(None, _ping_tcp)
        elapsed_ping = (time.perf_counter() - t1) * 1000.0
        results.append(CheckResult(
            check_id="net_ping", category="Rede", title="Ping (TCP Porta 443)",
            status=CheckStatus.SUCCESS, summary=f"Conexão bem sucedida. Latência: {elapsed_ping:.1f}ms.",
            response_time_ms=elapsed_ping
        ))
    except Exception as e:
        elapsed_ping = (time.perf_counter() - t1) * 1000.0
        results.append(CheckResult(
            check_id="net_ping", category="Rede", title="Ping (TCP Porta 443)",
            status=CheckStatus.WARNING, summary=f"Sem resposta na porta 443 (HTTPS) após {elapsed_ping:.1f}ms.",
            details=str(e), response_time_ms=elapsed_ping
        ))

    return results
