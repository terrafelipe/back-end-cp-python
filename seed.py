"""Popula o banco com dados de demonstração.

Uso:
    python seed.py            # cria os dados se ainda não existirem
    python seed.py --recriar  # apaga os dados da empresa demo e recria

As movimentações são registradas pelo próprio serviço, e não por inserção
direta: assim o custo médio (RN-07) sai calculado pela mesma regra que a
API usa, e o seed serve como prova de que ela funciona.
"""

import logging
import sys
from decimal import Decimal

from app import aplicar_migrations, create_app
from app.extensions import db
from app.models import (
    Categoria,
    Empresa,
    Fornecedor,
    Movimentacao,
    Produto,
    RoleUsuario,
    Usuario,
)
from app.security import gerar_hash
from app.services import movimentacao_service

CNPJ_DEMO = "12.345.678/0001-90"

CATEGORIAS = ["Bebidas", "Mercearia", "Limpeza", "Hortifrúti"]

FORNECEDORES = [
    ("Distribuidora Sul", "11.222.333/0001-44", "contato@distsul.com.br", "(11) 3344-5566"),
    ("Atacado Central", "55.666.777/0001-88", "vendas@atacadocentral.com.br", "(11) 2233-4455"),
    ("Fazenda Boa Vista", None, "boavista@fazenda.com.br", "(19) 99887-7665"),
]

# sku, nome, categoria, fornecedor, preço de venda, estoque mínimo, unidade
PRODUTOS = [
    ("BEB-COLA-350", "Refrigerante Cola 350ml", "Bebidas", 0, "5.50", 24, "UN"),
    ("BEB-AGUA-500", "Água Mineral 500ml", "Bebidas", 0, "2.50", 48, "UN"),
    ("BEB-SUCO-1L", "Suco de Laranja 1L", "Bebidas", 1, "9.90", 12, "UN"),
    ("MER-ARROZ-5KG", "Arroz Tipo 1 5kg", "Mercearia", 1, "27.90", 20, "PC"),
    ("MER-FEIJAO-1KG", "Feijão Carioca 1kg", "Mercearia", 1, "8.90", 30, "PC"),
    ("LIM-DETER-500", "Detergente Neutro 500ml", "Limpeza", 0, "3.20", 36, "UN"),
    ("LIM-SABAO-1L", "Sabão Líquido 1L", "Limpeza", 0, "18.50", 12, "UN"),
    ("HOR-BANANA-KG", "Banana Prata", "Hortifrúti", 2, "6.90", 15, "KG"),
]

# sku, tipo, quantidade, custo unitário, motivo
MOVIMENTACOES = [
    ("BEB-COLA-350", "ENTRADA", 120, "3.10", "Compra nota 10021"),
    ("BEB-COLA-350", "ENTRADA", 80, "3.50", "Compra nota 10044"),
    ("BEB-COLA-350", "SAIDA", 95, None, "Venda do dia"),
    ("BEB-AGUA-500", "ENTRADA", 240, "1.10", "Compra nota 10022"),
    ("BEB-AGUA-500", "SAIDA", 210, None, "Venda da semana"),
    ("BEB-SUCO-1L", "ENTRADA", 60, "6.40", "Compra nota 10023"),
    ("BEB-SUCO-1L", "SAIDA", 18, None, "Venda do dia"),
    ("MER-ARROZ-5KG", "ENTRADA", 100, "19.80", "Compra nota 10030"),
    ("MER-ARROZ-5KG", "ENTRADA", 50, "21.40", "Compra nota 10055"),
    ("MER-ARROZ-5KG", "SAIDA", 62, None, "Venda da semana"),
    ("MER-FEIJAO-1KG", "ENTRADA", 90, "5.70", "Compra nota 10031"),
    ("MER-FEIJAO-1KG", "SAIDA", 74, None, "Venda da semana"),
    ("LIM-DETER-500", "ENTRADA", 150, "1.90", "Compra nota 10040"),
    ("LIM-DETER-500", "SAIDA", 40, None, "Venda do dia"),
    ("LIM-SABAO-1L", "ENTRADA", 40, "12.30", "Compra nota 10041"),
    ("LIM-SABAO-1L", "SAIDA", 33, None, "Venda da semana"),
    ("HOR-BANANA-KG", "ENTRADA", 80, "3.80", "Compra da feira"),
    ("HOR-BANANA-KG", "SAIDA", 55, None, "Venda do dia"),
    # Contagem de inventário: o AJUSTE define o saldo pelo que foi contado
    # na prateleira, em vez de somar a ele.
    ("HOR-BANANA-KG", "AJUSTE", 22, None, "Contagem de inventário — perda por maturação"),
]


