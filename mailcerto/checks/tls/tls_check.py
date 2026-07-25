import ssl
import socket
import time
from datetime import datetime
from cryptography import x509
from mailcerto.core.models import CheckResult, CheckStatus

async def check_tls_cert(domain: str) -> list[CheckResult]:
    results = []
    t0 = time.perf_counter()

    try:
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _get_cert():
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5.0) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    return der_cert
                    
        der_cert = await loop.run_in_executor(None, _get_cert)
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        cert = x509.load_der_x509_certificate(der_cert)
        not_after = cert.not_valid_after_utc
        days_remaining = (not_after - datetime.now(not_after.tzinfo)).days
        
        status = CheckStatus.SUCCESS
        summary = f"Certificado TLS válido. Expira em {days_remaining} dias."
        
        if days_remaining < 15:
            status = CheckStatus.CRITICAL
            summary = f"Alerta crítico: Certificado expira em {days_remaining} dias!"
        elif days_remaining < 30:
            status = CheckStatus.WARNING
            summary = f"Aviso: Certificado expira em {days_remaining} dias."

        details = f"Sujeito: {cert.subject.rfc4514_string()}\nEmissor: {cert.issuer.rfc4514_string()}\nVálido até: {not_after.isoformat()}"

        results.append(CheckResult(
            check_id="tls_cert_expiry",
            category="TLS & Certificados",
            title="Validade do Certificado",
            status=status,
            summary=summary,
            details=details,
            response_time_ms=elapsed
        ))
        
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="tls_cert_expiry",
            category="TLS & Certificados",
            title="Validade do Certificado",
            status=CheckStatus.ERROR,
            summary="Falha ao inspecionar certificado SSL/TLS.",
            details=str(e),
            recommendation="Verifique se o domínio possui certificado HTTPS ativo na porta 443.",
            response_time_ms=elapsed
        ))

    return results
