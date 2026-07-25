import re
import dns.asyncresolver
from mailcerto.core.models import CheckResult, CheckStatus
from datetime import datetime
import time

async def check_spf(domain: str) -> list[CheckResult]:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []

    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        answers = await resolver.resolve(domain, 'TXT')
        
        spf_records = []
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=spf1"):
                spf_records.append(txt)

        elapsed = (time.perf_counter() - t0) * 1000.0

        if not spf_records:
            results.append(CheckResult(
                check_id="email_spf_existence",
                category="Autenticação",
                title="Registro SPF",
                status=CheckStatus.WARNING,
                summary="Registro SPF não encontrado.",
                details="Não foi localizado nenhum registro TXT começando com 'v=spf1'.",
                recommendation="Crie um registro TXT com a política de e-mails autorizados para evitar falsificação (spoofing).",
                response_time_ms=elapsed
            ))
        elif len(spf_records) > 1:
            results.append(CheckResult(
                check_id="email_spf_multi",
                category="Autenticação",
                title="Múltiplos Registros SPF",
                status=CheckStatus.CRITICAL,
                summary="Detectado mais de um registro SPF.",
                details="\n".join(spf_records),
                recommendation="Remova os registros duplicados e unifique a política em um único registro TXT.",
                response_time_ms=elapsed
            ))
        else:
            spf = spf_records[0]
            # Validação simples de política restritiva
            status = CheckStatus.SUCCESS
            summary = "Registro SPF válido encontrado."
            recommendation = None
            if "+all" in spf:
                status = CheckStatus.WARNING
                summary = "SPF com política +all (permissiva)."
                recommendation = "Substitua +all por ~all ou -all para impedir que qualquer servidor envie e-mails em seu nome."
            
            results.append(CheckResult(
                check_id="email_spf_existence",
                category="Autenticação",
                title="Registro SPF",
                status=status,
                summary=summary,
                details=f"Registro: {spf}",
                recommendation=recommendation,
                response_time_ms=elapsed
            ))

    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="email_spf_existence",
            category="Autenticação",
            title="Registro SPF",
            status=CheckStatus.ERROR,
            summary="Erro ao consultar SPF.",
            details=str(e),
            response_time_ms=elapsed
        ))

    return results

async def check_dmarc(domain: str) -> list[CheckResult]:
    started_at = datetime.utcnow()
    t0 = time.perf_counter()
    results = []
    dmarc_domain = f"_dmarc.{domain}"

    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0
        answers = await resolver.resolve(dmarc_domain, 'TXT')
        
        dmarc_records = []
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=DMARC1"):
                dmarc_records.append(txt)

        elapsed = (time.perf_counter() - t0) * 1000.0

        if not dmarc_records:
            results.append(CheckResult(
                check_id="email_dmarc_existence",
                category="Autenticação",
                title="Registro DMARC",
                status=CheckStatus.CRITICAL,
                summary="Registro DMARC ausente.",
                details="Não foi encontrado um registro TXT em " + dmarc_domain,
                recommendation="Configure o DMARC para monitorar e proteger seu domínio contra abuso de marca.",
                response_time_ms=elapsed
            ))
        else:
            dmarc = dmarc_records[0]
            status = CheckStatus.SUCCESS
            summary = "DMARC configurado corretamente."
            recommendation = None
            
            if "p=none" in dmarc:
                status = CheckStatus.INFO
                summary = "DMARC em modo apenas monitoramento (p=none)."
                recommendation = "Recomenda-se evoluir a política para p=quarantine ou p=reject após a fase de testes."

            results.append(CheckResult(
                check_id="email_dmarc_existence",
                category="Autenticação",
                title="Registro DMARC",
                status=status,
                summary=summary,
                details=f"Registro: {dmarc}",
                recommendation=recommendation,
                response_time_ms=elapsed
            ))

    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        results.append(CheckResult(
            check_id="email_dmarc_existence",
            category="Autenticação",
            title="Registro DMARC",
            status=CheckStatus.WARNING,
            summary="DMARC ausente ou erro de consulta.",
            details=str(e),
            recommendation="Configure o registro TXT em _dmarc.seu-dominio para ativar o DMARC.",
            response_time_ms=elapsed
        ))

    return results
