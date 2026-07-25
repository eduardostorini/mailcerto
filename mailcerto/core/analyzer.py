import asyncio
from mailcerto.core.models import CheckResult, CheckStatus
from mailcerto.checks.dns.dns_check import perform_dns_check
from mailcerto.checks.email.auth_check import check_spf, check_dmarc
from mailcerto.checks.smtp.smtp_check import perform_smtp_check
from mailcerto.checks.tls.tls_check import check_tls_cert
from mailcerto.checks.reputation.blacklist_check import DEFAULT_DNSBL_PROVIDERS, check_dnsbl_single
from mailcerto.checks.http.http_check import check_http_security
from mailcerto.checks.network.network_check import check_network_diagnostics
from mailcerto.checks.network.ip_location import check_ip_location
from mailcerto.checks.rdap.rdap_check import check_rdap_whois
from datetime import datetime

class SuperAnalyzer:
    def __init__(self, target: str):
        self.target = target
        self.clean_domain = target.replace("https://", "").replace("http://", "").split("/")[0].strip()

    async def run_all_checks(self, callback_func) -> list[CheckResult]:
        """
        Executes all checks concurrently and reports results via callback_func.
        """
        # Preparar a lista de tarefas
        tasks = []

        # 1. DNS Tasks
        for r_type in ["A", "MX", "NS", "TXT", "SOA"]:
            tasks.append(self._run_and_callback(perform_dns_check(self.clean_domain, r_type), callback_func))

        # 2. Email Auth Tasks
        tasks.append(self._run_and_callback_list(check_spf(self.clean_domain), callback_func))
        tasks.append(self._run_and_callback_list(check_dmarc(self.clean_domain), callback_func))

        # 3. SMTP Connect Task
        tasks.append(self._run_and_callback_list(perform_smtp_check(self.clean_domain), callback_func))

        # 4. TLS Connect Task
        tasks.append(self._run_and_callback_list(check_tls_cert(self.clean_domain), callback_func))

        # 5. Blacklists ZEN & Spamcop
        for provider in DEFAULT_DNSBL_PROVIDERS[:2]: # Limit to top 2 to keep speed fast
            # We need an IP for DNSBL, resolved from domain
            tasks.append(self._run_dnsbl_and_callback(provider, callback_func))

        # 6. HTTP & Security Headers Task
        tasks.append(self._run_and_callback_list(check_http_security(self.clean_domain), callback_func))

        # 7. Network Diagnostics Task
        tasks.append(self._run_and_callback_list(check_network_diagnostics(self.clean_domain), callback_func))

        # 8. IP Geo-Location Task
        tasks.append(self._run_and_callback_list(check_ip_location(self.clean_domain), callback_func))

        # 9. RDAP Task
        tasks.append(self._run_and_callback_list(check_rdap_whois(self.clean_domain), callback_func))

        # Aguarda todas terminarem
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Unificar e retornar lista final
        flat_results = []
        for r in completed_results:
            if isinstance(r, list):
                flat_results.extend(r)
            elif isinstance(r, CheckResult):
                flat_results.append(r)
        return flat_results

    async def _run_and_callback(self, coro, callback):
        try:
            res = await coro
            callback(res)
            return res
        except Exception as e:
            err = CheckResult(
                check_id="generic_err", category="Super", title="Verificação",
                status=CheckStatus.ERROR, summary=str(e)
            )
            callback(err)
            return err

    async def _run_and_callback_list(self, coro, callback):
        try:
            results = await coro
            for r in results:
                callback(r)
            return results
        except Exception as e:
            err = CheckResult(
                check_id="generic_err", category="Super", title="Verificação",
                status=CheckStatus.ERROR, summary=str(e)
            )
            callback(err)
            return [err]

    async def _run_dnsbl_and_callback(self, provider, callback):
        try:
            import socket
            ip = await asyncio.get_running_loop().run_in_executor(None, socket.gethostbyname, self.clean_domain)
            res = await check_dnsbl_single(ip, provider["zone"], provider["name"])
            callback(res)
            return res
        except Exception as e:
            err = CheckResult(
                check_id=f"dnsbl_{provider['name'].lower()}", category="Reputação",
                title=provider["name"], status=CheckStatus.ERROR, summary=str(e)
            )
            callback(err)
            return err
