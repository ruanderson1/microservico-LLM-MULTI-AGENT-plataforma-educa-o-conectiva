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


logger = logging.getLogger(__name__)


def _parse_llm_json(llm_response: str) -> dict:
    try:
        return json.loads(llm_response)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", llm_response)
        if match:
            return json.loads(match.group(0))
        raise ValueError("LLM did not return valid JSON.")


async def generate_class_report(request: ClassReportRequest) -> ClassReportResponse:
    logger.info(
        "class_report.start class_id=%s periodo=%s students=%d",
        request.class_id,
        request.periodo_referencia,
        len(request.students),
    )

    try:
        start_agregado = time.perf_counter()
        agregado_data = _parse_llm_json(
            OpenAIClient.generate(build_class_agregado_prompt(request))
        )
        agregado = ClassAgregadoAlunosResponse(**agregado_data)
        logger.info(
            "class_report.agent_done agent=agregado_alunos class_id=%s duration_ms=%d",
            request.class_id,
            int((time.perf_counter() - start_agregado) * 1000),
        )
    except Exception:
        logger.exception(
            "class_report.failed agent=agregado_alunos class_id=%s periodo=%s",
            request.class_id,
            request.periodo_referencia,
        )
        raise

    try:
        start_risco = time.perf_counter()
        risco_data = _parse_llm_json(
            OpenAIClient.generate(build_class_risco_prompt(request))
        )
        risco = ClassRiscoColetivoResponse(**risco_data)
        logger.info(
            "class_report.agent_done agent=risco_coletivo class_id=%s duration_ms=%d",
            request.class_id,
            int((time.perf_counter() - start_risco) * 1000),
        )
    except Exception:
        logger.exception(
            "class_report.failed agent=risco_coletivo class_id=%s periodo=%s",
            request.class_id,
            request.periodo_referencia,
        )
        raise

    try:
        start_resumo = time.perf_counter()
        resumo_data = _parse_llm_json(
            OpenAIClient.generate(
                build_class_resumo_llm_turma_prompt(request, agregado_data, risco_data)
            )
        )
        resumo = ClassResumoLLMTurmaResponse(**resumo_data)
        logger.info(
            "class_report.agent_done agent=resumo_llm_turma class_id=%s duration_ms=%d",
            request.class_id,
            int((time.perf_counter() - start_resumo) * 1000),
        )
    except Exception:
        logger.exception(
            "class_report.failed agent=resumo_llm_turma class_id=%s periodo=%s",
            request.class_id,
            request.periodo_referencia,
        )
        raise

    try:
        start_recomendacao = time.perf_counter()
        recomendacao_data = _parse_llm_json(
            OpenAIClient.generate(
                build_class_recomendacao_para_professor_turma_prompt(
                    request,
                    agregado_data,
                    risco_data,
                    resumo_data,
                )
            )
        )
        recomendacao = ClassRecomendacaoParaProfessorTurmaResponse(
            **recomendacao_data
        )
        logger.info(
            "class_report.agent_done agent=recomendacao_para_professor_turma class_id=%s duration_ms=%d",
            request.class_id,
            int((time.perf_counter() - start_recomendacao) * 1000),
        )
    except Exception:
        logger.exception(
            "class_report.failed agent=recomendacao_para_professor_turma class_id=%s periodo=%s",
            request.class_id,
            request.periodo_referencia,
        )
        raise

    try:
        start_plano = time.perf_counter()
        plano_data = _parse_llm_json(
            OpenAIClient.generate(
                build_class_plano_acao_turma_prompt(
                    request,
                    agregado_data,
                    risco_data,
                    resumo_data,
                    recomendacao_data,
                )
            )
        )
        plano = ClassPlanoAcaoTurmaResponse(**plano_data)
        logger.info(
            "class_report.agent_done agent=plano_acao_turma class_id=%s duration_ms=%d",
            request.class_id,
            int((time.perf_counter() - start_plano) * 1000),
        )
    except Exception:
        logger.exception(
            "class_report.failed agent=plano_acao_turma class_id=%s periodo=%s",
            request.class_id,
            request.periodo_referencia,
        )
        raise

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
