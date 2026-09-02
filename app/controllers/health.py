"""Endpoint de verificação de disponibilidade da API e do banco."""

from flask_restx import Namespace, Resource, fields
from sqlalchemy import text

from app.extensions import db

ns = Namespace(
    "health",
    description="Verificação de disponibilidade da API e da conexão com o banco",
)

health_model = ns.model(
    "Health",
    {
        "status": fields.String(
            description="Estado geral da aplicação",
            example="ok",
        ),
        "banco": fields.String(
            description="Estado da conexão com o banco de dados",
            example="conectado",
        ),
    },
)


@ns.route("")
class Health(Resource):
    @ns.doc("health_check")
    @ns.response(200, "API e banco respondendo", health_model)
    @ns.response(503, "Banco de dados indisponível")
    @ns.marshal_with(health_model)
    def get(self):
        """Verifica se a API está no ar e se o banco responde.

        Executa um `SELECT 1` no banco configurado em `DATABASE_URL`.
        Útil para confirmar que a instalação local ficou correta.
        """
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            ns.abort(503, "Banco de dados indisponível")

        return {"status": "ok", "banco": "conectado"}
