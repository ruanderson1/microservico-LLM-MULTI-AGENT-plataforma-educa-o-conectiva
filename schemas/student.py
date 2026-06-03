from pydantic import BaseModel
from typing import List, Optional, Union


class Activity(BaseModel):
    tipo: str
    nota_maxima: Optional[float] = None
    notaMaxima: Optional[float] = None
    pontuacao: float
    peso: Optional[float] = 1
    observacoes: Optional[str] = ""


class NotesPayload(BaseModel):
    total: Optional[int] = 0
    media: Optional[float] = 0
    detalhes: List[Activity] = []


class AttendanceDetail(BaseModel):
    data: Optional[str] = ""
    tipo: Optional[str] = ""


class AttendancePayload(BaseModel):
    total_presencas: Optional[int] = 0
    total_faltas: Optional[int] = 0
    total_registros: Optional[int] = 0
    detalhes: List[AttendanceDetail] = []


class ObservationsPayload(BaseModel):
    professor: Optional[str] = ""
    pais: Optional[str] = ""
    geral: Optional[str] = ""


class StudentReportRequest(BaseModel):
    student_id: Union[str, int]
    periodo_referencia: str

    # Current backend payload format.
    nome: Optional[str] = ""
    notas: Optional[NotesPayload] = None
    frequencia: Optional[AttendancePayload] = None
    observacoes: Optional[ObservationsPayload] = None

    # Backward-compatible legacy payload format.
    observacao_professor: Optional[str] = ""
    observacao_pais: Optional[str] = ""
    atividades: List[Activity] = []


class AcademicoResponse(BaseModel):
    desempenho_geral: str
    evolucao_recente: str
    dificuldades_aprendizagem: str
    pontos_fortes_aprendizagem: str


class EmocionalResponse(BaseModel):
    estado_emocional_geral: str
    engajamento: str


class RiscoResponse(BaseModel):
    risco_desempenho_baixo: str
    risco_desengajamento: str
    necessita_intervencao: bool


class ResumoLLMResponse(BaseModel):
    resumo_llm: str


class RecomendacaoParaProfessorResponse(BaseModel):
    recomendacao_para_professor: str


class RecomendacaoParaPaisResponse(BaseModel):
    recomendacao_para_pais: str


class PlanoAcaoSugeridoResponse(BaseModel):
    plano_acao_sugerido: str


class SaidaLLMResponse(BaseModel):
    resumo_llm: str
    recomendacao_para_professor: str
    recomendacao_para_pais: str
    plano_acao_sugerido: str


class StudentReportResponse(BaseModel):
    student_id: Union[str, int]
    periodo_referencia: str
    academico: AcademicoResponse
    emocional: EmocionalResponse
    risco: RiscoResponse
    saida_llm: SaidaLLMResponse
