import dns.asyncresolver
import dns.rdatatype
from mailcerto.core.models import CheckResult, CheckStatus
from datetime import datetime
import time

async def check_dnssec(domain: str) -> list[CheckResult]:
    """Check DNSSEC validation for the domain"""
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []
    
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 10.0
        resolver.lifetime = 10.0
        
        # Try to resolve with DNSSEC validation
        # First, check if the resolver supports DNSSEC
        resolver.flags |= dns.flags.AD
        
        # Query for DNSKEY records
        try:
            dnskey_answer = await resolver.resolve(domain, 'DNSKEY')
            elapsed = (time.perf_counter() - t0) * 1000.0
            
            if dnskey_answer.flags & dns.flags.AD:
                # AD flag means the answer was authenticated
                dnskey_count = len(dnskey_answer)
                
                results.append(CheckResult(
                    check_id="dnssec_validation",
                    category="DNSSEC",
                    title="Validação DNSSEC",
                    status=CheckStatus.SUCCESS,
                    summary=f"DNSSEC está ativo e validado ({dnskey_count} chaves DNSKEY encontradas)",
                    details=f"O domínio {domain} possui DNSSEC configurado e a validação foi bem-sucedida.\n\nChaves DNSKEY encontradas: {dnskey_count}",
                    recommendation="DNSSEC está funcionando corretamente. Continue monitorando a validação.",
                    response_time_ms=elapsed,
                    score=100
                ))
            else:
                # DNSKEY exists but not authenticated
                results.append(CheckResult(
                    check_id="dnssec_validation",
                    category="DNSSEC",
                    title="Validação DNSSEC",
                    status=CheckStatus.WARNING,
                    summary="DNSKEY encontrado mas não autenticado",
                    details=f"Registros DNSKEY foram encontrados para {domain}, mas a validação DNSSEC não foi confirmada (flag AD não definida).",
                    recommendation="Verifique se a cadeia de confiança DNSSEC está completa e se os registros DS estão configurados corretamente no registrador.",
                    response_time_ms=elapsed,
                    score=50
                ))
                
        except dns.resolver.NoAnswer:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="dnssec_existence",
                category="DNSSEC",
                title="Registro DNSKEY",
                status=CheckStatus.WARNING,
                summary="Nenhum registro DNSKEY encontrado",
                details=f"O domínio {domain} não possui registros DNSKEY, indicando que DNSSEC não está configurado.",
                recommendation="Configure DNSSEC para proteger seu domínio contra ataques de envenenamento de cache DNS. Consulte seu registrador para habilitar DNSSEC.",
                response_time_ms=elapsed,
                score=0
            ))
            
        except dns.resolver.NXDOMAIN:
            elapsed = (time.perf_counter() - t0) * 1000.0
            results.append(CheckResult(
                check_id="dnssec_validation",
                category="DNSSEC",
                title="Validação DNSSEC",
                status=CheckStatus.ERROR,
                summary=f"Domínio {domain} não existe",
                details="Não foi possível verificar DNSSEC porque o domínio não existe.",
                recommendation="Verifique a ortografia do domínio.",
                response_time_ms=elapsed,
                score=0
            ))
            
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="dnssec_validation",
            category="DNSSEC",
            title="Validação DNSSEC",
            status=CheckStatus.ERROR,
            summary="Erro ao verificar DNSSEC",
            details=f"Exceção: {str(e)}",
            recommendation="Verifique a conectividade de rede e tente novamente. O resolvedor DNS pode não suportar DNSSEC.",
            response_time_ms=elapsed,
            score=0
        ))
    
    return results
