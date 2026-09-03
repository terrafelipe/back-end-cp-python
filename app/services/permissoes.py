"""Decisões de permissão por papel (RN-09 e RN-10).

A verificação mora aqui, na camada de serviço. O decorator em
`app.security` apenas chama estas funções, para que o resource declare a
exigência sem conter a regra.
"""

from app.errors import SemPermissao
from app.models import RoleUsuario, Usuario

MENSAGEM_ADMIN = "Esta operação exige perfil ADMIN."
# RN-10 — o OPERADOR registra movimentação e consulta, mas não exclui produto.
MENSAGEM_EXCLUIR_PRODUTO = "Apenas ADMIN pode excluir produto."


def exigir_admin(
    usuario: Usuario,
    codigo: str = "RN-09",
    mensagem: str = MENSAGEM_ADMIN,
) -> None:
    """Barra quem não é ADMIN.

    O código é parametrizado porque duas regras diferentes desembocam aqui:
    a RN-09 (cadastro de usuário, fornecedor e preço de venda) e a RN-10
    (exclusão de produto). A mensagem de erro precisa apontar a regra certa.
    """
    if usuario.role is not RoleUsuario.ADMIN:
        raise SemPermissao(mensagem, codigo=codigo)
