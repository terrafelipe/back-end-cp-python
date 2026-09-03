"""Tratamento centralizado de erros.

Toda resposta de erro da API — sem exceção — tem este formato:

    {
      "erro": {
        "codigo": "RN-02",
        "mensagem": "Saída de 50 unidades excede o saldo disponível de 12.",
        "campo": "quantidade"
      }
    }

Duas famílias de código convivem no campo `codigo`:

* `RN-xx`  — violação de regra de negócio, sempre 422 (exceto a RN-04, que é
             405 por ser ausência de método, e a RN-09/RN-10, que são 403).
* `HTTP-x` — erro de protocolo: requisição malformada, token ausente,
             recurso inexistente, método não permitido.

Nenhum stack trace chega ao cliente. Exceções inesperadas viram 500 genérico
e o traceback vai para o log do servidor.
"""

import logging

from flask import Flask, jsonify
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError
from werkzeug.exceptions import HTTPException

from app.extensions import api, jwt

logger = logging.getLogger(__name__)

# Código padrão por status HTTP, usado quando o erro não carrega um RN.
CODIGOS_HTTP = {
    400: "HTTP-400",
    401: "HTTP-401",
    403: "HTTP-403",
    404: "HTTP-404",
    405: "HTTP-405",
    422: "HTTP-422",
    500: "HTTP-500",
}

# O Flask e o werkzeug descrevem seus erros em inglês. A API responde em
# português, então a descrição padrão é substituída.
MENSAGENS_HTTP = {
    400: "Requisição malformada.",
    401: "Autenticação necessária.",
    403: "Sem permissão para executar esta operação.",
    404: "Recurso não encontrado.",
    405: "Método não permitido para este recurso.",
    422: "Regra de negócio violada.",
    500: "Erro interno no servidor.",
}


# Mensagem por tipo de falha de token. O nome da classe é usado como chave
# para não importar sete exceções só para comparar.
MENSAGENS_JWT = {
    "NoAuthorizationError": (
        "Token de acesso ausente ou mal formatado. Faça login em "
        "/auth/login e envie o cabeçalho como: Authorization: Bearer <token>."
    ),
    "ExpiredSignatureError": "Token de acesso expirado. Faça login novamente.",
    "RevokedTokenError": "Token de acesso revogado.",
}


def montar_erro(codigo: str, mensagem: str, campo: str | None = None) -> dict:
    """Monta o envelope de erro. Único ponto que conhece o formato."""
    return {"erro": {"codigo": codigo, "mensagem": mensagem, "campo": campo}}


# --------------------------------------------------------------------------
# Exceções do domínio
# --------------------------------------------------------------------------
class ErroAPI(Exception):
    """Base de toda exceção que vira resposta de erro formatada."""

    status_code = 500
    codigo = "HTTP-500"
    mensagem = "Erro interno no servidor."

    def __init__(
        self,
        mensagem: str | None = None,
        *,
        codigo: str | None = None,
        campo: str | None = None,
    ):
        super().__init__(mensagem or self.mensagem)
        self.mensagem = mensagem or self.mensagem
        self.codigo = codigo or self.codigo
        self.campo = campo

    def payload(self) -> dict:
        return montar_erro(self.codigo, self.mensagem, self.campo)


class RequisicaoInvalida(ErroAPI):
    """400 — o corpo ou os parâmetros não formam uma requisição válida."""

    status_code = 400
    codigo = "HTTP-400"
    mensagem = "Requisição malformada."


class NaoAutenticado(ErroAPI):
    """401 — token ausente, inválido ou expirado."""

    status_code = 401
    codigo = "HTTP-401"
    mensagem = "Autenticação necessária."


class SemPermissao(ErroAPI):
    """403 — autenticado, mas sem o papel exigido pela operação."""

    status_code = 403
    codigo = "HTTP-403"
    mensagem = "Sem permissão para executar esta operação."


class NaoEncontrado(ErroAPI):
    """404 — recurso inexistente, ou de outra empresa (RN-08).

    Responder 404 em vez de 403 para recurso de outra empresa é deliberado:
    404 não revela que o registro existe.
    """

    status_code = 404
    codigo = "HTTP-404"
    mensagem = "Recurso não encontrado."


class MetodoNaoPermitido(ErroAPI):
    """405 — o método não existe para este recurso."""

    status_code = 405
    codigo = "HTTP-405"
    mensagem = "Método não permitido para este recurso."


class RegraDeNegocio(ErroAPI):
    """422 — regra de negócio violada. O código da regra é obrigatório."""

    status_code = 422

    def __init__(self, codigo: str, mensagem: str, campo: str | None = None):
        super().__init__(mensagem, codigo=codigo, campo=campo)


# --------------------------------------------------------------------------
# Registro dos tratadores
# --------------------------------------------------------------------------
def _traduzir_erro_de_validacao(campo: str | None, detalhe: str) -> str:
    """Converte a mensagem do jsonschema para português.

    O `validate=True` do flask-restx valida contra JSON Schema, que descreve
    as falhas em inglês. Traduzir aqui mantém a API inteira em um só idioma.
    """
    alvo = f"O campo '{campo}'" if campo else "O corpo da requisição"

    if "is a required property" in detalhe:
        return f"{alvo} é obrigatório."
    if "is not of type" in detalhe:
        tipo = detalhe.rsplit("is not of type", 1)[-1].strip().strip("'\"")
        return f"{alvo} deve ser do tipo {tipo}."
    if "is too short" in detalhe or "is too long" in detalhe:
        return f"{alvo} tem tamanho inválido."
    if "is not one of" in detalhe:
        opcoes = detalhe.rsplit("is not one of", 1)[-1].strip()
        return f"{alvo} deve ser um dos valores: {opcoes}."
    if "is less than the minimum" in detalhe or "is greater than the maximum" in detalhe:
        return f"{alvo} está fora do intervalo permitido."
    return f"{alvo} tem valor inválido: {detalhe}"


