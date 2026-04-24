import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import QUERY_PROJETOS


def buscar_projetos(itens_por_pagina: int = 100) -> pd.DataFrame:
    """
    Retorna todos os projetos da empresa.
    Colunas: id_projeto, nome_projeto, area, fase.
    Percorre automaticamente todas as páginas de resultados.
    """
    todos = []
    cursor = None

    while True:
        dados = fazer_requisicao(QUERY_PROJETOS, {"first": itens_por_pagina, "after": cursor})
        pagina = dados["me"]["projectsPage"]
        todos.extend(pagina["nodes"])

        if not pagina["pageInfo"]["hasNextPage"]:
            break
        cursor = pagina["pageInfo"]["endCursor"]

    tabela = pd.DataFrame(todos)
    tabela.rename(columns={"id": "id_projeto", "name": "nome_projeto",
                            "area": "area", "phase": "fase"}, inplace=True)
    return tabela