# Arquitetura de Agentes

Este documento descreve os fluxos reais dos agentes usados atualmente no sistema.

## Visao Geral de Orquestracao

```mermaid
flowchart TD
    API[/POST /reports/student/] --> SRV1[generate_student_report]
    API2[/POST /reports/class/] --> SRV2[generate_class_report]

    SRV1 --> S1
    SRV1 --> S2
    SRV1 --> S3
    SRV2 --> C1
    SRV2 --> C2

    S7 --> OUT1[(StudentReportResponse)]
    C5 --> OUT2[(ClassReportResponse)]

    S1[Agente Aluno 1\nAcademico]
    S2[Agente Aluno 2\nEmocional]
    S3[Agente Aluno 3\nRisco]
    S4[Agente Aluno 4\nResumo LLM]
    S5[Agente Aluno 5\nRecomendacao Professor]
    S6[Agente Aluno 6\nRecomendacao Pais]
    S7[Agente Aluno 7\nPlano Acao Sugerido]

    C1[Agente Turma 1\nAgregado Alunos]
    C2[Agente Turma 2\nRisco Coletivo]
    C3[Agente Turma 3\nResumo LLM Turma]
    C4[Agente Turma 4\nRecomendacao Professor Turma]
    C5[Agente Turma 5\nPlano Acao Turma]
```

## Fluxo Completo - Relatorio de Aluno

```mermaid
flowchart TD
    IN1[Input StudentReportRequest] --> CTX[Build Shared Context]

    CTX --> A1[Agente 1\nAcademico]
    CTX --> A2[Agente 2\nEmocional]
    CTX --> A3[Agente 3\nRisco]

    A1 --> A4[Agente 4\nResumo LLM]
    A2 --> A4
    A3 --> A4

    A1 --> A5[Agente 5\nRecomendacao para Professor]
    A2 --> A5
    A3 --> A5
    A4 --> A5

    A1 --> A6[Agente 6\nRecomendacao para Pais]
    A2 --> A6
    A3 --> A6
    A4 --> A6
    A5 --> A6

    A1 --> A7[Agente 7\nPlano de Acao Sugerido]
    A2 --> A7
    A3 --> A7
    A4 --> A7
    A5 --> A7
    A6 --> A7

    A4 --> OUTA[saida_llm.resumo_llm]
    A5 --> OUTB[saida_llm.recomendacao_para_professor]
    A6 --> OUTC[saida_llm.recomendacao_para_pais]
    A7 --> OUTD[saida_llm.plano_acao_sugerido]

    OUTA --> R1[(StudentReportResponse)]
    OUTB --> R1
    OUTC --> R1
    OUTD --> R1
    A1 --> R1
    A2 --> R1
    A3 --> R1
```

Representacao textual:

1. Agentes de analise base: Academico, Emocional e Risco.
2. Resumo LLM recebe a saida dos 3 agentes base.
3. Recomendacao para Professor recebe os 3 agentes base + Resumo LLM.
4. Recomendacao para Pais recebe os 3 agentes base + Resumo LLM + Recomendacao Professor.
5. Plano de Acao Sugerido recebe todos os agentes anteriores.
6. A resposta final inclui academico, emocional, risco e saida_llm consolidada.

## Fluxo Completo - Relatorio de Turma

```mermaid
flowchart TD
    IN2[Input ClassReportRequest] --> C1[Agente 1\nAgregado Alunos]
    IN2 --> C2[Agente 2\nRisco Coletivo]

    C1 --> C3[Agente 3\nResumo LLM Turma]
    C2 --> C3

    C1 --> C4[Agente 4\nRecomendacao para Professor Turma]
    C2 --> C4
    C3 --> C4

    C1 --> C5[Agente 5\nPlano de Acao Turma]
    C2 --> C5
    C3 --> C5
    C4 --> C5

    C3 --> OUT1[saida_llm_turma.resumo_llm_turma]
    C4 --> OUT2[saida_llm_turma.recomendacao_para_professor_turma]
    C5 --> OUT3[saida_llm_turma.plano_acao_turma]

    OUT1 --> R2[(ClassReportResponse)]
    OUT2 --> R2
    OUT3 --> R2
    C1 --> R2
    C2 --> R2
```

Representacao textual:

1. Agregado Alunos e Risco Coletivo sao os agentes base.
2. Resumo LLM Turma recebe Agregado Alunos + Risco Coletivo.
3. Recomendacao para Professor Turma recebe Agregado Alunos + Risco Coletivo + Resumo LLM Turma.
4. Plano de Acao Turma recebe todos os agentes anteriores.
5. A resposta final inclui agregado_alunos, risco_coletivo e saida_llm_turma consolidada.

## Observacoes

- Todos os agentes sao executados com chamadas independentes a OpenAIClient.generate.
- A orquestracao atual e sequencial por dependencias de contexto entre os agentes.
