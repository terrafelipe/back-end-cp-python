"""Cadastro inicial e autenticação.

`/auth/register` é o único caminho que cria empresa: o sistema não tem
cadastro de empresa separado, porque uma empresa sem nenhum administrador
seria inacessível.
"""

from flask_jwt_extended import create_access_token

from app.errors import NaoAutenticado, RegraDeNegocio
from app.extensions import db
from app.models import Empresa, RoleUsuario, Usuario
from app.security import gerar_hash, senha_confere


def _email_ja_usado(email: str, ignorar_id: int | None = None) -> bool:
    consulta = Usuario.query.filter(Usuario.email == email)
    if ignorar_id is not None:
        consulta = consulta.filter(Usuario.id != ignorar_id)
    return db.session.query(consulta.exists()).scalar()


def registrar(dados: dict) -> dict:
    """Cria a empresa e seu primeiro usuário, sempre ADMIN."""
    email = dados["email"].strip().lower()
    if _email_ja_usado(email):
        raise RegraDeNegocio(
            "HTTP-422", "Já existe um usuário com este e-mail.", campo="email"
        )

    cnpj = dados["cnpj"].strip()
    if db.session.query(Empresa.query.filter(Empresa.cnpj == cnpj).exists()).scalar():
        raise RegraDeNegocio(
            "HTTP-422", "Já existe uma empresa com este CNPJ.", campo="cnpj"
        )

    empresa = Empresa(nome=dados["empresa"].strip(), cnpj=cnpj)
    db.session.add(empresa)
    # Necessário para que `empresa.id` exista antes de vincular o usuário.
    db.session.flush()

    usuario = Usuario(
        nome=dados["nome"].strip(),
        email=email,
        senha_hash=gerar_hash(dados["senha"]),
        # O primeiro usuário é sempre ADMIN: alguém precisa poder cadastrar
        # os demais.
        role=RoleUsuario.ADMIN,
        empresa_id=empresa.id,
    )
    db.session.add(usuario)
    db.session.commit()

    return {"access_token": _token(usuario), "usuario": usuario}


def autenticar(email: str, senha: str) -> dict:
    """Valida as credenciais e devolve o token."""
    usuario = Usuario.query.filter(Usuario.email == email.strip().lower()).first()

    # Mensagem única para e-mail inexistente e senha errada: dizer qual dos
    # dois falhou permitiria descobrir quem tem conta no sistema.
    if usuario is None or not senha_confere(senha, usuario.senha_hash):
        raise NaoAutenticado("E-mail ou senha inválidos.")
    if not usuario.ativo:
        raise NaoAutenticado("Este usuário está inativo.")

    return {"access_token": _token(usuario), "usuario": usuario}


def _token(usuario: Usuario) -> str:
    # O `sub` do JWT precisa ser string. A empresa e o papel vão junto só
    # para leitura humana do token; quem manda é o que está no banco.
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "empresa_id": usuario.empresa_id,
            "role": usuario.role.value,
        },
    )
