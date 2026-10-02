"""Fornecedor, escopado por empresa."""

from app.extensions import db


class Fornecedor(db.Model):
    __tablename__ = "fornecedor"
    __table_args__ = (
        # CNPJ é opcional; quando informado, não se repete dentro da empresa.
        # Em SQL, múltiplos NULL não colidem em constraint UNIQUE.
        db.UniqueConstraint("cnpj", "empresa_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(18), nullable=True)
    email = db.Column(db.String(180), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )

    empresa = db.relationship("Empresa", back_populates="fornecedores")
    produtos = db.relationship("Produto", back_populates="fornecedor")

    def __repr__(self) -> str:
        return f"<Fornecedor {self.id} {self.nome!r}>"
