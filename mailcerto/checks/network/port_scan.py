import socket
import time
import asyncio
from datetime import datetime
from mailcerto.core.models import CheckResult, CheckStatus

# Portas de mercado mais comuns e importantes para servidores de e-mail e web
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP (E-mail)",
    53: "DNS",
    80: "HTTP (Web)",
    110: "POP3 (E-mail)",
    143: "IMAP (E-mail)",
    443: "HTTPS (Web)",
    465: "SMTPS (E-mail SSL)",
    587: "SMTP Submission (STARTTLS)",
    993: "IMAPS (E-mail SSL)",
    995: "POP3S (E-mail SSL)",
    2525: "SMTP Alternativo",
    3306: "MySQL",
    5432: "PostgreSQL",
    8080: "HTTP Alternativo"
}

async def scan_single_port(ip: str, port: int, service_name: str) -> CheckResult:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    check_id = f"port_scan_{port}"
    
    try:
        # Tenta conexão TCP de forma assíncrona simples usando run_in_executor
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _connect():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0) # Timeout curto de 2 segundos para scanner ágil
            result = s.connect_ex((ip, port))
            s.close()
            return result
            
        conn_code = await loop.run_in_executor(None, _connect)
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        if conn_code == 0:
            return CheckResult(
                check_id=check_id,
                category="Portas",
                title=f"Porta {port} ({service_name})",
                status=CheckStatus.SUCCESS,
                summary=f"Porta {port} está ABERTA.",
                details=f"Conexão TCP estabelecida com sucesso na porta {port}.",
                response_time_ms=elapsed
            )
        else:
            return CheckResult(
                check_id=check_id,
                category="Portas",
                title=f"Porta {port} ({service_name})",
                status=CheckStatus.INFO,
                summary=f"Porta {port} está fechada ou filtrada.",
                details=f"O socket retornou código de erro: {conn_code}.",
                response_time_ms=elapsed
            )
            
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category="Portas",
            title=f"Porta {port} ({service_name})",
            status=CheckStatus.WARNING,
            summary=f"Falha ao escanear porta {port}.",
            details=str(e),
            response_time_ms=elapsed
        )
