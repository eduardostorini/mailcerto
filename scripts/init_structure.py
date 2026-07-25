import os
import sys

# Criar a estrutura básica de diretórios
dirs = [
    "mailcerto",
    "mailcerto/core",
    "mailcerto/checks",
    "mailcerto/checks/dns",
    "mailcerto/checks/email",
    "mailcerto/checks/smtp",
    "mailcerto/checks/tls",
    "mailcerto/checks/reputation",
    "mailcerto/checks/http",
    "mailcerto/checks/network",
    "mailcerto/checks/rdap",
    "mailcerto/database",
    "mailcerto/services",
    "mailcerto/ui",
    "mailcerto/ui/pages",
    "mailcerto/ui/widgets",
    "mailcerto/resources",
    "mailcerto/resources/dnsbl",
    "mailcerto/resources/themes",
    "mailcerto/reports",
    "mailcerto/reports/templates",
    "tests",
    "tests/unit",
    "tests/integration",
    "scripts"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    init_py = os.path.join(d, "__init__.py")
    if "resources" not in d and "templates" not in d and "scripts" not in d:
        with open(init_py, "w", encoding="utf-8") as f:
            f.write("")

print("Diretórios e pacotes do MailCerto criados com sucesso!")
