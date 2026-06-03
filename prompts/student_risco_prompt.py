from schemas.student import StudentReportRequest


def build_risco_prompt(request: StudentReportRequest, ctx: dict) -> str:
    nome = ctx["nome_aluno"]
    activities = ctx["activities"]
    weighted_avg = ctx["weighted_avg"]
    low_scores = ctx["low_scores"]
    obs_prof = ctx["observacao_professor"]
    obs_pais = ctx["observacao_pais"]
    total_presencas = ctx["total_presencas"]
    total_faltas = ctx["total_faltas"]

    return f"""
    Você é um agente educacional especializado em avaliação de risco escolar.

    Sua única função é avaliar os RISCOS acadêmicos e de engajamento do aluno e retornar um JSON com exatamente
    3 campos. Não descreva desempenho detalhado nem aspectos emocionais — esses são responsabilidade de outros agentes.

    IMPORTANTE:
    - Gere APENAS JSON válido, sem texto fora do JSON.
    - Não use markdown.
    - Não altere os nomes dos campos.
    - Não adicione campos extras.
    - Use linguagem objetiva, cuidadosa e não punitiva.
    - Toda avaliação deve estar baseada nos dados fornecidos.
    - Se os dados forem insuficientes, reduza a força das conclusões.

    REGRAS PARA "risco_desempenho_baixo":
    - "alto": média baixa, várias atividades com nota baixa, faltas relevantes e/ou observações que reforcem dificuldade persistente.
    - "medio": alguns sinais de dificuldade, mas também evidências de recuperação, pontos fortes ou dados insuficientes.
    - "baixo": desempenho adequado ou ausência de sinais consistentes de dificuldade acadêmica.

    REGRAS PARA "risco_desengajamento":
    - "alto": muitas faltas, baixa entrega de atividades, observações de pouca participação ou sinais recorrentes de desmotivação.
    - "medio": alguns sinais de baixa participação ou frequência irregular (se tiver muito poucas faltas ou faltas justificadas em relação a quantidade de presença não entra em médio), mas sem evidências fortes.
    - "baixo": boa frequência, muito poucas faltas ou faltas justificadas em relação a quantidade de presença, participação adequada ou ausência de sinais de desengajamento.

    REGRAS PARA "necessita_intervencao":
    - true: risco alto em desempenho ou desengajamento, ou dados que indiquem necessidade de acompanhamento mais próximo.
    - false: acompanhamento regular parece suficiente.

    FORMATO OBRIGATÓRIO DO JSON:
    {{
      "risco_desempenho_baixo": "alto|medio|baixo",
      "risco_desengajamento": "alto|medio|baixo",
      "necessita_intervencao": boolean
    }}

    DADOS DO ALUNO:
    - Nome: {nome}
    - ID: {request.student_id}
    - Período: {request.periodo_referencia}

    OBSERVAÇÕES QUALITATIVAS:
    - Professor: {obs_prof}
    - Pais: {obs_pais}

    DADOS ACADÊMICOS:
    - Média ponderada: {weighted_avg:.2f}
    - Total de atividades: {len(activities)}
    - Atividades com nota baixa (< 50%): {[a.tipo for a in low_scores]}
    - Observações das atividades: {[a.observacoes for a in activities if a.observacoes]}

    FREQUÊNCIA:
    - Presenças: {total_presencas}
    - Faltas: {total_faltas}

    Gere agora apenas o JSON válido.
    """
