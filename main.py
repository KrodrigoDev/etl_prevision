import sys
from pathlib import Path

# Caminho da raiz do projeto
ROOT_PATH = Path(r"C:\Users\kaua.rodrigo\PycharmProjects\etl_prevision")

# Adiciona ao PYTHONPATH
if str(ROOT_PATH) not in sys.path:
    sys.path.append(str(ROOT_PATH))

from pathlib import Path

import pandas as pd

from stages.extract.projetos import buscar_projetos
from stages.extract.cronograma import (buscar_atividades, buscar_unidades_medida,
                                       buscar_linha_base, buscar_predecessores_sucessores,
                                       buscar_metas, buscar_responsaveis)
from stages.extract.medicoes import (buscar_datas_medicoes, buscar_ultima_medicao,
                                     buscar_todas_medicoes_projeto)
from stages.extract.orcamento import buscar_relatorios_orcamento
from stages.extract.restricoes import buscar_kanban

from stages.extract.dashboard import (buscar_dashboard_completo,
                                      buscar_evolucao_pacotes,
                                      buscar_evolucao_pavimentos)

# ──────────────────────────────────────────────
# Configuração de saída
# ──────────────────────────────────────────────

OUTPUT_PATH = Path(r'C:\Users\kaua.rodrigo\PycharmProjects\etl_prevision\files\output')


# ──────────────────────────────────────────────
# Funções auxiliares
# ──────────────────────────────────────────────

def _para_cada_projeto(projetos: pd.DataFrame, funcao, descricao: str) -> pd.DataFrame:
    """Itera sobre todos os projetos, chama a função e agrega os resultados."""
    lista = []
    print(f"\nBuscando {descricao}...")
    for _, p in projetos.iterrows():
        print(f"  → {p['nome_projeto']} (id={p['id_projeto']})")
        try:
            resultado = funcao(p["id_projeto"])
            if resultado is not None and not resultado.empty:
                lista.append(resultado)
        except Exception as e:
            print(f"     Erro: {e}")

    tabela = pd.concat(lista, ignore_index=True) if lista else pd.DataFrame()
    print(f"  {len(tabela)} registros encontrados.")
    return tabela


def _salvar(nome: str, tabela: pd.DataFrame, output_path: Path) -> None:
    """Salva a tabela como CSV separado por ponto e vírgula."""
    caminho = output_path / f"{nome}.csv"
    tabela.to_csv(caminho, sep=";", index=False)
    print(f"  ✔ {nome}.csv → {caminho}")


# ──────────────────────────────────────────────
# EXECUÇÃO PRINCIPAL
# ──────────────────────────────────────────────

if __name__ == "__main__":

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    # ── 1. Projetos ────────────────────────────────────────────────────────
    print("Buscando projetos...")
    tabela_projetos = buscar_projetos()
    print(f"  {len(tabela_projetos)} projetos encontrados.")

    # ── 2. Cronograma ──────────────────────────────────────────────────────
    tabela_atividades = _para_cada_projeto(tabela_projetos, buscar_atividades, "atividades do cronograma")
    tabela_unidades = _para_cada_projeto(tabela_projetos, buscar_unidades_medida, "unidades de medida")
    tabela_baseline = _para_cada_projeto(tabela_projetos, buscar_linha_base, "linha de base")
    tabela_relacoes = _para_cada_projeto(tabela_projetos, buscar_predecessores_sucessores, "predecessores e sucessores")
    tabela_metas = _para_cada_projeto(tabela_projetos, buscar_metas, "metas")
    tabela_responsaveis = _para_cada_projeto(tabela_projetos, buscar_responsaveis, "responsáveis do cronograma")

    # ── 3. Medições ────────────────────────────────────────────────────────
    tabela_datas_medicoes = _para_cada_projeto(tabela_projetos, buscar_datas_medicoes, "datas de medições")
    tabela_ultima_medicao = _para_cada_projeto(tabela_projetos, buscar_ultima_medicao, "última medição")
    tabela_todas_medicoes = _para_cada_projeto(tabela_projetos, buscar_todas_medicoes_projeto,
                                               "detalhe de todas as medições")

    # ── 4. Orçamento ───────────────────────────────────────────────────────
    tabela_orcamentos = _para_cada_projeto(tabela_projetos, buscar_relatorios_orcamento, "relatórios de orçamento")

    # ── 5. Restrições (Kanban) — não depende de projeto ───────────────────
    print("\nBuscando restrições (Kanban)...")
    try:
        tabela_kanban_tarefas, tabela_kanban_checklists = buscar_kanban()
        print(f"  {len(tabela_kanban_tarefas)} tarefas encontradas.")
        print(f"  {len(tabela_kanban_checklists)} itens de checklist encontrados.")
    except Exception as e:
        print(f"  Erro: {e}")
        tabela_kanban_tarefas = pd.DataFrame()
        tabela_kanban_checklists = pd.DataFrame()

    # ── 6. Dashboard — todos os projetos ──────────────────────────────────
    tabela_dashboard = _para_cada_projeto(tabela_projetos, buscar_dashboard_completo, "dashboard completo")
    tabela_evolucao_pacotes = _para_cada_projeto(tabela_projetos, buscar_evolucao_pacotes,
                                                 "evolução por pacote de trabalho")
    tabela_evolucao_pavimentos = _para_cada_projeto(tabela_projetos, buscar_evolucao_pavimentos,
                                                    "evolução por pavimento")

    # ── Salvar e exibir resumo ─────────────────────────────────────────────
    print("\n─── Tabelas disponíveis para o Power BI ───")
    tabelas = [
        # Projetos
        ("tabela_projetos", tabela_projetos),
        # Cronograma
        ("cronograma_tabela_atividades", tabela_atividades),
        ("cronograma_tabela_unidades", tabela_unidades),
        ("cronograma_tabela_baseline", tabela_baseline),
        ("cronograma_tabela_relacoes", tabela_relacoes),
        ("cronograma_tabela_metas", tabela_metas),
        ("cronograma_tabela_responsaveis", tabela_responsaveis),
        # # Medições
        ("medicoes_tabela_datas_medicoes", tabela_datas_medicoes),
        ("medicoes_tabela_ultima_medicao", tabela_ultima_medicao),
        ("medicoes_tabela_todas_medicoes", tabela_todas_medicoes),
        # # Orçamento
        ("orcamento_tabela_orcamentos", tabela_orcamentos),
        # Restrições
        ("restricoes_tabela_kanban_tarefas", tabela_kanban_tarefas),
        ("restricoes_tabela_kanban_checklists", tabela_kanban_checklists),
        # Dashboard
        ("dashboard_tabela_dashboard", tabela_dashboard),
        ("dashboard_tabela_evolucao_pacotes", tabela_evolucao_pacotes),
        ("dashboard_tabela_evolucao_pavimentos", tabela_evolucao_pavimentos),
    ]

    for nome, tabela in tabelas:
        if tabela.empty:
            print(f"  {nome:<30} → vazia")
            continue
        print(f"  {nome:<30} → {tabela.shape[0]} linhas, {tabela.shape[1]} colunas")
        _salvar(nome, tabela, OUTPUT_PATH)
