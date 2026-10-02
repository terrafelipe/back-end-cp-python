"""cp2: saldo_atual em produto, indices de FK e tabela relatorio_ia

Revision ID: 2c9f4e1a7b3d
Revises: 1abc8de16adf
Create Date: 2026-09-25 12:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '2c9f4e1a7b3d'
down_revision = '1abc8de16adf'
branch_labels = None
depends_on = None


def _saldos_do_historico(conexao) -> dict[int, int]:
    """Mesmo cálculo de `estoque_service.saldos`, copiado de propósito:
    migration não importa código da aplicação, que muda depois dela."""
    saldos: dict[int, int] = {}
    linhas = conexao.execute(
        sa.text("SELECT produto_id, tipo, quantidade FROM movimentacao ORDER BY id")
    )
    for produto_id, tipo, quantidade in linhas:
        if tipo == "AJUSTE":
            saldos[produto_id] = quantidade
        elif tipo == "ENTRADA":
            saldos[produto_id] = saldos.get(produto_id, 0) + quantidade
        else:
            saldos[produto_id] = saldos.get(produto_id, 0) - quantidade
    return saldos


def upgrade():
    with op.batch_alter_table('produto', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('saldo_atual', sa.Integer(), nullable=False, server_default='0')
        )
        batch_op.create_check_constraint(
            op.f('ck_produto_saldo_atual_nao_negativo'), 'saldo_atual >= 0'
        )
        batch_op.create_index('ix_produto_empresa_id_ativo', ['empresa_id', 'ativo'], unique=False)
        batch_op.create_index(op.f('ix_produto_categoria_id'), ['categoria_id'], unique=False)
        batch_op.create_index(op.f('ix_produto_fornecedor_id'), ['fornecedor_id'], unique=False)

    conexao = op.get_bind()
    for produto_id, saldo in _saldos_do_historico(conexao).items():
        conexao.execute(
            sa.text("UPDATE produto SET saldo_atual = :saldo WHERE id = :id"),
            {"saldo": saldo, "id": produto_id},
        )

    op.create_index(op.f('ix_categoria_empresa_id'), 'categoria', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_fornecedor_empresa_id'), 'fornecedor', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_usuario_empresa_id'), 'usuario', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_movimentacao_usuario_id'), 'movimentacao', ['usuario_id'], unique=False)

    op.create_table('relatorio_ia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('origem', sa.Enum('LLM', 'REGRAS', name='origem', native_enum=False), nullable=False),
    sa.Column('modelo', sa.String(length=80), nullable=True),
    sa.Column('entrada', sa.JSON(), nullable=False),
    sa.Column('resultado', sa.JSON(), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("origem IN ('LLM', 'REGRAS')", name=op.f('ck_relatorio_ia_origem')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_relatorio_ia_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_relatorio_ia_usuario_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_relatorio_ia'))
    )
    op.create_index('ix_relatorio_ia_empresa_id_criado_em', 'relatorio_ia', ['empresa_id', 'criado_em'], unique=False)


def downgrade():
    op.drop_index('ix_relatorio_ia_empresa_id_criado_em', table_name='relatorio_ia')
    op.drop_table('relatorio_ia')
    op.drop_index(op.f('ix_movimentacao_usuario_id'), table_name='movimentacao')
    op.drop_index(op.f('ix_usuario_empresa_id'), table_name='usuario')
    op.drop_index(op.f('ix_fornecedor_empresa_id'), table_name='fornecedor')
    op.drop_index(op.f('ix_categoria_empresa_id'), table_name='categoria')
    with op.batch_alter_table('produto', schema=None) as batch_op:
        batch_op.drop_index(op.f('ix_produto_fornecedor_id'))
        batch_op.drop_index(op.f('ix_produto_categoria_id'))
        batch_op.drop_index('ix_produto_empresa_id_ativo')
        batch_op.drop_constraint(op.f('ck_produto_saldo_atual_nao_negativo'), type_='check')
        batch_op.drop_column('saldo_atual')
