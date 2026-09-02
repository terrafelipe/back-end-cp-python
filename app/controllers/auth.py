"""Endpoints de cadastro e autenticação.

O resource só recebe a requisição, chama o serviço e devolve a resposta.
Nenhuma regra é decidida aqui.
"""

from flask import request
from flask_restx import Namespace, Resource

from app.schemas.auth import login_entrada, registro_entrada, token_saida
from app.schemas.comum import erro
from app.schemas.usuario import usuario_saida
from app.security import usuario_atual
from app.services import auth_service

ns = Namespace("auth", description="Cadastro inicial, login e dados do usuário logado")


@ns.route("/register")
class Registro(Resource):
    @ns.doc("registrar")
    @ns.expect(registro_entrada, validate=True)
    @ns.response(201, "Empresa e administrador criados", token_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(422, "E-mail ou CNPJ já cadastrado", erro)
    @ns.marshal_with(token_saida, code=201)
    def post(self):
        """Cadastra uma empresa e seu primeiro usuário.

        O usuário criado aqui é sempre ADMIN — é ele quem cadastra os demais.
        Já devolve o token, então não é preciso fazer login em seguida.
        """
        return auth_service.registrar(request.get_json()), 201


@ns.route("/login")
class Login(Resource):
    @ns.doc("login")
    @ns.expect(login_entrada, validate=True)
    @ns.response(200, "Autenticado", token_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(401, "E-mail ou senha inválidos", erro)
    @ns.marshal_with(token_saida)
    def post(self):
        """Autentica e devolve o token JWT."""
        corpo = request.get_json()
        return auth_service.autenticar(corpo["email"], corpo["senha"])


@ns.route("/me")
class EuMesmo(Resource):
    @ns.doc("usuario_logado", security="Bearer")
    @ns.response(200, "Dados do usuário do token", usuario_saida)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.marshal_with(usuario_saida)
    def get(self):
        """Devolve os dados do usuário dono do token."""
        return usuario_atual()
