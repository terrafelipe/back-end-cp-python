"""Gestão de usuários da própria empresa.

Todas as funções recebem o usuário autenticado e restringem a consulta a
`usuario_logado.empresa_id`: a empresa nunca vem do cliente (RN-08).
"""

from app.errors import NaoEncontrado, RegraDeNegocio
from app.extensions import db
from app.models import RoleUsuario, Usuario
from app.security import gerar_hash
from app.services.auth_service import _email_ja_usado
from app.services.paginacao import paginar
from app.services.permissoes import exigir_admin


def _da_empresa(usuario_logado: Usuario):
    return Usuario.query.filter(Usuario.empresa_id == usuario_logado.empresa_id)


def _buscar(usuario_logado: Usuario, usuario_id: int) -> Usuario:
    """Busca dentro da empresa do solicitante.

    Registro de outra empresa responde 404, não 403: um 403 confirmaria que
    aquele id existe.
    """
    usuario = _da_empresa(usuario_logado).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise NaoEncontrado("Usuário não encontrado.")
    return usuario


def _admins_ativos(usuario_logado: Usuario, ignorar_id: int | None = None) -> int:
    consulta = _da_empresa(usuario_logado).filter(
        Usuario.role == RoleUsuario.ADMIN, Usuario.ativo.is_(True)
    )
    if ignorar_id is not None:
        consulta = consulta.filter(Usuario.id != ignorar_id)
    return consulta.count()


def _exigir_outro_admin(usuario_logado: Usuario, alvo: Usuario) -> None:
    """A empresa precisa manter ao menos um ADMIN ativo."""
    if alvo.role is not RoleUsuario.ADMIN or not alvo.ativo:
        return
    if _admins_ativos(usuario_logado, ignorar_id=alvo.id) == 0:
        raise RegraDeNegocio(
            "HTTP-422",
            "A empresa precisa manter ao menos um administrador ativo.",
            campo="role",
        )


def listar(
    usuario_logado: Usuario,
    pagina: int,
    por_pagina: int,
    incluir_inativos: bool = False,
) -> dict:
    exigir_admin(usuario_logado)
    consulta = _da_empresa(usuario_logado)
    if not incluir_inativos:
        consulta = consulta.filter(Usuario.ativo.is_(True))
    return paginar(consulta.order_by(Usuario.nome), pagina, por_pagina)


def obter(usuario_logado: Usuario, usuario_id: int) -> Usuario:
    return _buscar(usuario_logado, usuario_id)


def criar(usuario_logado: Usuario, dados: dict) -> Usuario:
    exigir_admin(usuario_logado)

    email = dados["email"].strip().lower()
    if _email_ja_usado(email):
        raise RegraDeNegocio(
            "HTTP-422", "Já existe um usuário com este e-mail.", campo="email"
        )

    usuario = Usuario(
        nome=dados["nome"].strip(),
        email=email,
        senha_hash=gerar_hash(dados["senha"]),
        role=RoleUsuario(dados["role"]),
        # A empresa vem do token, nunca do corpo da requisição (RN-08).
        empresa_id=usuario_logado.empresa_id,
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def atualizar(usuario_logado: Usuario, usuario_id: int, dados: dict) -> Usuario:
    exigir_admin(usuario_logado)
    usuario = _buscar(usuario_logado, usuario_id)

    if "email" in dados:
        email = dados["email"].strip().lower()
        if _email_ja_usado(email, ignorar_id=usuario.id):
            raise RegraDeNegocio(
                "HTTP-422", "Já existe um usuário com este e-mail.", campo="email"
            )
        usuario.email = email

    if "nome" in dados:
        usuario.nome = dados["nome"].strip()
    if "senha" in dados:
        usuario.senha_hash = gerar_hash(dados["senha"])

    if "role" in dados and RoleUsuario(dados["role"]) is not usuario.role:
        # Rebaixar o último ADMIN deixaria a empresa sem quem administre.
        _exigir_outro_admin(usuario_logado, usuario)
        usuario.role = RoleUsuario(dados["role"])

    db.session.commit()
    return usuario


def desativar(usuario_logado: Usuario, usuario_id: int) -> None:
    """Desativa o usuário. Não apaga: a movimentação precisa manter o autor."""
    exigir_admin(usuario_logado)
    usuario = _buscar(usuario_logado, usuario_id)

    if usuario.id == usuario_logado.id:
        raise RegraDeNegocio(
            "HTTP-422",
            "Um usuário não pode excluir a si mesmo.",
            campo="id",
        )

    _exigir_outro_admin(usuario_logado, usuario)

    usuario.ativo = False
    db.session.commit()
