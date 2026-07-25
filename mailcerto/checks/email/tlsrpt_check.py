import dns.asyncresolver
import re
from mailcerto.core.models import CheckResult, CheckStatus
from datetime import datetime
import time

async def check_tlsrpt(domain: str) -> list[CheckResult]:
    """Check TLS-RPT (TLS Reporting) configuration"""
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []
    
    # TLS-RPT uses a TXT record at _smtp._tls.domain
    tlsrpt_domain = f"_smtp._tls.{domain}"
    
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        
        dns_answer = await resolver.resolve(tlsrpt_domain, 'TXT')
        
        tlsrpt_records = []
        for rdata in dns_answer:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=TLSRPTv1"):
                tlsrpt_records.append(txt)
        
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        if not tlsrpt_records:
            results.append(CheckResult(
                check_id="tlsrpt_dns",
                category="TLS-RPT",
                title="Registro DNS TLS-RPT",
                status=CheckStatus.INFO,
                summary="Nenhum registro TLS-RPT encontrado",
                details=f"Não foi encontrado registro TXT em {tlsrpt_domain}",
                recommendation="Configure TLS-RPT para receber relatórios sobre falhas TLS. Isso ajuda a monitorar e melhorar a segurança TLS.",
                response_time_ms=elapsed,
                score=0
            ))
        else:
            tlsrpt_record = tlsrpt_records[0]
            tlsrpt_info = parse_tlsrpt_record(tlsrpt_record)
            
            # Validate configuration
            rua = tlsrpt_info.get('rua', [])
            if not rua:
                status = CheckStatus.WARNING
                summary = "TLS-RPT configurado sem destinatários de relatório"
                score = 50
            else:
                status = CheckStatus.SUCCESS
                summary = f"TLS-RPT configurado ({len(rua)} destinatário(s))"
                score = 100
            
            results.append(CheckResult(
                check_id="tlsrpt_dns",
                category="TLS-RPT",
                title="Registro DNS TLS-RPT",
                status=status,
                summary=summary,
                details=f"Registro DNS: {tlsrpt_record}\n\n{tlsrpt_info}",
                recommendation="Verifique se os endereços de e-mail em 'rua' estão configurados para receber relatórios TLS.",
                response_time_ms=elapsed,
                score=score
            ))
            
    except dns.resolver.NoAnswer:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="tlsrpt_dns",
            category="TLS-RPT",
            title="Registro DNS TLS-RPT",
            status=CheckStatus.INFO,
            summary="TLS-RPT não configurado",
            details=f"Não foi encontrado registro TXT em {tlsrpt_domain}",
            recommendation="Configure TLS-RPT para monitorar falhas TLS e receber relatórios de segurança.",
            response_time_ms=elapsed,
            score=0
        ))
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="tlsrpt_dns",
            category="TLS-RPT",
            title="Registro DNS TLS-RPT",
            status=CheckStatus.ERROR,
            summary="Erro ao verificar TLS-RPT",
            details=f"Exceção: {str(e)}",
            response_time_ms=elapsed,
            score=0
        ))
    
    return results

def parse_tlsrpt_record(record: str) -> str:
    """Parse TLS-RPT record and extract information"""
    info_parts = []
    
    # Extract tags
    tags = re.findall(r'(\w+)=(\S+)', record)
    
    tag_dict = {}
    for tag, value in tags:
        tag_dict[tag] = value
    
    if 'v' in tag_dict:
        info_parts.append(f"Versão: {tag_dict['v']}")
    
    if 'rua' in tag_dict:
        rua_values = tag_dict['rua'].split(',')
        info_parts.append(f"Destinatários de relatório: {len(rua_values)}")
        for rua in rua_values[:3]:  # Show first 3
            info_parts.append(f"  - {rua}")
        if len(rua_values) > 3:
            info_parts.append(f"  ... e mais {len(rua_values) - 3}")
    
    if 'ruf' in tag_dict:
        ruf_values = tag_dict['ruf'].split(',')
        info_parts.append(f"Destinatários de falhas imediatas: {len(ruf_values)}")
    
    return "\n".join(info_parts) if info_parts else "Informações adicionais não disponíveis"
