# ──────────────────────────────────────────────
# PROJETOS
# ──────────────────────────────────────────────

QUERY_PROJETOS = """
query Projects($first: Int, $after: String) {
  me {
    id
    name
    projectsPage(first: $first, after: $after) {
      totalCount
      pageInfo { hasNextPage startCursor endCursor }
      nodes { id name area phase }
    }
  }
}
"""

# ──────────────────────────────────────────────
# CRONOGRAMA
# ──────────────────────────────────────────────

QUERY_RESPONSAVEIS = """
query ProjectResponsiblesList($projectId: ID!) {
  me {
    project(id: $projectId) {
      contractorsPage {
        nodes {
          id
          name
          workPackageResponsiblesPage {
            nodes {
              activity {
                floorNameWithActivityPart
                id
                service { id name }
              }
              activityJob {
                activityId
                id
                name
                part
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_ATIVIDADES = """
query Activities($projectId: ID!, $jobsWithDates: Boolean) {
  me {
    project(id: $projectId) {
      name
      floorsPage {
        nodes {
          id
          name
          activitiesPage {
            nodes {
              id part wbsCode
              percentageCompleted expectedPercentageCompleted
              startAt endAt
              duration: workDuration
              service { name }
              floor   { name }
              jobs(withDates: $jobsWithDates) {
                id name wbsCode
                percentageCompleted expectedPercentageCompleted
                startAt endAt duration
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_CRONOGRAMA_UNIDADE_MEDIDA = """
fragment MeasurementUnit on MeasurementUnit {
  id name type
  quantity { max }
  checklist { max { id name position } }
}

query Projects($projectId: ID!) {
  me {
    project(id: $projectId) {
      floorsPage(sortBy: [{ attribute: "position", order: "desc" }]) {
        nodes {
          id name position
          activitiesPage {
            nodes {
              id part wbsCode
              percentageCompleted startAt endAt workDuration
              measurementUnit { ...MeasurementUnit }
              service { name }
              floor   { name }
              jobs(withDates: true) {
                id name wbsCode
                percentageCompleted startAt endAt duration
                measurementUnit { ...MeasurementUnit }
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_CRONOGRAMA_LINHA_BASE = """
query Baseline($projectId: ID!, $withDates: Boolean!) {
  me {
    project(id: $projectId) {
      activeBaseline {
        baselineStepsPage {
          nodes {
            id startAt endAt
            activities {
              id
              service { name }
              jobs(withDates: $withDates) { name startAt endAt }
              floor { name position }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_PREDECESSORES_SUCESSORES = """
query PredecessorsSuccessors($projectId: ID!) {
  me {
    project(id: $projectId) {
      id name
      activitiesPage {
        totalCount
        nodes {
          id
          service { name }
          jobs { id name }
          predecessorsPage {
            totalCount
            nodes {
              id baseAttribute precedenceAttribute
              predecessor { id service { name } }
              successor   { id service { name } }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_METAS = """
query GoalsPageAndLobVersion($projectId: ID!) {
  me {
    project(id: $projectId) {
      goalsPage {
        nodes {
          id name goalAt createdAt updatedAt
          lobVersion {
            id name description createdAt updatedAt
            projectId source restoredAt restoredById
          }
        }
      }
    }
  }
}
"""

# ──────────────────────────────────────────────
# MEDIÇÕES
# ──────────────────────────────────────────────

QUERY_DATAS_MEDICOES = """
query MeasurementsDates($projectId: ID!, $sortBy: [SortBy!], $after: String) {
  me {
    project(id: $projectId) {
      id name
      measurementsTasksPage(sortBy: $sortBy, after: $after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes { id measuredIn }
      }
    }
  }
}
"""

QUERY_DETALHE_MEDICAO = """
query MeasurementTaskData($projectId: ID!, $measurementTaskId: ID!, $after: String) {
  me {
    project(id: $projectId) {
      id name
      measurementTask(id: $measurementTaskId) {
        id measuredIn
        measurementsData {
          user { id email profile { name } }
        }
        measurementsPage(after: $after) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes {
            basePercentageCompleted expectedPercentageCompleted
            percentageCompleted workType
            work {
              ... on Activity {
                id workDuration part parts
                measurementUnit { type symbol }
                service { id name }
                floor   { id name }
              }
              ... on ActivityJob {
                id duration activityId name part partsAttrs
                measurementUnit { type symbol }
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_ULTIMA_MEDICAO = """
query LastMeasurementTaskData($projectId: ID!, $after: String) {
  me {
    project(id: $projectId) {
      id name
      lastMeasurementTask {
        id measuredIn
        measurementsData {
          user { id email profile { name } }
        }
        measurementsPage(after: $after) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes {
            basePercentageCompleted expectedPercentageCompleted
            percentageCompleted workType
            work {
              ... on Activity {
                id workDuration part parts
                measurementUnit { type symbol }
                service { id name }
                floor   { id name }
              }
              ... on ActivityJob {
                id duration activityId name part partsAttrs
                measurementUnit { type symbol }
              }
            }
          }
        }
      }
    }
  }
}
"""

# ──────────────────────────────────────────────
# ORÇAMENTO
# ──────────────────────────────────────────────

QUERY_RELATORIOS_ORCAMENTO = """
query BudgetReportsPage($projectId: ID!) {
  me {
    project(id: $projectId) {
      budgetReportsPage {
        nodes { id name }
      }
    }
  }
}
"""

# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

QUERY_DASHBOARD = """
query DefaultDashboardData($projectId: ID!, $perspective: String) {
  me {
    project(id: $projectId) {
      detailedDashboard(perspective: $perspective) {
        sCurve monthlyProgress generalInfo 
      }
      workPackageEvolution(perspective: $perspective)
      floorEvolution(perspective: $perspective)
    }
  }
}
"""


QUERY_DASHBOARD_EVOLUCAO_PACOTES = """
query DefaultDashboardWorkPackageEvolution($projectId: ID!) {
  me {
    project(id: $projectId) {
      workPackageEvolution
    }
  }
}
"""

QUERY_DASHBOARD_EVOLUCAO_PAVIMENTOS = """
query DefaultDashboardFloorEvolution($projectId: ID!) {
  me {
    project(id: $projectId) {
      floorEvolution
    }
  }
}
"""


# ──────────────────────────────────────────────
# RESTRIÇÕES — KANBAN
# ──────────────────────────────────────────────

QUERY_KANBAN = """
query kanbanStepsAndTasks {
  me {
    taskSummary {
      userTasks
      weekTasks
      lateTasks
    }
    kanbanStepsPage {
      nodes {
        name
        tasksPage {
          nodes {
            id
            title
            createdAt
            taskChecklists {
              id
              description
              createdAt
              doneAt
            }
          }
        }
      }
    }
  }
}
"""
