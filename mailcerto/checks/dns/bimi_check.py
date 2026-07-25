import asyncio
import time
from datetime import datetime
import dns.asyncresolver
import re
from mailcerto.core.models import CheckResult, CheckStatus

async def perform_bimi_check(target: str) -> CheckResult:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    
    check_id = "bimi_check"
    title = "Verificação BIMI (Brand Indicators for Message Identification)"
    category = "BIMI"

    try:
        # BIMI uses a TXT record at default._bimi.domain
        bimi_domain = f"default._bimi.{target}"
        
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        
        answer = await resolver.resolve(bimi_domain, "TXT")
        rdata_list = [rdata.to_text() for rdata in answer]
        
        elapsed = (time.perf_counter() - t0) * 1000.0
        
        details_list = []
        summary_parts = []
        
        # Parse BIMI records
        bimi_records = []
        for r in rdata_list:
            # Remove quotes from TXT records
            cleaned = r.strip('"')
            bimi_records.append(cleaned)
            details_list.append(f"- Registro: {cleaned}")
        
        # Check for required BIMI components
        has_v_bimi = any("v=BIMI1" in record for record in bimi_records)
        has_certificate = any("https://" in record for record in bimi_records)
        
        summary_parts.append(f"Encontrado(s) {len(bimi_records)} registro(s) BIMI")
        
        if has_v_bimi:
            summary_parts.append("versão BIMI1 detectada")
        if has_certificate:
            summary_parts.append("certificado detectado")
        
        summary = "BIMI: " + ", ".join(summary_parts)
        details = "Registros BIMI Encontrados:\n" + "\n".join(details_list)
        
        # Add recommendations
        recommendation = ""
        if not has_v_bimi:
            recommendation = "O registro BIMI não contém a versão BIMI1. Verifique a configuração do registro."
        elif not has_certificate:
            recommendation = "O registro BIMI não contém URL de certificado. Para exibição completa do logo, é necessário um certificado VMC."
        else:
            recommendation = "Configuração BIMI básica detectada. Verifique se o certificado VMC está válido e acessível."
        
        raw_data = {
            "record_type": "TXT",
            "target": bimi_domain,
            "records": bimi_records,
            "has_v_bimi": has_v_bimi,
            "has_certificate": has_certificate
        }
        
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.SUCCESS,
            summary=summary,
            details=details,
            recommendation=recommendation,
            response_time_ms=elapsed,
            score=100 if has_v_bimi else 50,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            raw_data=raw_data
        )

    except dns.resolver.NoAnswer as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.INFO,
            summary=f"Nenhum registro BIMI encontrado para {target}.",
            details=f"Erro de DNS: {str(e)}\n\nO domínio não possui registros BIMI configurados em default._bimi.{target}.",
            recommendation="Para implementar BIMI, você precisa criar um registro TXT em default._bimi.seudominio.com com o formato: v=BIMI1; l=https://seudominio.com/logo.svg; a=https://seudominio.com/cert.pem",
            response_time_ms=elapsed,
            score=0,
            started_at=started_at,
            finished_at=datetime.utcnow()
        )
    except dns.resolver.NXDOMAIN as e:
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
        import traceback
        elapsed = (time.perf_counter() - t0) * 1000.0
        return CheckResult(
            check_id=check_id,
            category=category,
            title=title,
            status=CheckStatus.WARNING,
            summary=f"Erro ao consultar registro BIMI.",
            details=f"Exceção capturada: {str(e)}\n\n{traceback.format_exc()}",
            recommendation="Verifique a conectividade de rede e tente novamente.",
            response_time_ms=elapsed,
            score=0,
            started_at=started_at,
            finished_at=datetime.utcnow()
        )
