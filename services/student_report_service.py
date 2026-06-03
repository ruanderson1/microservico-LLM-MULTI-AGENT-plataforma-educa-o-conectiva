from schemas.student import (
    StudentReportRequest,
    StudentReportResponse,
    AcademicoResponse,
    EmocionalResponse,
    RiscoResponse,
    ResumoLLMResponse,
    RecomendacaoParaProfessorResponse,
    RecomendacaoParaPaisResponse,
    PlanoAcaoSugeridoResponse,
    SaidaLLMResponse,
)
from prompts.student_academico_prompt import build_academico_prompt
from prompts.student_emocional_prompt import build_emocional_prompt
from prompts.student_risco_prompt import build_risco_prompt
from prompts.student_saida_llm_prompt import (
    build_resumo_llm_prompt,
    build_recomendacao_para_professor_prompt,
    build_recomendacao_para_pais_prompt,
    build_plano_acao_sugerido_prompt,
)
from llm.openai_client import OpenAIClient
import json
import re
import logging
import time


logger = logging.getLogger(__name__)


def _parse_llm_json(llm_response: str) -> dict:
    try:
        return json.loads(llm_response)
    except Exception:
        match = re.search(r'\{[\s\S]*\}', llm_response)
        if match:
            return json.loads(match.group(0))
        raise ValueError("LLM did not return valid JSON.")


def _build_shared_context(request: StudentReportRequest) -> dict:
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
    weighted_avg = (
        weighted_sum / total_weight
        if total_weight > 0
        else (request.notas.media if request.notas else 0)
    )

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

    return {
        "nome_aluno": request.nome or "Aluno",
        "activities": activities,
        "weighted_avg": weighted_avg,
        "low_scores": low_scores,
        "high_scores": high_scores,
        "observacao_professor": observacao_professor,
        "observacao_pais": observacao_pais,
        "total_presencas": total_presencas,
        "total_faltas": total_faltas,
    }


async def generate_student_report(request: StudentReportRequest) -> StudentReportResponse:
    ctx = _build_shared_context(request)
    logger.info(
        "student_report.start student_id=%s periodo=%s",
        request.student_id,
        request.periodo_referencia,
    )

    # Agent 1: Academic performance
    try:
        start_academico = time.perf_counter()
        academico_data = _parse_llm_json(
            OpenAIClient.generate(build_academico_prompt(request, ctx))
        )
        academico = AcademicoResponse(**academico_data)
        logger.info(
            "student_report.agent_done agent=academico student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_academico) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=academico student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 2: Socioemotional state and engagement
    try:
        start_emocional = time.perf_counter()
        emocional_data = _parse_llm_json(
            OpenAIClient.generate(build_emocional_prompt(request, ctx))
        )
        emocional = EmocionalResponse(**emocional_data)
        logger.info(
            "student_report.agent_done agent=emocional student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_emocional) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=emocional student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 3: Risk assessment
    try:
        start_risco = time.perf_counter()
        risco_data = _parse_llm_json(
            OpenAIClient.generate(build_risco_prompt(request, ctx))
        )
        risco = RiscoResponse(**risco_data)
        logger.info(
            "student_report.agent_done agent=risco student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_risco) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=risco student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 4: Resumo LLM (depends on previous analysis agents)
    try:
        start_resumo = time.perf_counter()
        resumo_data = _parse_llm_json(
            OpenAIClient.generate(
                build_resumo_llm_prompt(
                    request,
                    ctx,
                    academico_data,
                    emocional_data,
                    risco_data,
                )
            )
        )
        resumo = ResumoLLMResponse(**resumo_data)
        logger.info(
            "student_report.agent_done agent=resumo_llm student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_resumo) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=resumo_llm student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 5: Recommendation for teacher (depends on resumo + previous analyses)
    try:
        start_recomendacao_professor = time.perf_counter()
        recomendacao_professor_data = _parse_llm_json(
            OpenAIClient.generate(
                build_recomendacao_para_professor_prompt(
                    request,
                    ctx,
                    academico_data,
                    emocional_data,
                    risco_data,
                    resumo_data,
                )
            )
        )
        recomendacao_professor = RecomendacaoParaProfessorResponse(
            **recomendacao_professor_data
        )
        logger.info(
            "student_report.agent_done agent=recomendacao_para_professor student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_recomendacao_professor) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=recomendacao_para_professor student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 6: Recommendation for parents (depends on resumo + recommendation for teacher)
    try:
        start_recomendacao_pais = time.perf_counter()
        recomendacao_pais_data = _parse_llm_json(
            OpenAIClient.generate(
                build_recomendacao_para_pais_prompt(
                    request,
                    ctx,
                    academico_data,
                    emocional_data,
                    risco_data,
                    resumo_data,
                    recomendacao_professor_data,
                )
            )
        )
        recomendacao_pais = RecomendacaoParaPaisResponse(**recomendacao_pais_data)
        logger.info(
            "student_report.agent_done agent=recomendacao_para_pais student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_recomendacao_pais) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=recomendacao_para_pais student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    # Agent 7: Suggested action plan (depends on all previous output agents)
    try:
        start_plano = time.perf_counter()
        plano_data = _parse_llm_json(
            OpenAIClient.generate(
                build_plano_acao_sugerido_prompt(
                    request,
                    ctx,
                    academico_data,
                    emocional_data,
                    risco_data,
                    resumo_data,
                    recomendacao_professor_data,
                    recomendacao_pais_data,
                )
            )
        )
        plano = PlanoAcaoSugeridoResponse(**plano_data)
        logger.info(
            "student_report.agent_done agent=plano_acao_sugerido student_id=%s duration_ms=%d",
            request.student_id,
            int((time.perf_counter() - start_plano) * 1000),
        )
    except Exception:
        logger.exception(
            "student_report.failed agent=plano_acao_sugerido student_id=%s periodo=%s",
            request.student_id,
            request.periodo_referencia,
        )
        raise

    saida_llm = SaidaLLMResponse(
        resumo_llm=resumo.resumo_llm,
        recomendacao_para_professor=recomendacao_professor.recomendacao_para_professor,
        recomendacao_para_pais=recomendacao_pais.recomendacao_para_pais,
        plano_acao_sugerido=plano.plano_acao_sugerido,
    )

    logger.info(
        "student_report.success student_id=%s periodo=%s",
        request.student_id,
        request.periodo_referencia,
    )

    return StudentReportResponse(
        student_id=request.student_id,
        periodo_referencia=request.periodo_referencia,
        academico=academico,
        emocional=emocional,
        risco=risco,
        saida_llm=saida_llm,
    )
