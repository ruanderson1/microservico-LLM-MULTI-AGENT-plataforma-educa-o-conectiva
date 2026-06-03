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
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph  # type: ignore[reportMissingImports]


logger = logging.getLogger(__name__)


class StudentReportState(TypedDict, total=False):
    request: StudentReportRequest
    ctx: dict[str, Any]
    academico_data: dict[str, Any]
    academico: AcademicoResponse
    emocional_data: dict[str, Any]
    emocional: EmocionalResponse
    risco_data: dict[str, Any]
    risco: RiscoResponse
    resumo_data: dict[str, Any]
    resumo: ResumoLLMResponse
    recomendacao_professor_data: dict[str, Any]
    recomendacao_professor: RecomendacaoParaProfessorResponse
    recomendacao_pais_data: dict[str, Any]
    recomendacao_pais: RecomendacaoParaPaisResponse
    plano_data: dict[str, Any]
    plano: PlanoAcaoSugeridoResponse


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


def _run_agent(request: StudentReportRequest, agent_name: str, prompt: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        data = _parse_llm_json(OpenAIClient.generate(prompt))
        logger.info(
            "student_report.agent_done agent=%s student_id=%s duration_ms=%d",
            agent_name,
            request.student_id,
            int((time.perf_counter() - start) * 1000),
        )
        return data
    except Exception:
        logger.exception(
            "student_report.failed agent=%s student_id=%s periodo=%s",
            agent_name,
            request.student_id,
            request.periodo_referencia,
        )
        raise


def _node_academico(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(request, "academico", build_academico_prompt(request, ctx))
    return {"academico_data": data, "academico": AcademicoResponse(**data)}


def _node_emocional(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(request, "emocional", build_emocional_prompt(request, ctx))
    return {"emocional_data": data, "emocional": EmocionalResponse(**data)}


def _node_risco(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(request, "risco", build_risco_prompt(request, ctx))
    return {"risco_data": data, "risco": RiscoResponse(**data)}


def _node_resumo(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(
        request,
        "resumo_llm",
        build_resumo_llm_prompt(
            request,
            ctx,
            state["academico_data"],
            state["emocional_data"],
            state["risco_data"],
        ),
    )
    return {"resumo_data": data, "resumo": ResumoLLMResponse(**data)}


def _node_recomendacao_professor(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(
        request,
        "recomendacao_para_professor",
        build_recomendacao_para_professor_prompt(
            request,
            ctx,
            state["academico_data"],
            state["emocional_data"],
            state["risco_data"],
            state["resumo_data"],
        ),
    )
    return {
        "recomendacao_professor_data": data,
        "recomendacao_professor": RecomendacaoParaProfessorResponse(**data),
    }


def _node_recomendacao_pais(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(
        request,
        "recomendacao_para_pais",
        build_recomendacao_para_pais_prompt(
            request,
            ctx,
            state["academico_data"],
            state["emocional_data"],
            state["risco_data"],
            state["resumo_data"],
            state["recomendacao_professor_data"],
        ),
    )
    return {"recomendacao_pais_data": data, "recomendacao_pais": RecomendacaoParaPaisResponse(**data)}


def _node_plano_acao(state: StudentReportState) -> StudentReportState:
    request = state["request"]
    ctx = state["ctx"]
    data = _run_agent(
        request,
        "plano_acao_sugerido",
        build_plano_acao_sugerido_prompt(
            request,
            ctx,
            state["academico_data"],
            state["emocional_data"],
            state["risco_data"],
            state["resumo_data"],
            state["recomendacao_professor_data"],
            state["recomendacao_pais_data"],
        ),
    )
    return {"plano_data": data, "plano": PlanoAcaoSugeridoResponse(**data)}


def _build_student_report_graph():
    graph = StateGraph(StudentReportState)

    graph.add_node("academico", _node_academico)
    graph.add_node("emocional", _node_emocional)
    graph.add_node("risco", _node_risco)
    graph.add_node("resumo", _node_resumo)
    graph.add_node("recomendacao_professor", _node_recomendacao_professor)
    graph.add_node("recomendacao_pais", _node_recomendacao_pais)
    graph.add_node("plano_acao", _node_plano_acao)

    graph.add_edge(START, "academico")
    graph.add_edge("academico", "emocional")
    graph.add_edge("emocional", "risco")
    graph.add_edge("risco", "resumo")
    graph.add_edge("resumo", "recomendacao_professor")
    graph.add_edge("recomendacao_professor", "recomendacao_pais")
    graph.add_edge("recomendacao_pais", "plano_acao")
    graph.add_edge("plano_acao", END)

    return graph.compile()


STUDENT_REPORT_GRAPH = _build_student_report_graph()


async def generate_student_report(request: StudentReportRequest) -> StudentReportResponse:
    logger.info(
        "student_report.start student_id=%s periodo=%s",
        request.student_id,
        request.periodo_referencia,
    )
    final_state = STUDENT_REPORT_GRAPH.invoke(
        {
            "request": request,
            "ctx": _build_shared_context(request),
        }
    )

    academico = final_state["academico"]
    emocional = final_state["emocional"]
    risco = final_state["risco"]
    resumo = final_state["resumo"]
    recomendacao_professor = final_state["recomendacao_professor"]
    recomendacao_pais = final_state["recomendacao_pais"]
    plano = final_state["plano"]

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
