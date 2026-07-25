import httpx
import time
from datetime import datetime
from mailcerto.core.models import CheckResult, CheckStatus

async def check_http_security(domain: str) -> list[CheckResult]:
    results = []
    
    # 1. Test HTTP Redirection to HTTPS
    t0 = time.perf_counter()
    url_http = f"http://{domain}"
    url_https = f"https://{domain}"
    
    headers = {
        "User-Agent": "MailCerto/1.0.0 Diagnostic Tool"
    }

    async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
        try:
            resp = await client.get(url_http, headers=headers, follow_redirects=False)
            elapsed = (time.perf_counter() - t0) * 1000.0
            
            if resp.status_code in [301, 302, 307, 308] and "location" in resp.headers:
                location = resp.headers["location"]
                if location.startswith("https://"):
                    results.append(CheckResult(
                        check_id="http_https_redirect", category="HTTP & Segurança",
                        title="Redirecionamento HTTPS", status=CheckStatus.SUCCESS,
                        summary="Redirecionamento HTTP para HTTPS ativo.",
                        details=f"Status: {resp.status_code}\nRedirecionado para: {location}",
                        response_time_ms=elapsed
                    ))
                else:
                    results.append(CheckResult(
                        check_id="http_https_redirect", category="HTTP & Segurança",
                        title="Redirecionamento HTTPS", status=CheckStatus.WARNING,
                        summary="HTTP redireciona, mas não para HTTPS.",
                        details=f"Status: {resp.status_code}\nRedirecionado para: {location}",
                        recommendation="Configure o redirecionamento automático de tráfego HTTP para HTTPS seguro.",
                        response_time_ms=elapsed
                    ))
            else:
                results.append(CheckResult(
                    check_id="http_https_redirect", category="HTTP & Segurança",
                    title="Redirecionamento HTTPS", status=CheckStatus.WARNING,
                    summary="O site HTTP não força redirecionamento para HTTPS.",
                    details=f"Status retornado: {resp.status_code}",
                    recommendation="Force conexões HTTPS seguras para proteger dados em trânsito.",
                    response_time_ms=elapsed
                ))
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="http_https_redirect", category="HTTP & Segurança",
                title="Redirecionamento HTTPS", status=CheckStatus.INFO,
                summary="HTTP inacessível ou sem resposta de redirecionamento.",
                details=str(e),
                response_time_ms=elapsed
            ))

    # 2. Test Security Headers on HTTPS
    t1 = time.perf_counter()
    async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
        try:
            resp = await client.get(url_https, headers=headers, follow_redirects=True)
            elapsed_https = (time.perf_counter() - t1) * 1000.0
            
            # Check for HSTS (Strict-Transport-Security)
            hsts = resp.headers.get("Strict-Transport-Security")
            if hsts:
                results.append(CheckResult(
                    check_id="http_header_hsts", category="HTTP & Segurança",
                    title="Header HSTS", status=CheckStatus.SUCCESS,
                    summary="HSTS (Strict-Transport-Security) ativo.",
                    details=f"Valor do cabeçalho: {hsts}",
                    response_time_ms=elapsed_https
                ))
            else:
                results.append(CheckResult(
                    check_id="http_header_hsts", category="HTTP & Segurança",
                    title="Header HSTS", status=CheckStatus.WARNING,
                    summary="Strict-Transport-Security (HSTS) ausente.",
                    details="O HSTS instrui os navegadores a acessarem o site apenas via HTTPS.",
                    recommendation="Adicione o cabeçalho 'Strict-Transport-Security: max-age=63072000; includeSubDomains; preload' às suas respostas HTTPS.",
                    response_time_ms=elapsed_https
                ))
                
            # Check Content-Security-Policy (CSP)
            csp = resp.headers.get("Content-Security-Policy")
            if csp:
                results.append(CheckResult(
                    check_id="http_header_csp", category="HTTP & Segurança",
                    title="Header CSP", status=CheckStatus.SUCCESS,
                    summary="Content-Security-Policy ativo.",
                    details=f"CSP: {csp[:100]}...",
                    response_time_ms=elapsed_https
                ))
            else:
                results.append(CheckResult(
                    check_id="http_header_csp", category="HTTP & Segurança",
                    title="Header CSP", status=CheckStatus.INFO,
                    summary="Content-Security-Policy (CSP) ausente.",
                    recommendation="Configure uma política CSP robusta para mitigar ataques de Cross-Site Scripting (XSS).",
                    response_time_ms=elapsed_https
                ))
        except Exception as e:
            elapsed_https = (time.perf_counter() - t1) * 1000.0
            results.append(CheckResult(
                check_id="http_https_accessible", category="HTTP & Segurança",
                title="Acessibilidade HTTPS", status=CheckStatus.ERROR,
                summary="Não foi possível estabelecer conexão HTTPS segura.",
                details=str(e),
                response_time_ms=elapsed_https
            ))

    return results
