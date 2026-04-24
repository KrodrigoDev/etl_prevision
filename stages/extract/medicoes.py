import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import (
    QUERY_DATAS_MEDICOES,
    QUERY_DETALHE_MEDICAO,
    QUERY_ULTIMA_MEDICAO,
)


def buscar_datas_medicoes(id_projeto: str, ordem: str = "desc") -> pd.DataFrame:
    """
    Retorna todas as datas de medição de um projeto.
    Parâmetro 'ordem': 'desc' (mais recente primeiro) ou 'asc' (mais antiga primeiro).
    Colunas: id_medicao, data_medicao, id_projeto.
    """
    todos = []
    cursor = None

    while True:
        dados = fazer_requisicao(QUERY_DATAS_MEDICOES, {
            "projectId": id_projeto,
            "after": cursor,
            "sortBy": [{"attribute": "measuredIn", "order": ordem}],
        })
        pagina = dados["me"]["project"]["measurementsTasksPage"]
        todos.extend(pagina["nodes"])

        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    tabela = pd.DataFrame(todos)
    if not tabela.empty:
        tabela.rename(columns={"id": "id_medicao", "measuredIn": "data_medicao"}, inplace=True)
        tabela["id_projeto"] = id_projeto

    return tabela


def _extrair_linhas_medicao(id_projeto: str, medicao: dict, pagina: dict) -> list:
    """
    Função auxiliar: transforma os nodes de uma página de medição em lista de dicionários.
    """
    dados_medicao = medicao.get("measurementsData") or []
    usuario = (dados_medicao[0].get("user") or {}) if dados_medicao else {}

    linhas = []
    for item in pagina["nodes"]:
        work = item.get("work") or {}
        base = {
            "id_projeto":            id_projeto,
            "id_medicao":            medicao.get("id"),
            "data_medicao":          medicao.get("measuredIn"),
            "usuario_id":            usuario.get("id"),
            "usuario_nome":          (usuario.get("profile") or {}).get("name"),
            "usuario_email":         usuario.get("email"),
            "percentual_concluido":  item.get("percentageCompleted"),
            "percentual_base":       item.get("basePercentageCompleted"),
            "percentual_esperado":   item.get("expectedPercentageCompleted"),
            "tipo_trabalho":         item.get("workType"),
        }

        if "service" in work:  # Activity
            linhas.append({**base,
                "tipo_registro":  "atividade",
                "id_atividade":   work.get("id"),
                "nome_servico":   (work.get("service") or {}).get("name"),
                "id_pavimento":   (work.get("floor") or {}).get("id"),
                "nome_pavimento": (work.get("floor") or {}).get("name"),
                "duracao":        work.get("workDuration"),
                "unidade_tipo":   (work.get("measurementUnit") or {}).get("type"),
                "unidade_simbolo": (work.get("measurementUnit") or {}).get("symbol"),
            })
        else:  # ActivityJob
            linhas.append({**base,
                "tipo_registro":  "servico",
                "id_servico":     work.get("id"),
                "nome_servico":   work.get("name"),
                "id_atividade":   work.get("activityId"),
                "duracao":        work.get("duration"),
                "unidade_tipo":   (work.get("measurementUnit") or {}).get("type"),
                "unidade_simbolo": (work.get("measurementUnit") or {}).get("symbol"),
            })

    return linhas


def buscar_detalhe_medicao(id_projeto: str, id_medicao: str) -> pd.DataFrame:
    """
    Retorna o detalhamento completo de uma medição específica.
    Colunas: id_projeto, id_medicao, data_medicao, usuario, percentuais, tipo_registro, etc.
    """
    linhas = []
    cursor = None

    while True:
        dados = fazer_requisicao(QUERY_DETALHE_MEDICAO, {
            "projectId": id_projeto,
            "measurementTaskId": id_medicao,
            "after": cursor,
        })
        medicao = dados["me"]["project"]["measurementTask"]
        pagina = medicao["measurementsPage"]

        linhas.extend(_extrair_linhas_medicao(id_projeto, medicao, pagina))

        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    return pd.DataFrame(linhas)


def buscar_ultima_medicao(id_projeto: str) -> pd.DataFrame:
    """
    Retorna o detalhamento da última medição do projeto.
    """
    linhas = []
    cursor = None

    while True:
        dados = fazer_requisicao(QUERY_ULTIMA_MEDICAO, {
            "projectId": id_projeto,
            "after": cursor,
        })
        medicao = dados["me"]["project"].get("lastMeasurementTask")
        if not medicao:
            return pd.DataFrame()

        pagina = medicao["measurementsPage"]
        linhas.extend(_extrair_linhas_medicao(id_projeto, medicao, pagina))

        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    return pd.DataFrame(linhas)


def buscar_todas_medicoes_projeto(id_projeto: str) -> pd.DataFrame:
    """
    Retorna o detalhamento de TODAS as medições de um projeto.
    Internamente chama buscar_datas_medicoes + buscar_detalhe_medicao para cada data.
    """
    datas = buscar_datas_medicoes(id_projeto)
    lista = []

    for _, linha in datas.iterrows():
        print(f"   → Medição {linha['id_medicao']} ({linha['data_medicao']})")
        try:
            df = buscar_detalhe_medicao(id_projeto, linha["id_medicao"])
            lista.append(df)
        except Exception as erro:
            print(f"      Erro: {erro}")

    return pd.concat(lista, ignore_index=True) if lista else pd.DataFrame()