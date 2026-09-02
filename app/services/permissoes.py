"""Decisões de permissão por papel (RN-09 e RN-10).

A verificação mora aqui, na camada de serviço. O decorator em
`app.security` apenas chama estas funções, para que o resource declare a
exigência sem conter a regra.
"""

from app.errors import SemPermissao
from app.models import RoleUsuario, Usuario


def exigir_admin(usuario: Usuario) -> None:
    """RN-09 — apenas ADMIN cria ou altera usuário, fornecedor e preço de venda."""
    if usuario.role is not RoleUsuario.ADMIN:
        raise SemPermissao(
            "Esta operação exige perfil ADMIN.",
            codigo="RN-09",
        )
