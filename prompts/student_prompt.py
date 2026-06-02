from schemas.student import StudentReportRequest

def build_student_prompt(request: StudentReportRequest) -> str:
    # Accept current backend payload (notas/frequencia/observacoes)
    # and keep compatibility with legacy payload (atividades/observacao_*).
    activities = []
    if request.notas and request.notas.detalhes:
        activities = request.notas.detalhes
    elif request.atividades:
        activities = request.atividades

    def score_ratio(activity):
        max_score = activity.nota_maxima or activity.notaMaxima or 10
        if not max_score or max_score <= 0:
            max_score = 10
        return activity.pontuacao / max_score

    total_weight = sum((a.peso or 1) for a in activities)
    weighted_sum = sum(score_ratio(a) * (a.peso or 1) for a in activities)
    weighted_avg = weighted_sum / total_weight if total_weight > 0 else (request.notas.media if request.notas else 0)

    low_scores = [a for a in activities if score_ratio(a) < 0.5]
    high_scores = [a for a in activities if score_ratio(a) > 0.85]

    observacao_professor = ""
    observacao_pais = ""
    if request.observacoes:
        observacao_professor = request.observacoes.professor or ""
        observacao_pais = request.observacoes.pais or ""

    if not observacao_professor:
        observacao_professor = request.observacao_professor or ""
    if not observacao_pais:
        observacao_pais = request.observacao_pais or ""

    total_presencas = 0
    total_faltas = 0
    if request.frequencia:
        total_presencas = request.frequencia.total_presencas or 0
        total_faltas = request.frequencia.total_faltas or 0

    nome_aluno = request.nome or "Aluno"

    prompt = f"""
Você é um assistente educacional. Gere um relatório ESTRUTURADO em JSON (apenas JSON, sem explicações) com o seguinte formato:
Gere para cada campo com base nas informações fornecidasum relatorio detalhado sobre o desempenho acadêmico, engajamento e estado emocional do aluno, 
incluindo recomendações para professores e pais. Use as observações qualitativas e os dados quantitativos para fundamentar suas análises e recomendações.

{{
  "student_id": string,
  "periodo_referencia": string,
  "desempenho_geral": string,
  "evolucao_recente": "melhorando|estavel|piorando",
  "dificuldades_aprendizagem": string,
  "pontos_fortes_aprendizagem": string,
  "estado_emocional_geral": string,
  "engajamento": string,
  "risco_desempenho_baixo": string,
  "risco_desengajamento": string,
  "necessita_intervencao": boolean,
  "resumo_llm": string,
  "recomendacao_para_professor": string,
  "recomendacao_para_pais": string,
  "plano_acao_sugerido": string
}}

Dados do aluno:
- Nome: {nome_aluno}
- ID: {request.student_id}
- Período: {request.periodo_referencia}

Observações qualitativas:
- Professor: {observacao_professor}
- Pais: {observacao_pais}

Resumo acadêmico:
- Média ponderada: {weighted_avg:.2f}
- Total de atividades: {len(activities)}
- Atividades com nota baixa: {[a.tipo for a in low_scores]}
- Atividades com nota alta: {[a.tipo for a in high_scores]}
- Observações relevantes: {[a.observacoes for a in activities if a.observacoes]}

Resumo de frequência:
- Presenças: {total_presencas}
- Faltas: {total_faltas}

Gere apenas o JSON válido, sem explicações extras.
"""
    return prompt
