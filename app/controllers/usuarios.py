"""Endpoints de gestão de usuários da própria empresa."""

from flask import request
from flask_restx import Namespace, Resource

from app.controllers import argumento_booleano, parser_paginacao
from app.schemas.comum import erro
from app.schemas.usuario import usuario_atualizacao, usuario_entrada, usuario_paginado, usuario_saida
from app.security import somente_admin, usuario_atual
from app.services import usuario_service

ns = Namespace("usuarios", description="Gestão de usuários da empresa (RN-09)")

filtros = parser_paginacao()
argumento_booleano(
    filtros, "incluir_inativos", "Inclui na listagem os usuários já desativados"
)


@ns.route("")
class ListaDeUsuarios(Resource):
    @ns.doc("listar_usuarios", security="Bearer")
    @ns.expect(filtros)
    @ns.response(200, "Lista paginada", usuario_paginado)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.marshal_with(usuario_paginado)
    @somente_admin
    def get(self):
        """Lista os usuários da empresa do token."""
        argumentos = filtros.parse_args()
        return usuario_service.listar(
            usuario_atual(),
            pagina=argumentos["pagina"],
            por_pagina=argumentos["por_pagina"],
            incluir_inativos=argumentos["incluir_inativos"],
        )

    @ns.doc("criar_usuario", security="Bearer")
    @ns.expect(usuario_entrada, validate=True)
    @ns.response(201, "Usuário criado", usuario_saida)
    @ns.response(400, "Corpo da requisição inválido", erro)
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(422, "E-mail já cadastrado", erro)
    @ns.marshal_with(usuario_saida, code=201)
    @somente_admin
    def post(self):
        """Cadastra um usuário na empresa do token."""
        return usuario_service.criar(usuario_atual(), request.get_json()), 201


@ns.route("/<int:usuario_id>")
@ns.param("usuario_id", "Identificador do usuário")
class UsuarioDetalhe(Resource):
    @ns.doc("obter_usuario", security="Bearer")
    @ns.response(200, "Usuário encontrado", usuario_saida)
    @ns.response(401, "Token ausente ou inválido", erro)
    @ns.response(404, "Usuário não encontrado nesta empresa", erro)
    @ns.marshal_with(usuario_saida)
    def get(self, usuario_id):
        """Detalha um usuário da empresa do token."""
        return usuario_service.obter(usuario_atual(), usuario_id)

    @ns.doc("atualizar_usuario", security="Bearer")
    @ns.expect(usuario_atualizacao, validate=True)
    @ns.response(200, "Usuário atualizado", usuario_saida)
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(404, "Usuário não encontrado nesta empresa", erro)
    @ns.response(422, "E-mail em uso ou último ADMIN ativo", erro)
    @ns.marshal_with(usuario_saida)
    @somente_admin
    def put(self, usuario_id):
        """Atualiza um usuário. Aceita alteração parcial."""
        return usuario_service.atualizar(
            usuario_atual(), usuario_id, request.get_json()
        )

    @ns.doc("desativar_usuario", security="Bearer")
    @ns.response(204, "Usuário desativado")
    @ns.response(403, "Exige perfil ADMIN", erro)
    @ns.response(404, "Usuário não encontrado nesta empresa", erro)
    @ns.response(422, "Usuário é você mesmo ou é o último ADMIN ativo", erro)
    @somente_admin
    def delete(self, usuario_id):
        """Desativa um usuário.

        Não apaga o registro: a movimentação já feita precisa continuar
        apontando para quem a registrou, pelo mesmo motivo da RN-05.
        """
        usuario_service.desativar(usuario_atual(), usuario_id)
        return "", 204
