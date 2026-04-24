import pandas as pd
from stages.extract.cliente import fazer_requisicao
from stages.extract.queries import QUERY_KANBAN


def buscar_kanban() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Busca colunas, tarefas e checklists do Kanban.
    Não recebe id_projeto — a query retorna dados do usuário autenticado.

    Retorna duas tabelas:
      - tabela_tarefas   → uma linha por tarefa (com coluna e resumo)
      - tabela_checklists → uma linha por item de checklist de cada tarefa
    """
    dados = fazer_requisicao(QUERY_KANBAN)

    resumo     = dados["me"]["taskSummary"]
    colunas    = dados["me"]["kanbanStepsPage"]["nodes"]

    linhas_tarefas     = []
    linhas_checklists  = []

    for coluna in colunas:
        nome_coluna = coluna["name"]

        for tarefa in coluna["tasksPage"]["nodes"]:
            linhas_tarefas.append({
                "nome_coluna":          nome_coluna,
                "id_tarefa":            tarefa["id"],
                "titulo_tarefa":        tarefa["title"],
                "data_criacao_tarefa":  tarefa["createdAt"],
                # resumo geral (igual para todas as linhas — útil no Power BI)
                "total_minhas_tarefas": resumo.get("userTasks"),
                "total_tarefas_semana": resumo.get("weekTasks"),
                "total_tarefas_atrasadas": resumo.get("lateTasks"),
            })

            for checklist in tarefa.get("taskChecklists") or []:
                linhas_checklists.append({
                    "id_tarefa":            tarefa["id"],
                    "titulo_tarefa":        tarefa["title"],
                    "nome_coluna":          nome_coluna,
                    "id_checklist":         checklist["id"],
                    "descricao_checklist":  checklist["description"],
                    "data_criacao_checklist": checklist["createdAt"],
                    "data_conclusao":       checklist.get("doneAt"),
                    "concluido":            checklist.get("doneAt") is not None,
                })

    return pd.DataFrame(linhas_tarefas), pd.DataFrame(linhas_checklists)