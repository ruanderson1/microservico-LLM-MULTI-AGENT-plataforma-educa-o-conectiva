from schemas.class_ import (
    ClassReportRequest,
    ClassReportResponse,
    ClassAgregadoAlunosResponse,
    ClassRiscoColetivoResponse,
    ClassResumoLLMTurmaResponse,
    ClassRecomendacaoParaProfessorTurmaResponse,
    ClassPlanoAcaoTurmaResponse,
    ClassSaidaLLMTurmaResponse,
)
from prompts.class_agregado_prompt import build_class_agregado_prompt
from prompts.class_risco_prompt import build_class_risco_prompt
from prompts.class_saida_llm_prompt import (
    build_class_resumo_llm_turma_prompt,
    build_class_recomendacao_para_professor_turma_prompt,
    build_class_plano_acao_turma_prompt,
)
from llm.openai_client import OpenAIClient
import json
import re
import logging
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


logger = logging.getLogger(__name__)


class ClassReportState(TypedDict, total=False):
    request: ClassReportRequest
    agregado_data: dict[str, Any]
    agregado: ClassAgregadoAlunosResponse
    risco_data: dict[str, Any]
    risco: ClassRiscoColetivoResponse
    resumo_data: dict[str, Any]
    resumo: ClassResumoLLMTurmaResponse
    recomendacao_data: dict[str, Any]
    recomendacao: ClassRecomendacaoParaProfessorTurmaResponse
    plano_data: dict[str, Any]
    plano: ClassPlanoAcaoTurmaResponse


def _parse_llm_json(llm_response: str) -> dict:
    try:
        return json.loads(llm_response)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", llm_response)
        if match:
            return json.loads(match.group(0))
        raise ValueError("LLM did not return valid JSON.")


def _run_agent(request: ClassReportRequest, agent_name: str, prompt: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        data = _parse_llm_json(OpenAIClient.generate(prompt))
        logger.info(
            "class_report.agent_done agent=%s class_id=%s duration_ms=%d",
            agent_name,
            request.class_id,
            int((time.perf_counter() - start) * 1000),
        )
        return data
    except Exception:
        logger.exception(
            "class_report.failed agent=%s class_id=%s periodo=%s",
            agent_name,
            request.class_id,
            request.periodo_referencia,
        )
        raise


def _node_agregado(state: ClassReportState) -> ClassReportState:
    request = state["request"]
    data = _run_agent(request, "agregado_alunos", build_class_agregado_prompt(request))
    return {"agregado_data": data, "agregado": ClassAgregadoAlunosResponse(**data)}


def _node_risco(state: ClassReportState) -> ClassReportState:
    request = state["request"]
    data = _run_agent(request, "risco_coletivo", build_class_risco_prompt(request))
    return {"risco_data": data, "risco": ClassRiscoColetivoResponse(**data)}


def _node_resumo(state: ClassReportState) -> ClassReportState:
    request = state["request"]
    data = _run_agent(
        request,
        "resumo_llm_turma",
        build_class_resumo_llm_turma_prompt(request, state["agregado_data"], state["risco_data"]),
    )
    return {"resumo_data": data, "resumo": ClassResumoLLMTurmaResponse(**data)}


def _node_recomendacao(state: ClassReportState) -> ClassReportState:
    request = state["request"]
    data = _run_agent(
        request,
        "recomendacao_para_professor_turma",
        build_class_recomendacao_para_professor_turma_prompt(
            request,
            state["agregado_data"],
            state["risco_data"],
            state["resumo_data"],
        ),
    )
    return {
        "recomendacao_data": data,
        "recomendacao": ClassRecomendacaoParaProfessorTurmaResponse(**data),
    }


def _node_plano(state: ClassReportState) -> ClassReportState:
    request = state["request"]
    data = _run_agent(
        request,
        "plano_acao_turma",
        build_class_plano_acao_turma_prompt(
            request,
            state["agregado_data"],
            state["risco_data"],
            state["resumo_data"],
            state["recomendacao_data"],
        ),
    )
    return {"plano_data": data, "plano": ClassPlanoAcaoTurmaResponse(**data)}


def _build_class_report_graph():
    graph = StateGraph(ClassReportState)

    graph.add_node("agregado", _node_agregado)
    graph.add_node("risco", _node_risco)
    graph.add_node("resumo", _node_resumo)
    graph.add_node("recomendacao", _node_recomendacao)
    graph.add_node("plano", _node_plano)

    graph.add_edge(START, "agregado")
    graph.add_edge("agregado", "risco")
    graph.add_edge("risco", "resumo")
    graph.add_edge("resumo", "recomendacao")
    graph.add_edge("recomendacao", "plano")
    graph.add_edge("plano", END)

    return graph.compile()


CLASS_REPORT_GRAPH = _build_class_report_graph()


async def generate_class_report(request: ClassReportRequest) -> ClassReportResponse:
    logger.info(
        "class_report.start class_id=%s periodo=%s students=%d",
        request.class_id,
        request.periodo_referencia,
        len(request.students),
    )

    final_state = CLASS_REPORT_GRAPH.invoke({"request": request})

    agregado = final_state["agregado"]
    risco = final_state["risco"]
    resumo = final_state["resumo"]
    recomendacao = final_state["recomendacao"]
    plano = final_state["plano"]

    saida = ClassSaidaLLMTurmaResponse(
        resumo_llm_turma=resumo.resumo_llm_turma,
        recomendacao_para_professor_turma=recomendacao.recomendacao_para_professor_turma,
        plano_acao_turma=plano.plano_acao_turma,
    )

    logger.info(
        "class_report.success class_id=%s periodo=%s",
        request.class_id,
        request.periodo_referencia,
    )

    return ClassReportResponse(
        class_id=request.class_id,
        periodo_referencia=request.periodo_referencia,
        agregado_alunos=agregado,
        risco_coletivo=risco,
        saida_llm_turma=saida,
    )