def _empresa_demo() -> Empresa | None:
    return Empresa.query.filter(Empresa.cnpj == CNPJ_DEMO).first()


def _apagar(empresa: Empresa) -> None:
    """Remove os dados da empresa demo na ordem que a FK exige."""
    produtos = Produto.query.filter(Produto.empresa_id == empresa.id).all()
    if produtos:
        Movimentacao.query.filter(
            Movimentacao.produto_id.in_([p.id for p in produtos])
        ).delete(synchronize_session=False)
    Produto.query.filter(Produto.empresa_id == empresa.id).delete(
        synchronize_session=False
    )
    for modelo in (Categoria, Fornecedor, Usuario):
        modelo.query.filter(modelo.empresa_id == empresa.id).delete(
            synchronize_session=False
        )
    db.session.delete(empresa)
    db.session.commit()


def povoar() -> None:
    empresa = Empresa(nome="Comércio Demonstração", cnpj=CNPJ_DEMO)
    db.session.add(empresa)
    db.session.flush()

    admin = Usuario(
        nome="Administrador Demo",
        email="admin@demo.com",
        senha_hash=gerar_hash("admin123"),
        role=RoleUsuario.ADMIN,
        empresa_id=empresa.id,
    )
    operador = Usuario(
        nome="Operador Demo",
        email="operador@demo.com",
        senha_hash=gerar_hash("operador123"),
        role=RoleUsuario.OPERADOR,
        empresa_id=empresa.id,
    )
    db.session.add_all([admin, operador])

    categorias = {
        nome: Categoria(nome=nome, empresa_id=empresa.id) for nome in CATEGORIAS
    }
    db.session.add_all(categorias.values())

    fornecedores = [
        Fornecedor(
            nome=nome, cnpj=cnpj, email=email, telefone=telefone, empresa_id=empresa.id
        )
        for nome, cnpj, email, telefone in FORNECEDORES
    ]
    db.session.add_all(fornecedores)
    db.session.flush()

    produtos = {}
    for sku, nome, categoria, indice, preco, minimo, unidade in PRODUTOS:
        produto = Produto(
            sku=sku,
            nome=nome,
            categoria_id=categorias[categoria].id,
            fornecedor_id=fornecedores[indice].id,
            preco_venda=Decimal(preco),
            estoque_minimo=minimo,
            unidade=unidade,
            empresa_id=empresa.id,
        )
        produtos[sku] = produto
        db.session.add(produto)
    db.session.commit()

    for sku, tipo, quantidade, custo, motivo in MOVIMENTACOES:
        movimentacao_service.registrar(
            operador,
            {
                "produto_id": produtos[sku].id,
                "tipo": tipo,
                "quantidade": quantidade,
                "custo_unitario": Decimal(custo) if custo else None,
                "motivo": motivo,
            },
        )

    return empresa, produtos


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    recriar = "--recriar" in sys.argv

    app = create_app()
    aplicar_migrations(app)

    with app.app_context():
        existente = _empresa_demo()
        if existente and not recriar:
            print(
                "Os dados de demonstração já existem. "
                "Use 'python seed.py --recriar' para apagar e gerar de novo."
            )
            return 0
        if existente:
            print("Apagando os dados de demonstração anteriores...")
            _apagar(existente)

        empresa, produtos = povoar()

        from app.services import estoque_service

        apurado = estoque_service.saldos([p.id for p in produtos.values()])
        em_ruptura = [
            p for p in produtos.values() if apurado[p.id] < p.estoque_minimo
        ]

        print(f"\nEmpresa: {empresa.nome}")
        print(f"  {len(CATEGORIAS)} categorias, {len(FORNECEDORES)} fornecedores, "
              f"{len(PRODUTOS)} produtos, {len(MOVIMENTACOES)} movimentações")
        print(f"  {len(em_ruptura)} produto(s) abaixo do estoque mínimo:")
        for produto in em_ruptura:
            print(f"    - {produto.sku}: saldo {apurado[produto.id]}, "
                  f"mínimo {produto.estoque_minimo}")
        print("\nUsuários de demonstração:")
        print("  admin@demo.com     / admin123     (ADMIN)")
        print("  operador@demo.com  / operador123  (OPERADOR)")
        print("\nSuba a API com: python app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
