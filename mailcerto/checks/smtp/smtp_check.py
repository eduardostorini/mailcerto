import socket
import ssl
import time
from datetime import datetime
from mailcerto.core.models import CheckResult, CheckStatus

async def perform_smtp_check(domain: str) -> list[CheckResult]:
    # Como SMTP precisa resolver MX antes de conectar, primeiro descobrimos o MX
    # Faremos uma resolução simples de socket/dns
    results = []
    t0 = time.perf_counter()
    
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = sorted(answers, key=lambda r: r.preference)
        if not mx_records:
            raise Exception("Nenhum servidor MX encontrado.")
        
        mx_host = str(mx_records[0].exchange).rstrip('.')
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return [CheckResult(
            check_id="smtp_mx_resolve",
            category="SMTP",
            title="Conexão SMTP (MX)",
            status=CheckStatus.ERROR,
            summary="Não foi possível determinar o servidor MX.",
            details=str(e),
            response_time_ms=elapsed
        )]

    # Conectar na porta 25 (padrão de mail server)
    t_conn = time.perf_counter()
    try:
        # Usando socket de forma assíncrona simples via run_in_executor
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _connect():
            s = socket.create_connection((mx_host, 25), timeout=5.0)
            banner = s.recv(1024).decode('utf-8', errors='ignore')
            s.sendall(b"EHLO mailcerto.local\r\n")
            ehlo_resp = s.recv(1024).decode('utf-8', errors='ignore')
            s.close()
            return banner, ehlo_resp
            
        banner, ehlo_resp = await loop.run_in_executor(None, _connect)
        elapsed = (time.perf_counter() - t_conn) * 1000.0
        
        results.append(CheckResult(
            check_id="smtp_connect",
            category="SMTP",
            title="Conectividade SMTP (Porta 25)",
            status=CheckStatus.SUCCESS,
            summary=f"Conectado com sucesso ao servidor MX: {mx_host}.",
            details=f"Banner recebido:\n{banner}\n\nResposta EHLO:\n{ehlo_resp}",
            response_time_ms=elapsed
        ))
    except Exception as e:
        elapsed = (time.perf_counter() - t_conn) * 1000.0
        results.append(CheckResult(
            check_id="smtp_connect",
            category="SMTP",
            title="Conectividade SMTP (Porta 25)",
            status=CheckStatus.CRITICAL,
            summary=f"Falha na conexão SMTP com {mx_host}.",
            details=str(e),
            recommendation="Certifique-se de que a porta 25 está aberta no seu firewall e que o servidor de e-mail está online.",
            response_time_ms=elapsed
        ))
        
    return results
