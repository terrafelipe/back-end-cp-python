"""Cliente da Groq (API compatível com a da OpenAI), atrás de uma função.

Trocar de provedor é reescrever `completar_json`; o resto do sistema só
conhece a assinatura dela e a exceção `FalhaLLM`.
"""

import json
import urllib.request

URL = "https://api.groq.com/openai/v1/chat/completions"
# Sem User-Agent próprio o urllib se apresenta como "Python-urllib", que
# proxies como o Cloudflare (na frente da Groq) costumam recusar com 403.
USER_AGENT = "gestor-estoque/1.0"


class FalhaLLM(Exception):
    """A LLM não respondeu, demorou demais ou respondeu fora do formato."""


def completar_json(mensagens: list[dict], *, modelo: str, chave: str, timeout_s: float) -> dict:
    corpo = json.dumps({
        "model": modelo,
        "messages": mensagens,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    pedido = urllib.request.Request(
        URL,
        data=corpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=timeout_s) as resposta:
            dados = json.load(resposta)
        conteudo = json.loads(dados["choices"][0]["message"]["content"])
    except (OSError, ValueError, KeyError, IndexError, TypeError) as erro:
        # OSError cobre URLError, HTTPError e timeout; ValueError, JSON inválido.
        raise FalhaLLM(f"{type(erro).__name__}: {erro}") from erro
    if not isinstance(conteudo, dict):
        raise FalhaLLM("A resposta não é um objeto JSON.")
    return conteudo
