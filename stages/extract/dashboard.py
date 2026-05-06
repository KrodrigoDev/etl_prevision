import json
import logging
from pathlib import Path

import pandas as pd

from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import (
    QUERY_DASHBOARD,
    QUERY_DASHBOARD_EVOLUCAO_PACOTES,
    QUERY_DASHBOARD_EVOLUCAO_PAVIMENTOS,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Funções individuais por bloco do dashboard
# ──────────────────────────────────────────────

def _salvar(nome: str, tabela: pd.DataFrame, output_path: Path) -> None:
    caminho = output_path / f"{nome}.csv"
    tabela.to_csv(caminho, sep=";", index=False, encoding='utf-8-sig')
    logger.info(f"{nome}.csv salvo em: {caminho}")


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

def explodir_dashboard(df: pd.DataFrame) -> None:
    ID_COL = 'id_projeto'

    def parse_json_col(series):
        return series.apply(lambda x: json.loads(x) if pd.notnull(x) and x != '' else None)

    # ─────────────────────────────────────────────
    # 1. info_geral  →  relação 1:1
    #    resultado: df_info_geral com id_projeto + campos do dict
    # ─────────────────────────────────────────────
    df['info_geral'] = parse_json_col(df['info_geral'])

    df_info_geral = pd.json_normalize(df['info_geral'])
    df_info_geral.insert(0, ID_COL, df[ID_COL].values)

    # ─────────────────────────────────────────────
    # 2. evolucao_pacotes  →  relação 1:N
    #    cada pacote vira uma linha; mantém id_projeto
    # ─────────────────────────────────────────────
    df['evolucao_pacotes'] = parse_json_col(df['evolucao_pacotes'])

    df_pacotes = (
        df[[ID_COL, 'evolucao_pacotes']]
        .explode('evolucao_pacotes')
        .reset_index(drop=True)
    )
    df_pacotes = pd.concat(
        [df_pacotes[[ID_COL]],
         pd.json_normalize(df_pacotes['evolucao_pacotes'])],
        axis=1
    )

    # ─────────────────────────────────────────────
    # 3. evolucao_pavimentos  →  relação 1:N
    #    mesma lógica dos pacotes
    # ─────────────────────────────────────────────
    df['evolucao_pavimentos'] = parse_json_col(df['evolucao_pavimentos'])

    df_pavimentos = (
        df[[ID_COL, 'evolucao_pavimentos']]
        .explode('evolucao_pavimentos')
        .reset_index(drop=True)
    )
    df_pavimentos = pd.concat(
        [df_pavimentos[[ID_COL]],
         pd.json_normalize(df_pavimentos['evolucao_pavimentos'])],
        axis=1
    )

    # ─────────────────────────────────────────────
    # 4. curva_s  →  arrays paralelos → 1:N por data
    #    campos: dates, base, expected, realized, measured
    # ─────────────────────────────────────────────
    df['curva_s'] = parse_json_col(df['curva_s'])

    def explode_parallel_arrays(row, id_val):
        """Transforma dict de arrays paralelos em lista de dicts."""
        if row is None:
            return []
        keys = [k for k in row if k != 'dates']
        return [
            {ID_COL: id_val, 'date': row['dates'][i], **{k: row[k][i] for k in keys}}
            for i in range(len(row['dates']))
        ]

    records_curva_s = []
    for id_val, row in zip(df[ID_COL], df['curva_s']):
        records_curva_s.extend(explode_parallel_arrays(row, id_val))

    df_curva_s = pd.DataFrame(records_curva_s)

    # ─────────────────────────────────────────────
    # 5. progresso_mensal  →  mesma lógica da curva_s
    #    campos: dates, base, expected, realized
    # ─────────────────────────────────────────────
    df['progresso_mensal'] = parse_json_col(df['progresso_mensal'])

    records_progresso = []
    for id_val, row in zip(df[ID_COL], df['progresso_mensal']):
        records_progresso.extend(explode_parallel_arrays(row, id_val))

    df_progresso_mensal = pd.DataFrame(records_progresso)

    # ─────────────────────────────────────────────
    # 6. df base limpo  (sem as colunas explodidas)
    # ─────────────────────────────────────────────
    colunas_json = ['curva_s', 'progresso_mensal', 'info_geral',
                    'evolucao_pacotes', 'evolucao_pavimentos']

    df_base = df.drop(columns=colunas_json)

    # ─────────────────────────────────────────────
    # 7. Exportar (opcional)
    # ─────────────────────────────────────────────

    output_path = Path(r'C:\Users\kaua.rodrigo\PycharmProjects\etl_prevision\files\output')
    output_path.mkdir(parents=True, exist_ok=True)

    _salvar('base', df_base, output_path)
    _salvar('info_geral', df_info_geral, output_path)
    _salvar('evolucao_pacotes', df_pacotes, output_path)
    _salvar('evolucao_pavimentos', df_pavimentos, output_path)
    _salvar('curva_s', df_curva_s, output_path)
    _salvar('progresso_mensal', df_progresso_mensal, output_path)


    print("DFs gerados:")
    print(f"  df_base:            {df_base.shape}")
    print(f"  df_info_geral:      {df_info_geral.shape}")
    print(f"  df_pacotes:         {df_pacotes.shape}")
    print(f"  df_pavimentos:      {df_pavimentos.shape}")
    print(f"  df_curva_s:         {df_curva_s.shape}")
    print(f"  df_progresso_mensal:{df_progresso_mensal.shape}")