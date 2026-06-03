from pydantic import BaseModel
from typing import List, Union

class StudentSummary(BaseModel):
    student_id: Union[str, int]
    desempenho_geral: str
    engajamento: str
    risco_desengajamento: str
    dificuldades_aprendizagem: str

class ClassReportRequest(BaseModel):
    class_id: Union[str, int]
    periodo_referencia: str
    observacao_professor_turma: str
    students: List[StudentSummary]


class ClassAgregadoAlunosResponse(BaseModel):
    desempenho_medio_turma: str
    principais_dificuldades_turma: str
    nivel_engajamento_turma: str


class ClassRiscoColetivoResponse(BaseModel):
    risco_desengajamento_turma: str
    necessita_intervencao_coletiva: bool


class ClassResumoLLMTurmaResponse(BaseModel):
    resumo_llm_turma: str


class ClassRecomendacaoParaProfessorTurmaResponse(BaseModel):
    recomendacao_para_professor_turma: str


class ClassPlanoAcaoTurmaResponse(BaseModel):
    plano_acao_turma: str


class ClassSaidaLLMTurmaResponse(BaseModel):
    resumo_llm_turma: str
    recomendacao_para_professor_turma: str
    plano_acao_turma: str


class ClassReportResponse(BaseModel):
    class_id: Union[str, int]
    periodo_referencia: str
    agregado_alunos: ClassAgregadoAlunosResponse
    risco_coletivo: ClassRiscoColetivoResponse
    saida_llm_turma: ClassSaidaLLMTurmaResponse
