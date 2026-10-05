import io
import json
import socket
import urllib.error
import urllib.request

import pytest

from app.services.llm import cliente


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _devolver(conteudo: str, capturados: list):
    def falso(pedido, timeout):
        capturados.append((pedido, timeout))
        corpo = {"choices": [{"message": {"content": conteudo}}]}
        return RespostaFalsa(json.dumps(corpo).encode("utf-8"))
    return falso


def _chamar():
    return cliente.completar_json([{"role": "user", "content": "oi"}],
                                  modelo="m", chave="k", timeout_s=3)


def test_envia_modelo_chave_e_pede_json(monkeypatch):
    capturados = []
    monkeypatch.setattr(urllib.request, "urlopen",
                        _devolver('{"resumo": "ok", "prioridades": []}', capturados))
    assert _chamar() == {"resumo": "ok", "prioridades": []}
    pedido, timeout = capturados[0]
    assert pedido.full_url == cliente.URL and timeout == 3
    assert pedido.get_header("Authorization") == "Bearer k"
    assert pedido.get_header("User-agent").startswith("gestor-estoque")
    corpo = json.loads(pedido.data)
    assert corpo["model"] == "m"
    assert corpo["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("falha", [socket.timeout("timed out"), TimeoutError(),
                                   urllib.error.URLError("sem rede")])
def test_falha_de_rede_vira_falha_llm(monkeypatch, falha):
    def falso(pedido, timeout):
        raise falha
    monkeypatch.setattr(urllib.request, "urlopen", falso)
    with pytest.raises(cliente.FalhaLLM):
        _chamar()


@pytest.mark.parametrize("conteudo", ["não é json", '"texto solto"'])
def test_conteudo_fora_do_formato_vira_falha_llm(monkeypatch, conteudo):
    monkeypatch.setattr(urllib.request, "urlopen", _devolver(conteudo, []))
    with pytest.raises(cliente.FalhaLLM):
        _chamar()
