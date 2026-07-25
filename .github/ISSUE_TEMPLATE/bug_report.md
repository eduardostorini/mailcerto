name: Bug Report
description: Reporte um bug encontrado
labels: ["bug"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Obrigado por reportar um bug! Por favor, preencha o formulário abaixo para nos ajudar a entender e corrigir o problema.

  - type: textarea
    id: description
    attributes:
      label: Descrição do Bug
      description: Uma descrição clara e concisa do que é o bug.
      placeholder: O que é o bug?
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: Passos para Reproduzir
      description: Passos exatos para reproduzir o problema
      placeholder: |
        1. Ir para '...'
        2. Clicar em '...'
        3. Ver erro
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Comportamento Esperado
      description: Uma descrição clara de qual seria o comportamento esperado.
      placeholder: O que deveria acontecer?
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Comportamento Atual
      description: O que realmente acontece? (inclua screenshots se possível)
      placeholder: O que realmente acontece?
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: Sistema Operacional
      options:
        - Windows
        - macOS
        - Linux
        - Outro
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Versão do Python
      placeholder: "3.10"
    validations:
      required: true

  - type: input
    id: mailcerto-version
    attributes:
      label: Versão do MailCerto
      placeholder: "1.0.0"
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Logs da Aplicação
      description: Se aplicável, copie os logs de erro
      render: markdown

  - type: textarea
    id: additional
    attributes:
      label: Contexto Adicional
      description: Alguma outra informação relevante?
      placeholder: Adicione qualquer contexto relevante aqui
