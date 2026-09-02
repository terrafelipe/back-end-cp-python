"""Produto.

Não existe coluna `saldo`: o saldo é sempre derivado da soma das
movimentações do item. Ver `services/estoque_service.py`.
"""

from app.extensions import db
from app.models.base import agora_utc


class Produto(db.Model):
    __tablename__ = "produto"
    __table_args__ = (
        # RN-01 — SKU é único por empresa.
        db.UniqueConstraint("sku", "empresa_id"),
        db.CheckConstraint("preco_custo >= 0", name="preco_custo_nao_negativo"),
        db.CheckConstraint("preco_venda >= 0", name="preco_venda_nao_negativo"),
        db.CheckConstraint("estoque_minimo >= 0", name="estoque_minimo_nao_negativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # index=True atende a busca por SKU, que o índice composto do UNIQUE
    # também cobre, mas de forma menos direta.
    sku = db.Column(db.String(40), nullable=False, index=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedor.id"), nullable=True)

    preco_custo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    preco_venda = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    unidade = db.Column(db.String(10), nullable=False, default="UN")
    # RN-05 — exclusão de produto com movimentação vira desativação.
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=agora_utc)

    empresa = db.relationship("Empresa", back_populates="produtos")
    categoria = db.relationship("Categoria", back_populates="produtos")
    fornecedor = db.relationship("Fornecedor", back_populates="produtos")
    movimentacoes = db.relationship("Movimentacao", back_populates="produto")

    def __repr__(self) -> str:
        return f"<Produto {self.id} {self.sku!r}>"
