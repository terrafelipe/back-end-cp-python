"""Movimentação de estoque — registro imutável (RN-04).

Não tem `empresa_id`: a empresa é alcançada por `produto.empresa_id`, e o
isolamento da RN-08 é aplicado por join. Duplicar a coluna aqui abriria a
possibilidade de uma movimentação apontar para empresa diferente da do produto.
"""

from app.extensions import db
from app.models.base import agora_utc, clausula_in
from app.models.enums import TipoMovimentacao


class Movimentacao(db.Model):
    __tablename__ = "movimentacao"
    __table_args__ = (
        # RN-03 — a quantidade é sempre positiva; o sentido vem de `tipo`.
        db.CheckConstraint("quantidade > 0", name="quantidade_positiva"),
        # Vira `ck_movimentacao_tipo` pela convenção de nomes.
        db.CheckConstraint(clausula_in("tipo", TipoMovimentacao), name="tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer, db.ForeignKey("produto.id"), nullable=False, index=True
    )
    tipo = db.Column(
        db.Enum(
            TipoMovimentacao,
            name="tipo",
            native_enum=False,
            # A CHECK vem do __table_args__ acima, não daqui.
            create_constraint=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    quantidade = db.Column(db.Integer, nullable=False)
    # Só faz sentido em ENTRADA; é o insumo da RN-07 (custo médio ponderado).
    custo_unitario = db.Column(db.Numeric(12, 2), nullable=True)
    motivo = db.Column(db.String(255), nullable=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True
    )
    # Indexado porque o extrato filtra por período (`de` / `ate`).
    criado_em = db.Column(
        db.DateTime(timezone=True), nullable=False, default=agora_utc, index=True
    )

    produto = db.relationship("Produto", back_populates="movimentacoes")
    usuario = db.relationship("Usuario", back_populates="movimentacoes")

    def __repr__(self) -> str:
        return f"<Movimentacao {self.id} {self.tipo} {self.quantidade}>"
