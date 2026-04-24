import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import (
    QUERY_ATIVIDADES,
    QUERY_CRONOGRAMA_UNIDADE_MEDIDA,
    QUERY_CRONOGRAMA_LINHA_BASE,
    QUERY_PREDECESSORES_SUCESSORES,
    QUERY_METAS,
)


def buscar_atividades(id_projeto: str, incluir_datas_nos_servicos: bool = True) -> pd.DataFrame:
    """
    Retorna todas as atividades e seus serviços de um projeto.
    Cada linha representa um serviço dentro de uma atividade.
    """
    dados = fazer_requisicao(QUERY_ATIVIDADES, {
        "projectId": id_projeto,
        "jobsWithDates": incluir_datas_nos_servicos,
    })

    projeto = dados["me"]["project"]
    linhas = []

    for pavimento in projeto["floorsPage"]["nodes"]:
        for atividade in pavimento["activitiesPage"]["nodes"]:
            base = {
                "id_projeto":               id_projeto,
                "nome_projeto":             projeto["name"],
                "id_pavimento":             pavimento["id"],
                "nome_pavimento":           pavimento["name"],
                "id_atividade":             atividade["id"],
                "parte_atividade":          atividade.get("part"),
                "codigo_wbs_atividade":     atividade.get("wbsCode"),
                "servico_atividade":        (atividade.get("service") or {}).get("name"),
                "perc_concluido_atividade": atividade.get("percentageCompleted"),
                "perc_esperado_atividade":  atividade.get("expectedPercentageCompleted"),
                "inicio_atividade":         atividade.get("startAt"),
                "fim_atividade":            atividade.get("endAt"),
                "duracao_atividade":        atividade.get("duration"),
            }

            servicos = atividade.get("jobs") or []
            if servicos:
                for s in servicos:
                    linhas.append({**base,
                        "id_servico":             s.get("id"),
                        "nome_servico":           s.get("name"),
                        "codigo_wbs_servico":     s.get("wbsCode"),
                        "perc_concluido_servico": s.get("percentageCompleted"),
                        "perc_esperado_servico":  s.get("expectedPercentageCompleted"),
                        "inicio_servico":         s.get("startAt"),
                        "fim_servico":            s.get("endAt"),
                        "duracao_servico":        s.get("duration"),
                    })
            else:
                linhas.append({**base,
                    "id_servico": None, "nome_servico": None,
                    "codigo_wbs_servico": None, "perc_concluido_servico": None,
                    "perc_esperado_servico": None, "inicio_servico": None,
                    "fim_servico": None, "duracao_servico": None,
                })

    return pd.DataFrame(linhas)


def buscar_unidades_medida(id_projeto: str) -> pd.DataFrame:
    """
    Retorna atividades e serviços com suas unidades de medida.
    """
    dados = fazer_requisicao(QUERY_CRONOGRAMA_UNIDADE_MEDIDA, {"projectId": id_projeto})
    linhas = []

    for pavimento in dados["me"]["project"]["floorsPage"]["nodes"]:
        for atividade in pavimento["activitiesPage"]["nodes"]:
            unidade = atividade.get("measurementUnit") or {}
            base = {
                "id_projeto":                  id_projeto,
                "id_pavimento":                pavimento["id"],
                "nome_pavimento":              pavimento["name"],
                "id_atividade":                atividade["id"],
                "servico_atividade":           (atividade.get("service") or {}).get("name"),
                "unidade_nome":                unidade.get("name"),
                "unidade_tipo":                unidade.get("type"),
                "unidade_quantidade_max":      (unidade.get("quantity") or {}).get("max"),
            }

            jobs = atividade.get("jobs") or []
            if jobs:
                for job in jobs:
                    u = job.get("measurementUnit") or {}
                    linhas.append({**base,
                        "id_servico":                    job.get("id"),
                        "nome_servico":                  job.get("name"),
                        "unidade_servico_nome":          u.get("name"),
                        "unidade_servico_tipo":          u.get("type"),
                        "unidade_servico_quantidade_max": (u.get("quantity") or {}).get("max"),
                    })
            else:
                linhas.append({**base, "id_servico": None, "nome_servico": None})

    return pd.DataFrame(linhas)


