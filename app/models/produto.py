"""Produto.

`saldo_atual` é um cache do saldo, desnormalizado por desempenho no CP2:
só `movimentacao_service.registrar` escreve nele, na mesma transação da
movimentação. O saldo de referência continua sendo o derivado do histórico
(`estoque_service.saldos`), e os testes comparam os dois.
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
        # RN-02 repetida no banco: o cache nunca fica negativo.
        db.CheckConstraint("saldo_atual >= 0", name="saldo_atual_nao_negativo"),
        # Toda listagem filtra pela empresa e, por padrão, só os ativos.
        db.Index("ix_produto_empresa_id_ativo", "empresa_id", "ativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # index=True atende a busca por SKU, que o índice composto do UNIQUE
    # também cobre, mas de forma menos direta.
    sku = db.Column(db.String(40), nullable=False, index=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categoria.id"), nullable=False, index=True
    )
    fornecedor_id = db.Column(
        db.Integer, db.ForeignKey("fornecedor.id"), nullable=True, index=True
    )

    preco_custo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    preco_venda = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    unidade = db.Column(db.String(10), nullable=False, default="UN")
    # RN-05 — exclusão de produto com movimentação vira desativação.
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    # Cache do saldo (ver docstring do módulo). server_default para o
    # ALTER TABLE preencher as linhas existentes antes do backfill.
    saldo_atual = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=agora_utc)

    empresa = db.relationship("Empresa", back_populates="produtos")
    categoria = db.relationship("Categoria", back_populates="produtos")
    fornecedor = db.relationship("Fornecedor", back_populates="produtos")
    movimentacoes = db.relationship("Movimentacao", back_populates="produto")

    def __repr__(self) -> str:
        return f"<Produto {self.id} {self.sku!r}>"
