"""Modelos de entrada e saída de produto.

`saldo` e `em_ruptura` aparecem na saída mas não são campos de entrada: vêm
do cache de saldo e da RN-06.
"""

from flask_restx import fields

from app.extensions import api
from app.schemas.comum import DataHoraUTC, modelo_paginado

produto_saida = api.model(
    "Produto",
    {
        "id": fields.Integer(example=1),
        "sku": fields.String(example="BEB-COLA-350"),
        "nome": fields.String(example="Refrigerante Cola 350ml"),
        "descricao": fields.String(example="Lata 350ml, caixa com 12"),
        "categoria_id": fields.Integer(example=1),
        "fornecedor_id": fields.Integer(example=1),
        "preco_custo": fields.Fixed(
            decimals=2, description="Custo médio ponderado, recalculado a cada entrada (RN-07)"
        ),
        "preco_venda": fields.Fixed(decimals=2),
        "estoque_minimo": fields.Integer(example=10),
        "unidade": fields.String(example="UN"),
        "ativo": fields.Boolean(example=True),
        "saldo": fields.Integer(
            description="Saldo atual (cache mantido a cada movimentação; referência: o histórico)"
        ),
        "em_ruptura": fields.Boolean(
            description="Verdadeiro quando o saldo está abaixo do estoque mínimo (RN-06)"
        ),
        "criado_em": DataHoraUTC(),
    },
)

produto_entrada = api.model(
    "ProdutoEntrada",
    {
        "sku": fields.String(
            required=True, min_length=1, max_length=40, example="BEB-TONICA-350"
        ),
        "nome": fields.String(
            required=True, min_length=2, max_length=160, example="Água Tônica 350ml"
        ),
        "descricao": fields.String(example="Lata 350ml, caixa com 12"),
        "categoria_id": fields.Integer(required=True, example=1),
        "fornecedor_id": fields.Integer(example=1),
        "preco_venda": fields.Float(
            min=0, example=6.90, description="Somente ADMIN pode definir (RN-09)"
        ),
        "estoque_minimo": fields.Integer(min=0, default=0, example=12),
        "unidade": fields.String(max_length=10, default="UN", example="UN"),
    },
)

produto_atualizacao = api.model(
    "ProdutoAtualizacao",
    {
        "sku": fields.String(min_length=1, max_length=40, example="BEB-TONICA-350"),
        "nome": fields.String(
            min_length=2, max_length=160, example="Água Tônica 350ml"
        ),
        "descricao": fields.String(example="Lata 350ml, caixa com 12"),
        "categoria_id": fields.Integer(example=1),
        "fornecedor_id": fields.Integer(example=1),
        "preco_venda": fields.Float(min=0, example=6.90),
        "estoque_minimo": fields.Integer(min=0, example=12),
        "unidade": fields.String(max_length=10, example="UN"),
    },
)

produto_paginado = modelo_paginado("ProdutoPaginado", produto_saida)