def buscar_linha_base(id_projeto: str) -> pd.DataFrame:
    """
    Retorna as atividades e serviços da linha de base ativa do projeto.
    """
    dados = fazer_requisicao(QUERY_CRONOGRAMA_LINHA_BASE, {
        "projectId": id_projeto,
        "withDates": True,
    })

    baseline = dados["me"]["project"].get("activeBaseline")
    if not baseline:
        return pd.DataFrame()

    linhas = []
    for step in baseline["baselineStepsPage"]["nodes"]:
        for atividade in step["activities"]:
            for job in atividade.get("jobs") or []:
                linhas.append({
                    "id_projeto":        id_projeto,
                    "id_atividade":      atividade["id"],
                    "servico_atividade": (atividade.get("service") or {}).get("name"),
                    "nome_servico":      job.get("name"),
                    "inicio_linha_base": job.get("startAt"),
                    "fim_linha_base":    job.get("endAt"),
                    "nome_pavimento":    (atividade.get("floor") or {}).get("name"),
                    "posicao_pavimento": (atividade.get("floor") or {}).get("position"),
                })

    return pd.DataFrame(linhas)


def buscar_predecessores_sucessores(id_projeto: str) -> pd.DataFrame:
    """
    Retorna as relações de precedência entre atividades do projeto.
    """
    dados = fazer_requisicao(QUERY_PREDECESSORES_SUCESSORES, {"projectId": id_projeto})
    linhas = []

    for atividade in dados["me"]["project"]["activitiesPage"]["nodes"]:
        for relacao in atividade["predecessorsPage"]["nodes"]:
            linhas.append({
                "id_projeto":          id_projeto,
                "id_relacao":          relacao.get("id"),
                "id_predecessor":      (relacao.get("predecessor") or {}).get("id"),
                "nome_predecessor":    ((relacao.get("predecessor") or {}).get("service") or {}).get("name"),
                "id_sucessor":         (relacao.get("successor") or {}).get("id"),
                "nome_sucessor":       ((relacao.get("successor") or {}).get("service") or {}).get("name"),
                "atributo_base":       relacao.get("baseAttribute"),
                "atributo_precedencia": relacao.get("precedenceAttribute"),
            })

    return pd.DataFrame(linhas)


def buscar_metas(id_projeto: str) -> pd.DataFrame:
    """
    Retorna as metas cadastradas no projeto.
    """
    dados = fazer_requisicao(QUERY_METAS, {"projectId": id_projeto})
    metas = dados["me"]["project"]["goalsPage"]["nodes"]

    tabela = pd.DataFrame(metas)
    if not tabela.empty:
        tabela.rename(columns={
            "id": "id_meta", "name": "nome_meta",
            "goalAt": "data_meta", "createdAt": "data_criacao",
            "updatedAt": "data_atualizacao",
        }, inplace=True)
        tabela["id_projeto"] = id_projeto

    return tabela


def buscar_responsaveis(id_projeto: str) -> pd.DataFrame:
    """
    Retorna a lista de responsáveis (contractors) de um projeto,
    com as atividades e serviços que cada um é responsável.

    Colunas:
      id_projeto, id_responsavel, nome_responsavel,
      id_atividade, nome_pavimento_atividade,
      id_servico, nome_servico,
      id_servico_job, nome_servico_job, parte_servico_job
    """
    dados = fazer_requisicao(QUERY_RESPONSAVEIS, {"projectId": id_projeto})
    contractors = dados["me"]["project"]["contractorsPage"]["nodes"]

    linhas = []
    for responsavel in contractors:
        base_responsavel = {
            "id_projeto": id_projeto,
            "id_responsavel": responsavel["id"],
            "nome_responsavel": responsavel["name"],
        }

        vinculos = responsavel["workPackageResponsiblesPage"]["nodes"]

        if not vinculos:
            linhas.append(base_responsavel)
            continue

        for vinculo in vinculos:
            atividade = vinculo.get("activity") or {}
            job = vinculo.get("activityJob") or {}
            servico = atividade.get("service") or {}

            linhas.append({
                **base_responsavel,
                # atividade
                "id_atividade": atividade.get("id"),
                "nome_pavimento_atividade": atividade.get("floorNameWithActivityPart"),
                "id_servico": servico.get("id"),
                "nome_servico": servico.get("name"),
                # job (serviço filho)
                "id_atividade_job": job.get("activityId"),
                "id_servico_job": job.get("id"),
                "nome_servico_job": job.get("name"),
                "parte_servico_job": job.get("part"),
            })

    return pd.DataFrame(linhas)