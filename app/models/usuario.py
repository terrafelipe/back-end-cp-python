"""Usuário do sistema, sempre vinculado a uma empresa."""

from app.extensions import db
from app.models.base import agora_utc, clausula_in
from app.models.enums import RoleUsuario


class Usuario(db.Model):
    __tablename__ = "usuario"
    __table_args__ = (
        # Vira `ck_usuario_role` pela convenção de nomes.
        db.CheckConstraint(clausula_in("role", RoleUsuario), name="role"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    # Único globalmente: o login é feito por e-mail, sem informar a empresa.
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        # native_enum=False gera VARCHAR + CHECK em qualquer banco. Evita o
        # tipo ENUM nativo do PostgreSQL, que exigiria ALTER TYPE em migration.
        db.Enum(
            RoleUsuario,
            name="role",
            native_enum=False,
            # A CHECK vem do __table_args__ acima, não daqui.
            create_constraint=False,
            validate_strings=True,
        ),
        nullable=False,
        default=RoleUsuario.OPERADOR,
    )
    # Desativação lógica: um usuário que já registrou movimentação não pode
    # ser removido sem quebrar a trilha de auditoria (mesmo motivo da RN-05).
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id"), nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=agora_utc)

    empresa = db.relationship("Empresa", back_populates="usuarios")
    movimentacoes = db.relationship("Movimentacao", back_populates="usuario")

    def __repr__(self) -> str:
        return f"<Usuario {self.id} {self.email!r} {self.role}>"
