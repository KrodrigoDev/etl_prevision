import os

from dotenv import load_dotenv

load_dotenv()
# ──────────────────────────────────────────────
# CONFIGURAÇÃO — altere apenas aqui
# ──────────────────────────────────────────────

ENDERECO_API = f"{os.getenv('ENDERECO_API')}"

CABECALHOS = {
    "Accept": "application/json",
    "UserAuthorization": f"{os.getenv('USERAUTHORIZATION')}",
    "Content-Type": "application/json",
}