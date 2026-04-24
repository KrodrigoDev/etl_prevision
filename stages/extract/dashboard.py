import json
import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import (
    QUERY_DASHBOARD,
    QUERY_DASHBOARD_EVOLUCAO_PACOTES,
    QUERY_DASHBOARD_EVOLUCAO_PAVIMENTOS,
)


# ──────────────────────────────────────────────
# Funções individuais por bloco do dashboard
# ──────────────────────────────────────────────

def buscar_dashboard_completo(id_projeto: str, perspectiva: str = "physical") -> pd.DataFrame:
    """
    Retorna curva S, progresso mensal e informações gerais do dashboard.
    Cada campo JSON é serializado como string para caber em uma célula do Power BI.
    Colunas: id_projeto, perspectiva, curva_s, progresso_mensal, info_geral,
             evolucao_pacotes, evolucao_pavimentos.
    """
    dados = fazer_requisicao(QUERY_DASHBOARD, {
        "projectId": id_projeto,
        "perspective": perspectiva,
    })
    projeto = dados["me"]["project"]
    dashboard = projeto["detailedDashboard"]

    return pd.DataFrame([{
        "id_projeto":          id_projeto,
        "perspectiva":         perspectiva,
        "curva_s":             json.dumps(dashboard.get("sCurve"),         ensure_ascii=False),
        "progresso_mensal":    json.dumps(dashboard.get("monthlyProgress"), ensure_ascii=False),
        "info_geral":          json.dumps(dashboard.get("generalInfo"),     ensure_ascii=False),
        "evolucao_pacotes":    json.dumps(projeto.get("workPackageEvolution"), ensure_ascii=False),
        "evolucao_pavimentos": json.dumps(projeto.get("floorEvolution"),    ensure_ascii=False),
    }])


def buscar_evolucao_pacotes(id_projeto: str) -> pd.DataFrame:
    """
    Retorna a evolução por pacote de trabalho de um projeto.
    O campo workPackageEvolution vem como JSON livre da API —
    cada entrada é expandida em uma linha.
    Colunas: id_projeto + campos retornados pela API.
    """
    dados = fazer_requisicao(QUERY_DASHBOARD_EVOLUCAO_PACOTES, {"projectId": id_projeto})
    evolucao = dados["me"]["project"].get("workPackageEvolution") or []

    if not evolucao:
        return pd.DataFrame()

    # A API pode retornar lista de dicts ou JSON string — normaliza os dois casos
    if isinstance(evolucao, str):
        evolucao = json.loads(evolucao)

    tabela = pd.json_normalize(evolucao)
    tabela.insert(0, "id_projeto", id_projeto)
    return tabela


def buscar_evolucao_pavimentos(id_projeto: str) -> pd.DataFrame:
    """
    Retorna a evolução por pavimento (lote) de um projeto.
    Colunas: id_projeto + campos retornados pela API.
    """
    dados = fazer_requisicao(QUERY_DASHBOARD_EVOLUCAO_PAVIMENTOS, {"projectId": id_projeto})
    evolucao = dados["me"]["project"].get("floorEvolution") or []

    if not evolucao:
        return pd.DataFrame()

    if isinstance(evolucao, str):
        evolucao = json.loads(evolucao)

    tabela = pd.json_normalize(evolucao)
    tabela.insert(0, "id_projeto", id_projeto)
    return tabela