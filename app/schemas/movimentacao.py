"""Modelos de entrada e saída de movimentação.

Não existe modelo de atualização: a movimentação é imutável (RN-04).
"""

from flask_restx import fields

from app.extensions import api
from app.models import TipoMovimentacao
from app.schemas.comum import DataHoraUTC, ValorDeEnum, modelo_paginado

TIPOS = [tipo.value for tipo in TipoMovimentacao]

movimentacao_saida = api.model(
    "Movimentacao",
    {
        "id": fields.Integer(example=1),
        "produto_id": fields.Integer(example=1),
        "tipo": ValorDeEnum(enum=TIPOS, example="ENTRADA"),
        "quantidade": fields.Integer(example=50),
        "custo_unitario": fields.Fixed(decimals=2),
        "motivo": fields.String(example="Compra da nota 1234"),
        "usuario_id": fields.Integer(example=1),
        "criado_em": DataHoraUTC(),
    },
)

movimentacao_entrada = api.model(
    "MovimentacaoEntrada",
    {
        "produto_id": fields.Integer(required=True, example=1),
        "tipo": fields.String(
            required=True,
            enum=TIPOS,
            description=(
                "ENTRADA soma ao saldo e recalcula o custo médio (RN-07). "
                "SAIDA subtrai e não pode deixar o saldo negativo (RN-02). "
                "AJUSTE define o saldo pelo valor contado na prateleira."
            ),
        ),
        "quantidade": fields.Integer(
            required=True,
            min=1,
            example=50,
            description="Sempre positiva; o sentido vem do tipo (RN-03)",
        ),
        "custo_unitario": fields.Float(
            min=0, example=3.20, description="Usado apenas em ENTRADA"
        ),
        "motivo": fields.String(max_length=255, example="Compra da nota 1234"),
    },
)

movimentacao_paginada = modelo_paginado("MovimentacaoPaginada", movimentacao_saida)
