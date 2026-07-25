import re
import dns.asyncresolver
import base64
import hashlib
from mailcerto.core.models import CheckResult, CheckStatus
from datetime import datetime
import time

async def check_dkim(domain: str) -> list[CheckResult]:
    """Check for DKIM records by searching for common selector patterns"""
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []
    
    # Common DKIM selectors to try
    common_selectors = [
        "default",
        "google",
        "k1",
        "smtp",
        "mail",
        "selector1",
        "selector2",
        "s1",
        "s2",
        "dkim",
        "domainkey"
    ]
    
    found_dkim = False
    found_selectors = []
    
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = 5.0
    resolver.lifetime = 5.0
    
    for selector in common_selectors:
        dkim_domain = f"{selector}._domainkey.{domain}"
        
        try:
            answers = await resolver.resolve(dkim_domain, 'TXT')
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith("v=DKIM1"):
                    found_dkim = True
                    found_selectors.append(selector)
                    
                    # Parse DKIM record
                    dkim_info = parse_dkim_record(txt)
                    
                    elapsed = (time.perf_counter() - t0) * 1000.0
                    
                    results.append(CheckResult(
                        check_id=f"email_dkim_{selector}",
                        category="Autenticação",
                        title=f"Registro DKIM ({selector})",
                        status=CheckStatus.SUCCESS,
                        summary=f"DKIM encontrado com seletor '{selector}'",
                        details=f"Seletor: {selector}\nRegistro: {txt}\n\n{dkim_info}",
                        response_time_ms=elapsed
                    ))
                    
        except dns.resolver.NXDOMAIN:
            continue
        except Exception as e:
            continue
    
    elapsed = (time.perf_counter() - t0) * 1000.0
    
    if not found_dkim:
        results.append(CheckResult(
            check_id="email_dkim_existence",
            category="Autenticação",
            title="Registro DKIM",
            status=CheckStatus.WARNING,
            summary="Nenhum registro DKIM encontrado com seletores comuns.",
            details="Não foi localizado nenhum registro DKIM usando seletores comuns (default, google, k1, smtp, mail, selector1, selector2, etc).",
            recommendation="Configure DKIM para seus servidores de e-mail. DKIM assina digitalmente seus e-mails para garantir que não foram modificados em trânsito.",
            response_time_ms=elapsed
        ))
    else:
        results.append(CheckResult(
            check_id="email_dkim_summary",
            category="Autenticação",
            title="Resumo DKIM",
            status=CheckStatus.SUCCESS,
            summary=f"Encontrado(s) {len(found_selectors)} registro(s) DKIM",
            details=f"Seletores encontrados: {', '.join(found_selectors)}",
            response_time_ms=elapsed
        ))
    
    return results

def parse_dkim_record(record: str) -> str:
    """Parse DKIM record and extract key information"""
    info_parts = []
    
    # Extract tags
    tags = re.findall(r'(\w+)=(\S+)', record)
    
    tag_dict = {}
    for tag, value in tags:
        tag_dict[tag] = value
    
    if 'v' in tag_dict:
        info_parts.append(f"Versão: {tag_dict['v']}")
    
    if 'k' in tag_dict:
        info_parts.append(f"Algoritmo de chave: {tag_dict['k']}")
    
    if 'p' in tag_dict:
        key_length = len(tag_dict['p'])
        info_parts.append(f"Chave pública presente ({key_length} caracteres)")
    
    if 'h' in tag_dict:
        info_parts.append(f"Algoritmos de hash permitidos: {tag_dict['h']}")
    
    if 't' in tag_dict:
        flags = tag_dict['t'].split(':')
        info_parts.append(f"Flags: {', '.join(flags)}")
    
    return "\n".join(info_parts) if info_parts else "Informações adicionais não disponíveis"
