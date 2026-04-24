import requests
from config import ENDERECO_API, CABECALHOS


def fazer_requisicao(query: str, variaveis: dict = None) -> dict:
    """
    Envia uma query GraphQL para a API e retorna os dados.
    Levanta um erro se a API retornar mensagens de problema.
    """
    corpo = {"query": query}
    if variaveis:
        corpo["variables"] = variaveis

    resposta = requests.post(ENDERECO_API, json=corpo, headers=CABECALHOS)
    resposta.raise_for_status()

    json_retornado = resposta.json()
    if "errors" in json_retornado:
        raise ValueError(f"Erro retornado pela API: {json_retornado['errors']}")

    return json_retornado["data"]