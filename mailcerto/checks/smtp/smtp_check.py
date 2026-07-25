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
        
        def _check_starttls():
            s = socket.create_connection((mx_host, 25), timeout=10.0)
            banner = s.recv(1024).decode('utf-8', errors='ignore')
            s.sendall(b"EHLO mailcerto.local\r\n")
            ehlo_resp = s.recv(1024).decode('utf-8', errors='ignore')
            
            if "STARTTLS" not in ehlo_resp.upper():
                s.close()
                return False, "STARTTLS não suportado", banner, ehlo_resp
            
            s.sendall(b"STARTTLS\r\n")
            starttls_resp = s.recv(1024).decode('utf-8', errors='ignore')
            
            if "220" not in starttls_resp:
                s.close()
                return False, "STARTTLS falhou", banner, ehlo_resp
            
            # Upgrade to TLS
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            try:
                ssl_socket = context.wrap_socket(s, server_hostname=mx_host)
                ssl_socket.sendall(b"EHLO mailcerto.local\r\n")
                ssl_ehlo = ssl_socket.recv(1024).decode('utf-8', errors='ignore')
                ssl_socket.close()
                return True, "STARTTLS bem-sucedido", banner, ehlo_resp
            except Exception as e:
                s.close()
                return False, f"Erro TLS: {str(e)}", banner, ehlo_resp
            
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
        
        # Check STARTTLS
        t_starttls = time.perf_counter()
        starttls_success, starttls_msg, starttls_banner, starttls_ehlo = await loop.run_in_executor(None, _check_starttls)
        starttls_elapsed = (time.perf_counter() - t_starttls) * 1000.0
        
        if starttls_success:
            results.append(CheckResult(
                check_id="smtp_starttls",
                category="SMTP",
                title="STARTTLS",
                status=CheckStatus.SUCCESS,
                summary=f"STARTTLS suportado e funcional em {mx_host}",
                details=f"{starttls_msg}\n\nBanner:\n{starttls_banner}\n\nEHLO:\n{starttls_ehlo}",
                response_time_ms=starttls_elapsed,
                score=100
            ))
        else:
            results.append(CheckResult(
                check_id="smtp_starttls",
                category="SMTP",
                title="STARTTLS",
                status=CheckStatus.WARNING,
                summary=f"STARTTLS não disponível ou falhou em {mx_host}",
                details=f"{starttls_msg}\n\nBanner:\n{starttls_banner}\n\nEHLO:\n{starttls_ehlo}",
                recommendation="Configure STARTTLS no servidor SMTP para criptografar conexões de e-mail.",
                response_time_ms=starttls_elapsed,
                score=0
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
