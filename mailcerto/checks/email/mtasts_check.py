import dns.asyncresolver
import httpx
from mailcerto.core.models import CheckResult, CheckStatus
from datetime import datetime
import time
import re

async def check_mtasts(domain: str) -> list[CheckResult]:
    """Check MTA-STS (SMTP Strict Transport Security) policy"""
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []
    
    # Step 1: Check for MTA-STS DNS record
    mtasts_dns_domain = f"_mta-sts.{domain}"
    
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        
        dns_answer = await resolver.resolve(mtasts_dns_domain, 'TXT')
        
        mtasts_records = []
        for rdata in dns_answer:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=STSv1"):
                mtasts_records.append(txt)
        
        if not mtasts_records:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="mtasts_dns",
                category="MTA-STS",
                title="Registro DNS MTA-STS",
                status=CheckStatus.INFO,
                summary="Nenhum registro MTA-STS encontrado",
                details=f"Não foi encontrado registro TXT em {mtasts_dns_domain}",
                recommendation="Configure MTA-STS para exigir TLS em todas as conexões SMTP. Isso protege contra ataques de downgrade TLS.",
                response_time_ms=elapsed,
                score=0
            ))
            return results
            
        # Step 2: Fetch and validate MTA-STS policy from HTTPS
        mtasts_record = mtasts_records[0]
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        # Extract ID from DNS record
        id_match = re.search(r'id=([a-zA-Z0-9]+)', mtasts_record)
        dns_id = id_match.group(1) if id_match else None
        
        results.append(CheckResult(
            check_id="mtasts_dns",
            category="MTA-STS",
            title="Registro DNS MTA-STS",
            status=CheckStatus.SUCCESS,
            summary=f"Registro MTA-STS encontrado (ID: {dns_id})",
            details=f"Registro DNS: {mtasts_record}",
            response_time_ms=elapsed,
            score=100
        ))
        
        # Step 3: Fetch policy from HTTPS
        policy_url = f"https://mta-sts.{domain}/.well-known/mta-sts.txt"
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                policy_response = await client.get(policy_url)
                policy_elapsed = (time.perf_counter() - t0) * 1000.0
                
                if policy_response.status_code == 200:
                    policy_content = policy_response.text
                    
                    # Parse MTA-STS policy
                    policy_info = parse_mtasts_policy(policy_content)
                    
                    # Validate policy ID matches DNS
                    policy_id = policy_info.get('id', '')
                    
                    if dns_id and policy_id != dns_id:
                        results.append(CheckResult(
                            check_id="mtasts_policy",
                            category="MTA-STS",
                            title="Validação de Política MTA-STS",
                            status=CheckStatus.CRITICAL,
                            summary=f"ID da política não corresponde ao DNS",
                            details=f"ID DNS: {dns_id}\nID Política: {policy_id}\n\nPolítica:\n{policy_content}",
                            recommendation="O ID da política deve corresponder ao registro DNS. Atualize o registro DNS ou a política.",
                            response_time_ms=policy_elapsed,
                            score=0
                        ))
                    else:
                        mode = policy_info.get('mode', 'unknown')
                        
                        if mode == 'enforce':
                            status = CheckStatus.SUCCESS
                            summary = "MTA-STS em modo enforce (TLS obrigatório)"
                            score = 100
                        elif mode == 'testing':
                            status = CheckStatus.INFO
                            summary = "MTA-STS em modo testing (monitoramento)"
                            score = 75
                        elif mode == 'none':
                            status = CheckStatus.WARNING
                            summary = "MTA-STS em modo none (desativado)"
                            score = 25
                        else:
                            status = CheckStatus.WARNING
                            summary = f"MTA-STS com modo desconhecido: {mode}"
                            score = 50
                        
                        results.append(CheckResult(
                            check_id="mtasts_policy",
                            category="MTA-STS",
                            title="Política MTA-STS",
                            status=status,
                            summary=summary,
                            details=f"URL: {policy_url}\n\n{policy_info}\n\nPolítica completa:\n{policy_content}",
                            recommendation="Recomenda-se usar modo 'enforce' após testes para máxima segurança.",
                            response_time_ms=policy_elapsed,
                            score=score
                        ))
                        
                else:
                    results.append(CheckResult(
                        check_id="mtasts_policy",
                        category="MTA-STS",
                        title="Política MTA-STS",
                        status=CheckStatus.ERROR,
                        summary=f"Política não acessível (HTTP {policy_response.status_code})",
                        details=f"Não foi possível acessar a política em {policy_url}",
                        recommendation="Verifique se o servidor mta-sts.{domain} está configurado corretamente e servindo o arquivo .well-known/mta-sts.txt",
                        response_time_ms=policy_elapsed,
                        score=0
                    ))
                    
        except Exception as e:
            policy_elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="mtasts_policy",
                category="MTA-STS",
                title="Política MTA-STS",
                status=CheckStatus.ERROR,
                summary="Erro ao buscar política MTA-STS",
                details=f"Exceção: {str(e)}",
                recommendation="Verifique a conectividade e a configuração HTTPS do servidor mta-sts.{domain}",
                response_time_ms=policy_elapsed,
                score=0
            ))
            
    except dns.resolver.NoAnswer:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="mtasts_dns",
            category="MTA-STS",
            title="Registro DNS MTA-STS",
            status=CheckStatus.INFO,
            summary="MTA-STS não configurado",
            details=f"Não foi encontrado registro TXT em {mtasts_dns_domain}",
            recommendation="Configure MTA-STS para proteger conexões SMTP contra ataques de downgrade TLS.",
            response_time_ms=elapsed,
            score=0
        ))
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="mtasts_dns",
            category="MTA-STS",
            title="Registro DNS MTA-STS",
            status=CheckStatus.ERROR,
            summary="Erro ao verificar MTA-STS",
            details=f"Exceção: {str(e)}",
            response_time_ms=elapsed,
            score=0
        ))
    
    return results

def parse_mtasts_policy(policy_content: str) -> dict:
    """Parse MTA-STS policy content"""
    info = {}
    lines = policy_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'mx':
                if 'mx' not in info:
                    info['mx'] = []
                info['mx'].append(value)
            else:
                info[key] = value
    
    return info
