import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Produto
from app.services import estoque_service
from tests.ajudantes import criar_produto, movimentar


def _cache_e_derivado(produto_id: int) -> tuple[int, int]:
    db.session.expire_all()
    return db.session.get(Produto, produto_id).saldo_atual, estoque_service.saldo(produto_id)


def test_cache_de_saldo_acompanha_o_historico(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    passos = [("ENTRADA", 10, 10), ("SAIDA", 3, 7), ("AJUSTE", 20, 20),
              ("SAIDA", 20, 0), ("ENTRADA", 5, 5)]
    for tipo, quantidade, esperado in passos:
        assert movimentar(cliente, h_admin, produto["id"], tipo, quantidade).status_code == 201
        assert _cache_e_derivado(produto["id"]) == (esperado, esperado)


def test_saida_recusada_nao_altera_o_cache(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id)
    movimentar(cliente, h_admin, produto["id"], "ENTRADA", 5)
    assert movimentar(cliente, h_admin, produto["id"], "SAIDA", 6).status_code == 422
    assert _cache_e_derivado(produto["id"]) == (5, 5)


def test_cliente_nao_define_o_saldo_ao_criar(cliente, dados, h_admin):
    produto = criar_produto(cliente, h_admin, dados.categoria.id, saldo_atual=99, saldo=99)
    assert produto["saldo"] == 0


def test_banco_recusa_saldo_negativo(dados):
    db.session.add(Produto(sku="NEG", nome="Negativo", categoria_id=dados.categoria.id,
                           empresa_id=dados.empresa.id, saldo_atual=-1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
