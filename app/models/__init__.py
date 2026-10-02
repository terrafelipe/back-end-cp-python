"""Modelos SQLAlchemy do domínio.

Todos são importados aqui para que fiquem registrados no metadata antes do
Alembic rodar o autogenerate — sem isso, a migration sai vazia.
"""

from app.models.categoria import Categoria
from app.models.empresa import Empresa
from app.models.enums import OrigemRelatorio, RoleUsuario, TipoMovimentacao
from app.models.fornecedor import Fornecedor
from app.models.movimentacao import Movimentacao
from app.models.produto import Produto
from app.models.relatorio_ia import RelatorioIA
from app.models.usuario import Usuario

__all__ = [
    "Categoria",
    "Empresa",
    "Fornecedor",
    "Movimentacao",
    "OrigemRelatorio",
    "Produto",
    "RelatorioIA",
    "RoleUsuario",
    "TipoMovimentacao",
    "Usuario",
]
