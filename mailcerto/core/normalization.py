import re
import ipaddress
from urllib.parse import urlparse
import tldextract

def detect_and_normalize_target(input_str: str) -> tuple[str, str]:
    """
    Detects the target type and normalizes it.
    Returns a tuple (normalized_value, target_type).
    Valid target types: "domain", "ip", "url", "email", "invalid"
    """
    cleaned = input_str.strip().lower()
    if not cleaned:
        return "", "invalid"

    # 1. Check IP
    # Try parsing as IPv4 or IPv6
    try:
        ip = ipaddress.ip_address(cleaned)
        return str(ip), "ip"
    except ValueError:
        pass

    # 2. Check Email
    email_regex = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    if email_regex.match(cleaned):
        return cleaned, "email"

    # 3. Check URL (with schemes)
    if cleaned.startswith(("http://", "https://")):
        try:
            parsed = urlparse(cleaned)
            hostname = parsed.hostname
            if hostname:
                return cleaned, "url"
        except Exception:
            pass

    # 4. Check domain/subdomain
    # Let's clean standard things like domain.com, sub.domain.com
    # If the user input has no scheme but has path like domain.com/abc, let's treat it carefully
    domain_candidate = cleaned
    if "/" in domain_candidate and not domain_candidate.startswith(("http://", "https://")):
        domain_candidate = domain_candidate.split("/")[0]

    # Validate domain using tldextract
    ext = tldextract.extract(domain_candidate)
    if ext.domain and ext.suffix:
        return domain_candidate, "domain"

    # If it is a host/domain like localhost or has a structure of labels
    domain_regex = re.compile(
        r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
    )
    if domain_regex.match(domain_candidate):
        return domain_candidate, "domain"

    return cleaned, "invalid"
