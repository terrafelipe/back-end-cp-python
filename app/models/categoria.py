"""Categoria de produto, escopada por empresa."""

from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"
    __table_args__ = (
        # Duas categorias de mesmo nome na mesma empresa seriam indistinguíveis
        # para o operador. Empresas diferentes podem repetir o nome.
        db.UniqueConstraint("nome", "empresa_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )

    empresa = db.relationship("Empresa", back_populates="categorias")
    produtos = db.relationship("Produto", back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Categoria {self.id} {self.nome!r}>"
