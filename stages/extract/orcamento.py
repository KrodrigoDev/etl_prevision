import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import QUERY_RELATORIOS_ORCAMENTO


# ──────────────────────────────────────────────
# ORÇAMENTO
# ──────────────────────────────────────────────

def buscar_relatorios_orcamento(id_projeto: str) -> pd.DataFrame:
    """
    Retorna os relatórios de orçamento de um projeto.
    Colunas: id_relatorio, nome_relatorio, id_projeto.
    """
    dados = fazer_requisicao(QUERY_RELATORIOS_ORCAMENTO, {"projectId": id_projeto})
    itens = dados["me"]["project"]["budgetReportsPage"]["nodes"]

    tabela = pd.DataFrame(itens)
    if not tabela.empty:
        tabela.rename(columns={"id": "id_relatorio", "name": "nome_relatorio"}, inplace=True)
        tabela["id_projeto"] = id_projeto

    return tabela