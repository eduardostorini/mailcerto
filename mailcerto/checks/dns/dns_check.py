import asyncio
import time
from datetime import datetime
import dns.asyncresolver
from mailcerto.core.models import CheckResult, CheckStatus

async def perform_dns_check(target: str, record_type: str) -> CheckResult:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    
    check_id = f"dns_{record_type.lower()}"
    title = f"Registro DNS {record_type}"
    category = "DNS"

    try:
        # Resolver using system defaults, or fallback to Google DNS if needed
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        
        answer = await resolver.resolve(target, record_type)
        rdata_list = [rdata.to_text() for rdata in answer]
        ttl = answer.ttl
        
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        details = f"Registros encontrados:\n" + "\n".join(f"- {r}" for r in rdata_list)
        summary = f"Encontrado(s) {len(rdata_list)} registro(s) {record_type} para {target}."
        
        raw_data = {
            "record_type": record_type,
            "target": target,
            "ttl": ttl,
            "records": rdata_list
        }
        
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.SUCCESS,
            summary=summary,
            details=details,
            response_time_ms=elapsed,
            score=100,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            raw_data=raw_data
        )

    except dns.resolver.NoAnswer as e:
        print(f"[DNS RESOLVER NO ANSWER ERROR] target={target} record_type={record_type} err={str(e)}")
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.INFO,
            summary=f"Nenhum registro {record_type} encontrado para {target}.",
            details=f"Erro de DNS: {str(e)}\n\nO servidor DNS respondeu com sucesso, mas este registro específico está vazio ou não existe.",
            recommendation=f"Se você precisa deste tipo de registro, configure-o em seu provedor de DNS.",
            response_time_ms=elapsed,
            score=100,
            started_at=started_at,
            finished_at=datetime.utcnow()
        )
    except dns.resolver.NXDOMAIN as e:
        print(f"[DNS RESOLVER NXDOMAIN ERROR] target={target} record_type={record_type} err={str(e)}")
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.ERROR,
            summary=f"Domínio {target} não existe (NXDOMAIN).",
            details=f"Erro de DNS: {str(e)}\n\nNão foi possível resolver o domínio informado porque ele não está registrado ou não possui nameservers válidos.",
            recommendation="Verifique a ortografia do domínio ou confirme se ele está registrado e ativo.",
            response_time_ms=elapsed,
            score=0,
            started_at=started_at,
            finished_at=datetime.utcnow()
        )
    except Exception as e:
        print(f"[DNS RESOLVER GENERIC ERROR] target={target} record_type={record_type} err={str(e)}")
        import traceback
        traceback.print_exc()
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.WARNING,
            summary=f"Erro ao consultar registro {record_type}.",
            details=f"Exceção capturada: {str(e)}\n\n{traceback.format_exc()}",
            recommendation="Verifique a conectividade de rede e tente novamente.",
            response_time_ms=elapsed,
            score=0,
            started_at=started_at,
            finished_at=datetime.utcnow()
        )
