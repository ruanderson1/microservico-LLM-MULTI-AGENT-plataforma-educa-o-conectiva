from schemas.student import StudentReportRequest


def _build_student_context_block(
    request: StudentReportRequest,
    ctx: dict,
    academico: dict,
    emocional: dict,
    risco: dict,
) -> str:
    nome = ctx["nome_aluno"]
    obs_prof = ctx["observacao_professor"]
    obs_pais = ctx["observacao_pais"]
    total_presencas = ctx["total_presencas"]
    total_faltas = ctx["total_faltas"]

    return f"""
    DADOS DO ALUNO:
    - Nome: {nome}
    - ID: {request.student_id}
    - Período: {request.periodo_referencia}

    OBSERVAÇÕES QUALITATIVAS:
    - Professor: {obs_prof}
    - Pais: {obs_pais}

    FREQUÊNCIA:
    - Presenças: {total_presencas}
    - Faltas: {total_faltas}

    ANÁLISE ACADÊMICA (Agente Acadêmico):
    - Desempenho geral: {academico.get("desempenho_geral", "")}
    - Evolução recente: {academico.get("evolucao_recente", "")}
    - Dificuldades: {academico.get("dificuldades_aprendizagem", "")}
    - Pontos fortes: {academico.get("pontos_fortes_aprendizagem", "")}

    ANÁLISE SOCIOEMOCIONAL (Agente Emocional):
    - Estado emocional: {emocional.get("estado_emocional_geral", "")}
    - Engajamento: {emocional.get("engajamento", "")}

    AVALIAÇÃO DE RISCO (Agente de Risco):
    - Risco de desempenho baixo: {risco.get("risco_desempenho_baixo", "")}
    - Risco de desengajamento: {risco.get("risco_desengajamento", "")}
    - Necessita intervenção: {risco.get("necessita_intervencao", "")}
    """


def build_resumo_llm_prompt(
    request: StudentReportRequest,
    ctx: dict,
    academico: dict,
    emocional: dict,
    risco: dict,
) -> str:
    base_context = _build_student_context_block(request, ctx, academico, emocional, risco)
    return f"""
    Você é um agente educacional especializado em síntese pedagógica.

    Sua função é gerar apenas o campo "resumo_llm" com base nas análises anteriores do fluxo.

    IMPORTANTE:
    - Gere APENAS JSON válido, sem texto fora do JSON.
    - Não use markdown.
    - Não altere o nome do campo.
    - Não adicione campos extras.
    - Use linguagem acolhedora, pedagógica e não punitiva.

    OBJETIVO:
    Faça um resumo integrado do momento do aluno conectando desempenho, frequência,
    observações qualitativas, engajamento e possíveis necessidades.

    FORMATO OBRIGATÓRIO DO JSON:
    {{
      "resumo_llm": string
    }}

    {base_context}

    Gere agora apenas o JSON válido.
    """


def build_recomendacao_para_professor_prompt(
    request: StudentReportRequest,
    ctx: dict,
    academico: dict,
    emocional: dict,
    risco: dict,
    resumo_llm: dict,
) -> str:
    base_context = _build_student_context_block(request, ctx, academico, emocional, risco)
    return f"""
    Você é um agente educacional especializado em práticas pedagógicas para sala de aula.

    Sua função é gerar apenas o campo "recomendacao_para_professor".

    IMPORTANTE:
    - Gere APENAS JSON válido, sem texto fora do JSON.
    - Não use markdown.
    - Não altere o nome do campo.
    - Não adicione campos extras.
    - Use linguagem clara, prática e não punitiva.

    OBJETIVO:
    Gere recomendações acionáveis para o professor com justificativas curtas,
    considerando as análises anteriores e o resumo consolidado.

    FORMATO OBRIGATÓRIO DO JSON:
    {{
      "recomendacao_para_professor": string
    }}

    RESUMO JÁ GERADO (Agente de Resumo):
    - resumo_llm: {resumo_llm.get("resumo_llm", "")}

    {base_context}

    Gere agora apenas o JSON válido.
    """


def build_recomendacao_para_pais_prompt(
    request: StudentReportRequest,
    ctx: dict,
    academico: dict,
    emocional: dict,
    risco: dict,
    resumo_llm: dict,
    recomendacao_professor: dict,
) -> str:
    base_context = _build_student_context_block(request, ctx, academico, emocional, risco)
    return f"""
    Você é um agente educacional especializado em orientação acolhedora para famílias.

    Sua função é gerar apenas o campo "recomendacao_para_pais".

    IMPORTANTE:
    - Gere APENAS JSON válido, sem texto fora do JSON.
    - Não use markdown.
    - Não altere o nome do campo.
    - Não adicione campos extras.
    - Evite tom de culpa ou cobrança.

    OBJETIVO:
    Sugira ações simples, práticas e acolhedoras para os responsáveis,
    com foco em rotina, incentivo e apoio ao aluno.

    FORMATO OBRIGATÓRIO DO JSON:
    {{
      "recomendacao_para_pais": string
    }}

    CONTEXTO DOS AGENTES ANTERIORES:
    - resumo_llm: {resumo_llm.get("resumo_llm", "")}
    - recomendacao_para_professor: {recomendacao_professor.get("recomendacao_para_professor", "")}

    {base_context}

    Gere agora apenas o JSON válido.
    """


def build_plano_acao_sugerido_prompt(
    request: StudentReportRequest,
    ctx: dict,
    academico: dict,
    emocional: dict,
    risco: dict,
    resumo_llm: dict,
    recomendacao_professor: dict,
    recomendacao_pais: dict,
) -> str:
    base_context = _build_student_context_block(request, ctx, academico, emocional, risco)
    return f"""
    Você é um agente educacional especializado em planejamento de intervenção pedagógica.

    Sua função é gerar apenas o campo "plano_acao_sugerido".

    IMPORTANTE:
    - Gere APENAS JSON válido, sem texto fora do JSON.
    - Não use markdown.
    - Não altere o nome do campo.
    - Não adicione campos extras.
    - Plano deve ser viável para curto prazo.

    OBJETIVO:
    Monte um plano de ação objetivo, com passos práticos, envolvendo professor,
    família e aluno quando necessário.

    FORMATO OBRIGATÓRIO DO JSON:
    {{
      "plano_acao_sugerido": string
    }}

    CONTEXTO DOS AGENTES ANTERIORES:
    - resumo_llm: {resumo_llm.get("resumo_llm", "")}
    - recomendacao_para_professor: {recomendacao_professor.get("recomendacao_para_professor", "")}
    - recomendacao_para_pais: {recomendacao_pais.get("recomendacao_para_pais", "")}

    {base_context}

    Gere agora apenas o JSON válido.
    """
