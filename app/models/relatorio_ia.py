"""Relatório de reposição gerado sob demanda (LLM ou regras).

Guardar entrada e resultado permite mostrar o último relatório sem chamar a
LLM de novo e auditar o que foi enviado a ela.
"""

from app.extensions import db
from app.models.base import agora_utc, clausula_in
from app.models.enums import OrigemRelatorio


class RelatorioIA(db.Model):
    __tablename__ = "relatorio_ia"
    __table_args__ = (
        db.CheckConstraint(clausula_in("origem", OrigemRelatorio), name="origem"),
        # "Último relatório" e histórico: sempre por empresa, do mais novo ao mais antigo.
        db.Index("ix_relatorio_ia_empresa_id_criado_em", "empresa_id", "criado_em"),
    )

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    origem = db.Column(
        db.Enum(
            OrigemRelatorio,
            name="origem",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    modelo = db.Column(db.String(80), nullable=True)
    entrada = db.Column(db.JSON, nullable=False)
    resultado = db.Column(db.JSON, nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=agora_utc)

    def __repr__(self) -> str:
        return f"<RelatorioIA {self.id} {self.origem}>"
