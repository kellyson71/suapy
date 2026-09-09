"""Valida a troca OIDC no runner GitHub, sem imprimir tokens nem enviar pacotes.

Usa a troca documentada em https://docs.pypi.org/trusted-publishers/using-a-publisher/.
Somente o diagnóstico usa os endpoints OIDC; a publicação usa a action oficial.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(request):
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def check_auth():
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    bearer = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not bearer:
        raise RuntimeError("Execute pelo workflow release.yml no GitHub Actions, com id-token: write.")
    separator = "&" if "?" in url else "?"
    identity = request_json(Request(url + separator + "audience=pypi",
                                   headers={"Authorization": "Bearer " + bearer}))
    token = identity.get("value")
    if not isinstance(token, str) or not token:
        raise RuntimeError("GitHub não retornou uma identidade OIDC válida.")
    minted = request_json(Request("https://pypi.org/_/oidc/mint-token",
        data=json.dumps({"token": token}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"))
    if not isinstance(minted.get("token"), str) or not minted["token"]:
        raise RuntimeError("PyPI não retornou uma credencial temporária.")
    print("Autenticação OIDC aceita pelo PyPI. Nenhum pacote foi enviado.")


def main():
    try:
        check_auth()
    except HTTPError as exc:
        # Nunca imprime corpo arbitrário da resposta, tokens ou headers.
        print(f"Autenticação recusada (HTTP {exc.code}). Confira o publicador GitHub: "
              "kellyson71/suapy, release.yml, environment pypi.")
        return 1
    except (URLError, ValueError, RuntimeError):
        print("Não foi possível validar OIDC. Execute no GitHub Actions e confira permissões e conectividade.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
