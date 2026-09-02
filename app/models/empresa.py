"""Empresa — raiz do isolamento multi-tenant (RN-08)."""

from app.extensions import db
from app.models.base import agora_utc


class Empresa(db.Model):
    __tablename__ = "empresa"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    plano = db.Column(db.String(20), nullable=False, default="BASICO")
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=agora_utc)

    usuarios = db.relationship("Usuario", back_populates="empresa")
    categorias = db.relationship("Categoria", back_populates="empresa")
    fornecedores = db.relationship("Fornecedor", back_populates="empresa")
    produtos = db.relationship("Produto", back_populates="empresa")

    def __repr__(self) -> str:
        return f"<Empresa {self.id} {self.nome!r}>"
