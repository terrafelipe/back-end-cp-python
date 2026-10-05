"""Popula o banco com dados de demonstração.

Uso:
    python seed.py            # cria os dados se ainda não existirem
    python seed.py --recriar  # apaga os dados da empresa demo e recria

As movimentações são registradas pelo próprio serviço, e não por inserção
direta: assim o custo médio (RN-07) sai calculado pela mesma regra que a
API usa, e o seed serve como prova de que ela funciona.

Gera 60 dias de histórico com datas passadas (compras semanais, vendas
diárias), sempre igual, terminando com três produtos em ruptura.
"""

import logging
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from app import aplicar_migrations, create_app
from app.extensions import db
from app.models import (
    Categoria,
    Empresa,
    Fornecedor,
    Movimentacao,
    Produto,
    RelatorioIA,
    RoleUsuario,
    Usuario,
)
from app.models.base import agora_utc
from app.security import gerar_hash
from app.services import movimentacao_service

CNPJ_DEMO = "12.345.678/0001-95"
EMAIL_ADMIN_DEMO = "admin@demo.com"

CATEGORIAS = ["Bebidas", "Mercearia", "Limpeza", "Hortifrúti"]

FORNECEDORES = [
    ("Distribuidora Sul", "11.222.333/0001-81", "contato@distsul.com.br", "(11) 3344-5566"),
    ("Atacado Central", "55.666.777/0001-81", "vendas@atacadocentral.com.br", "(11) 2233-4455"),
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

DIAS_DE_HISTORICO = 60
# Ficam sem compra nas últimas semanas e terminam abaixo do mínimo (RN-06).
SEM_REPOSICAO_NO_FIM = {"BEB-AGUA-500", "MER-FEIJAO-1KG", "LIM-SABAO-1L"}
ULTIMA_COMPRA_DOS_SEM_REPOSICAO = 49  # dia do histórico; 0 = o mais antigo

# sku: (compra semanal, venda média por dia, custo unitário da primeira compra)
PERFIS = {
    "BEB-COLA-350": (90, 11, "3.10"),
    "BEB-AGUA-500": (150, 20, "1.10"),
    "BEB-SUCO-1L": (25, 3, "6.40"),
    "MER-ARROZ-5KG": (38, 5, "19.80"),
    "MER-FEIJAO-1KG": (55, 7, "5.70"),
    "LIM-DETER-500": (40, 5, "1.90"),
    "LIM-SABAO-1L": (18, 2, "12.30"),
    "HOR-BANANA-KG": (45, 6, "3.80"),
}


def plano_de_movimentacoes(agora: datetime) -> list[dict]:
    """Histórico determinístico: compra semanal e venda diária por produto.

    Mesma semente sempre, para o seed dar os mesmos números (e os 3 produtos
    em ruptura que o roteiro do README espera). As datas são relativas a
    `agora`, então o dashboard sempre tem dados recentes.
    """
    sorteio = random.Random(2026)
    saldo = {sku: 0 for sku in PERFIS}
    plano = []
    for dia in range(DIAS_DE_HISTORICO + 1):
        base = agora - timedelta(days=DIAS_DE_HISTORICO - dia)
        for sku, *_ in PRODUTOS:
            compra, venda, custo = PERFIS[sku]
            repoe = sku not in SEM_REPOSICAO_NO_FIM or dia <= ULTIMA_COMPRA_DOS_SEM_REPOSICAO
            if dia % 7 == 0 and repoe:
                saldo[sku] += compra
                # O custo sobe 1% por semana: mostra o custo médio (RN-07) mudando.
                custo_da_semana = (
                    Decimal(custo) * (1 + Decimal(dia // 7) / 100)
                ).quantize(Decimal("0.01"))
                plano.append({
                    "sku": sku, "tipo": "ENTRADA", "quantidade": compra,
                    "custo_unitario": custo_da_semana,
                    "motivo": f"Compra semanal {dia // 7 + 1}",
                    "criado_em": base - timedelta(hours=10),
                })
            # O sorteio acontece mesmo sem saldo: mantém a sequência estável.
            quantidade = min(sorteio.randint(max(1, venda - 2), venda + 2), saldo[sku])
            if quantidade > 0:
                saldo[sku] -= quantidade
                plano.append({
                    "sku": sku, "tipo": "SAIDA", "quantidade": quantidade,
                    "custo_unitario": None, "motivo": "Vendas do dia",
                    "criado_em": base - timedelta(hours=2),
                })

    # Contagem de inventário: o AJUSTE define o saldo pelo que foi contado.
    plano.append({
        "sku": "HOR-BANANA-KG", "tipo": "AJUSTE",
        "quantidade": saldo["HOR-BANANA-KG"] - 4, "custo_unitario": None,
        "motivo": "Contagem de inventário — perda por maturação",
        "criado_em": agora - timedelta(hours=1),
    })
    return plano


def _empresa_demo() -> Empresa | None:
    """Acha a demo pelo admin: o CNPJ da demo mudou no CP2 (o antigo tinha DV inválido)."""
    admin = Usuario.query.filter(Usuario.email == EMAIL_ADMIN_DEMO).first()
    return admin.empresa if admin else None


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
    RelatorioIA.query.filter(RelatorioIA.empresa_id == empresa.id).delete(
        synchronize_session=False
    )
    for modelo in (Categoria, Fornecedor, Usuario):
        modelo.query.filter(modelo.empresa_id == empresa.id).delete(
            synchronize_session=False
        )
    db.session.delete(empresa)
    db.session.commit()


def povoar() -> tuple[Empresa, dict[str, Produto]]:
    empresa = Empresa(nome="Comércio Demonstração", cnpj=CNPJ_DEMO)
    db.session.add(empresa)
    db.session.flush()

    admin = Usuario(
        nome="Administrador Demo",
        email=EMAIL_ADMIN_DEMO,
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

    for passo in plano_de_movimentacoes(agora_utc()):
        autor = operador if passo["tipo"] == "SAIDA" else admin
        movimentacao = movimentacao_service.registrar(autor, {
            "produto_id": produtos[passo["sku"]].id,
            "tipo": passo["tipo"],
            "quantidade": passo["quantidade"],
            "custo_unitario": passo["custo_unitario"],
            "motivo": passo["motivo"],
        })
        # A API sempre grava "agora"; só o seed recua a data, para haver histórico.
        movimentacao.criado_em = passo["criado_em"]
    db.session.commit()

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

        em_ruptura = [p for p in produtos.values() if p.saldo_atual < p.estoque_minimo]
        total_movimentacoes = (
            Movimentacao.query.join(Produto)
            .filter(Produto.empresa_id == empresa.id)
            .count()
        )

        print(f"\nEmpresa: {empresa.nome}")
        print(f"  {len(CATEGORIAS)} categorias, {len(FORNECEDORES)} fornecedores, "
              f"{len(PRODUTOS)} produtos, {total_movimentacoes} movimentações "
              f"em {DIAS_DE_HISTORICO} dias")
        print(f"  {len(em_ruptura)} produto(s) abaixo do estoque mínimo:")
        for produto in em_ruptura:
            print(f"    - {produto.sku}: saldo {produto.saldo_atual}, "
                  f"mínimo {produto.estoque_minimo}")
        print("\nUsuários de demonstração:")
        print("  admin@demo.com     / admin123     (ADMIN)")
        print("  operador@demo.com  / operador123  (OPERADOR)")
        print("\nSuba a API com: python app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
