# Contribuindo para MailCerto

Obrigado por considerar contribuir para o MailCerto! É pessoas como você que tornam o MailCerto uma ferramenta tão útil.

## Como Contribuir

Existem muitas maneiras de contribuir, desde escrever tutoriais ou melhorar a documentação, até submeter relatórios de bugs e solicitar novas funcionalidades.

## v1.

### 🐛 Reportando Bugs

Antes de criar um relatório de bug, verifique a lista de issues pois você pode descobrir que não precisa criar um. Quando você está criando um relatório de bug, inclua o máximo de detalhes possível:

- **Use um título claro e descritivo**
- **Descreva os passos exatos que reproduzem o problema**
- **Forneça exemplos específicos para demonstrar os passos**
- **Descreva o comportamento observado e aponte exatamente qual é o problema**
- **Explique qual era o comportamento esperado**
- **Inclua screenshots se possível**
- **Inclua seu ambiente** (OS, versão do Python, versão do MailCerto, etc.)

### 💡 Sugerindo Melhorias

As sugestões de melhorias são rastreadas como issues do GitHub. Ao criar uma sugestão de melhoria, inclua:

- **Use um título claro e descritivo**
- **Forneça uma descrição passo a passo da melhoria sugerida**
- **Forneça exemplos específicos para demonstrar os passos**
- **Descreva o comportamento atual e mencione o comportamento esperado**
- **Explique por que essa melhoria seria útil**

### ✍️ Contribuindo com Código

Sugestões de pull request são bem-vindas! Para mudanças maiores, abra primeiro uma issue para discutir que mudanças você gostaria de fazer.

#### Processo de Desenvolvimento

1. **Fork o repositório**
   ```bash
   git clone https://github.com/seu-usuario/mailcerto.git
   ```

2. **Crie um branch para sua feature**
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **Setup do ambiente de desenvolvimento**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Faça suas mudanças**
   - Mantenha o código limpo e bem documentado
   - Adicione testes para novas funcionalidades
   - Atualize a documentação se necessário

5. **Rode os testes**
   ```bash
   pytest tests/
   ```

6. **Verifique a qualidade do código**
   ```bash
   black mailcerto/ tests/
   flake8 mailcerto/ tests/
   mypy mailcerto/
   ```

7. **Commit suas mudanças**
   ```bash
   git add .
   git commit -m 'Add some AmazingFeature'
   ```

8. **Push para a branch**
   ```bash
   git push origin feature/AmazingFeature
   ```

9. **Abra um Pull Request**

#### Diretrizes de Pull Request

- Siga o estilo de código do projeto (use `black` para formatting)
- Inclua testes apropriados para novas funcionalidades
- Atualize a documentação conforme necessário
- Use commits atômicos com mensagens claras
- Descreva claramente suas mudanças no PR

### 📚 Melhorando a Documentação

Documentação é super importante para qualquer projeto. Você pode ajudar:

- Melhorando arquivos README
- Adicionando exemplos de uso
- Escrevendo tutoriais
- Traduzindo documentação

## 🎨 Padrões de Código

### Python Style Guide

Seguimos [PEP 8](https://pep8.org/) com algumas extensões:

```python
# Use type hints
def analyze_domain(domain: str) -> CheckResult:
    """Analisa um domínio.
    
    Args:
        domain: O domínio a ser analisado
        
    Returns:
        Resultado da análise
        
    Raises:
        ValueError: Se o domínio for inválido
    """
    pass

# Use docstrings descritivas
class DomainAnalyzer:
    """Orquestrador de análises de domínio."""
    
    def __init__(self):
        """Inicializa o analisador."""
        self.results = []
```

### Commits

- Use mensagens de commit claras e descritivas
- Comece com um verbo (Add, Fix, Update, etc.)
- Referência issues quando apropriado: `Fix #123`

```
Add IP location feature to network checks

- Implemented check_ip_location function
- Added geo-location API integration
- Created IPLocationPage UI component

Fixes #42
```

### Tests

- Escreva testes para novas funcionalidades
- Mantenha cobertura acima de 80%
- Use nomes descritivos para funções de teste

```python
def test_domain_normalization_with_http_prefix():
    """Testa normalização de domínio com prefixo http."""
    result, target_type = detect_and_normalize_target("http://example.com")
    assert result == "example.com"
    assert target_type == "domain"
```

## 🏆 Processo de Review

- Pelo menos um maintainer deve revisar seu PR
- Todas as verificações automatizadas devem passar
- Toda a discussão deve ser respeitosa e construtiva

## 📝 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a Licença Apache 2.0 do projeto.

## 💬 Comunidade

- **Discussions**: Use para perguntas e discussões gerais
- **Issues**: Para bugs e feature requests
- **Pull Requests**: Para submeter mudanças
- **Email**: Para assuntos sensíveis

## 🙌 Obrigado!

Obrigado por ser parte da comunidade MailCerto! Sua contribuição é super valorizada.

---

Para perguntas, entre em contato através de:
- Issues: https://github.com/seu-usuario/mailcerto/issues
- Discussions: https://github.com/seu-usuario/mailcerto/discussions