def _extrair_de_http(e: HTTPException) -> tuple[str, str, str | None]:
    """Traduz uma HTTPException para (codigo, mensagem, campo).

    Cobre também o 400 gerado pelo `validate=True` do flask-restx, cujos
    detalhes vêm em `e.data["errors"]` no formato {campo: descrição}.
    """
    status = e.code or 500
    codigo = CODIGOS_HTTP.get(status, f"HTTP-{status}")
    mensagem = MENSAGENS_HTTP.get(status) or e.description or "Erro na requisição."
    campo = None

    dados = getattr(e, "data", None) or {}

    # Mensagem vinda de um abort() explícito nosso, que já está em português.
    # A do validador é genérica e é substituída logo abaixo pelo detalhe.
    recebida = dados.get("message")
    if recebida and recebida != "Input payload validation failed":
        mensagem = str(recebida)

    erros = dados.get("errors")
    if isinstance(erros, dict) and erros:
        campo, detalhe = next(iter(erros.items()))
        campo = campo or None
        mensagem = _traduzir_erro_de_validacao(campo, str(detalhe))

    return codigo, mensagem, campo


def registrar_tratadores(app: Flask) -> None:
    """Liga os tratadores de erro na aplicação.

    São dois níveis: os do flask-restx cobrem o que acontece dentro de um
    resource; os do Flask cobrem o que nunca chega lá, como uma URL
    inexistente.
    """

    # --- Nível flask-restx (dentro dos controllers) -------------------------
    # A ordem importa: o flask-restx percorre os tratadores registrados e
    # usa o primeiro cujo isinstance() casar. Do mais específico ao geral.
    @api.errorhandler(ErroAPI)
    def _erro_de_dominio(e: ErroAPI):
        return e.payload(), e.status_code

    @api.errorhandler(JWTExtendedException)
    @api.errorhandler(PyJWTError)
    def _erro_de_token(e: Exception):
        """Traduz falha de token dentro de um resource.

        Os loaders do flask-jwt-extended registrados abaixo só valem para
        exceções que chegam ao Flask. Dentro de um resource, o flask-restx
        captura antes, e sem este tratador a falta de token viraria 500.
        """
        mensagem = MENSAGENS_JWT.get(
            type(e).__name__, "Token de acesso inválido."
        )
        return montar_erro("HTTP-401", mensagem), 401

    @api.errorhandler(HTTPException)
    def _erro_http(e: HTTPException):
        codigo, mensagem, campo = _extrair_de_http(e)
        envelope = montar_erro(codigo, mensagem, campo)
        # O flask-restx, depois de chamar este tratador, faz
        # `data = getattr(e, "data", default_data)` — ou seja, se a exceção
        # carregar `.data`, o retorno daqui é descartado. Todo abort() interno
        # do flask-restx (inclusive o da validação de payload) carrega. Por
        # isso o envelope é escrito também em `e.data`.
        e.data = envelope
        return envelope, e.code or 500

    @api.errorhandler(Exception)
    def _erro_inesperado(e: Exception):
        logger.exception("Erro não tratado: %s", e)
        return montar_erro("HTTP-500", "Erro interno no servidor."), 500

    # --- Nível Flask (fora dos controllers) ---------------------------------
    @app.errorhandler(ErroAPI)
    def _erro_de_dominio_fora(e: ErroAPI):
        return jsonify(e.payload()), e.status_code

    @app.errorhandler(HTTPException)
    def _erro_http_fora(e: HTTPException):
        codigo, mensagem, campo = _extrair_de_http(e)
        return jsonify(montar_erro(codigo, mensagem, campo)), e.code or 500

    @app.errorhandler(Exception)
    def _erro_inesperado_fora(e: Exception):
        logger.exception("Erro não tratado: %s", e)
        return jsonify(montar_erro("HTTP-500", "Erro interno no servidor.")), 500

    _registrar_tratadores_jwt()


def _registrar_tratadores_jwt() -> None:
    """Faz o flask-jwt-extended responder no mesmo envelope de erro.

    Sem isso, ele devolveria o formato próprio dele ({"msg": "..."}), quebrando
    a promessa de formato único da API.
    """

    @jwt.unauthorized_loader
    def _sem_token(motivo: str):
        return jsonify(
            montar_erro("HTTP-401", "Token de acesso ausente. Faça login em /auth/login.")
        ), 401

    @jwt.invalid_token_loader
    def _token_invalido(motivo: str):
        return jsonify(montar_erro("HTTP-401", "Token de acesso inválido.")), 401

    @jwt.expired_token_loader
    def _token_expirado(header: dict, payload: dict):
        return jsonify(
            montar_erro("HTTP-401", "Token de acesso expirado. Faça login novamente.")
        ), 401

    @jwt.revoked_token_loader
    def _token_revogado(header: dict, payload: dict):
        return jsonify(montar_erro("HTTP-401", "Token de acesso revogado.")), 401
