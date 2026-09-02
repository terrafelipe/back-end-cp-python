"""Hash de senha, identificação do usuário do token e controle de papel."""

from functools import wraps

import bcrypt
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.errors import NaoAutenticado
from app.extensions import db
from app.models import Usuario
from app.services.permissoes import exigir_admin


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


def somente_admin(metodo):
    """Exige perfil ADMIN no resource (RN-09). A regra está em `permissoes`."""

    @wraps(metodo)
    def wrapper(*args, **kwargs):
        exigir_admin(usuario_atual())
        return metodo(*args, **kwargs)

    return wrapper
