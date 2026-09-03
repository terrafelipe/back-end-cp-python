"""Hash de senha, identificação do usuário do token e controle de papel."""

from functools import wraps

import bcrypt
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.errors import NaoAutenticado
from app.extensions import db
from app.models import Usuario
from app.services.permissoes import MENSAGEM_ADMIN, exigir_admin


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def senha_confere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def usuario_atual() -> Usuario:
    """Usuário dono do token, lido do banco a cada requisição.

    Consultar o banco em vez de confiar nas claims faz a desativação do
    usuário e a troca de papel valerem na hora, sem esperar o token expirar.

    A verificação do token acontece aqui dentro: assim a proteção não depende
    da ordem em que os decorators foram empilhados no resource.
    """
    verify_jwt_in_request()
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado("O usuário deste token não está mais ativo.")
    return usuario


def somente_admin(metodo=None, *, codigo="RN-09", mensagem=MENSAGEM_ADMIN):
    """Exige perfil ADMIN no resource. A regra em si está em `permissoes`.

    Aceita as duas formas de uso: `@somente_admin` para o caso comum da
    RN-09, e `@somente_admin(codigo="RN-10", ...)` quando outra regra
    desemboca na mesma exigência. Sem isso o decorator responderia sempre
    RN-09, inclusive na exclusão de produto, que é RN-10.
    """

    def decorador(funcao):
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            exigir_admin(usuario_atual(), codigo=codigo, mensagem=mensagem)
            return funcao(*args, **kwargs)

        return wrapper

    return decorador(metodo) if metodo is not None else decorador
