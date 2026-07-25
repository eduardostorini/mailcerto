# Changelog

Todos os cambios notáveis neste projeto serão documentados neste arquivo.

O formato está baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-01-XX

### ✨ Added

#### Funcionalidades Principais
- **Super Análise**: Execução paralela de todas as verificações com interface unificada
- **Análise DNS Completa**:
  - Registros MX (servidores de e-mail)
  - Registros TXT (SPF, DKIM, DMARC)
  - Registros A (IPv4)
  - Registros AAAA (IPv6)
  - Registros NS (servidores de nomes)
  - Registros CNAME (aliases)
  - Registros SOA (informações de zona)

#### Verificações de E-mail
- Validação SPF (Sender Policy Framework)
- Validação DKIM (DomainKeys Identified Mail)
- Validação DMARC (Domain-based Message Authentication)
- Teste de conectividade SMTP
- Verificação de TLS em conexões SMTP

#### Segurança
- Análise completa de certificados SSL/TLS
- Detecção de vulnerabilidades (Heartbleed, etc.)
- Verificação de reputação em blacklists DNSBL
- Análise de headers HTTP de segurança
- Scan de portas abertas

#### Rede
- Geo-localização de IPs com API pública
- Diagnósticos de latência e ping
- Consultas WHOIS/RDAP
- Informações de ISP e ASN

#### Interface Gráfica
- Interface moderna com PySide6
- Menu lateral com navegação intuitiva
- Histórico de análises com busca
- Temas personalizáveis (light/dark)
- Suporte a autocomplete de domínios
- Detalhes técnicos expandíveis
- Exportação de relatórios em PDF

#### Banco de Dados
- Persistência com SQLAlchemy
- Armazenamento de histórico de análises
- Cache de resultados

### 🔧 Technical

- Python 3.10+
- PySide6 para GUI
- Async/await com asyncio
- HTTPX para requisições HTTP
- dnspython para operações DNS
- Cryptography para análise SSL/TLS
- SQLAlchemy para ORM
