name: Feature Request
description: Sugira uma ideia para o MailCerto
labels: ["enhancement"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Obrigado por sugerir uma melhoria! Por favor, descreva a funcionalidade desejada de forma clara.

  - type: textarea
    id: description
    attributes:
      label: Descrição da Feature
      description: Uma descrição clara e concisa da feature desejada
      placeholder: O que você gostaria de adicionar?
    validations:
      required: true

  - type: textarea
    id: motivation
    attributes:
      label: Motivação
      description: Por que essa feature seria útil? Qual problema resolve?
      placeholder: Qual é o caso de uso?
    validations:
      required: true

  - type: textarea
    id: implementation
    attributes:
      label: Implementação Sugerida
      description: Como você imagina a implementação? (opcional)
      placeholder: Descreva como a feature deveria funcionar

  - type: textarea
    id: alternatives
    attributes:
      label: Alternativas Consideradas
      description: Existem outras formas de resolver este problema?
      placeholder: Quais são as alternativas?

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: Eu procurei por issues similares
          required: true
        - label: Esta é uma feature nova e não uma duplicata
          required: true
