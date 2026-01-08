"""Add assignment analytics tables

Revision ID: 7d1c1e4e6c2b
Revises: 25c385ae142c
Create Date: 2025-01-03 10:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d1c1e4e6c2b"
down_revision: Union[str, Sequence[str], None] = "25c385ae142c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "assignments",
        sa.Column("structure_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_concepts_id"), "concepts", ["id"], unique=False)

    op.create_table(
        "assignment_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assignment_questions_id"), "assignment_questions", ["id"], unique=False)

    op.add_column(
        "chat_logs",
        sa.Column("question_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_chat_logs_question_id_assignment_questions",
        "chat_logs",
        "assignment_questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "assignment_concepts",
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("assignment_id", "concept_id"),
    )

    op.create_table(
        "question_concepts",
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["assignment_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id", "concept_id"),
    )

    op.create_table(
        "understanding_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=True),
        sa.Column("concept_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["assignment_questions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_understanding_scores_id"), "understanding_scores", ["id"], unique=False)
    op.create_index(
        "ix_understanding_scores_student_assignment",
        "understanding_scores",
        ["student_id", "assignment_id"],
        unique=False,
    )

    op.alter_column("assignments", "structure_approved", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_understanding_scores_student_assignment", table_name="understanding_scores")
    op.drop_index(op.f("ix_understanding_scores_id"), table_name="understanding_scores")
    op.drop_table("understanding_scores")
    op.drop_table("question_concepts")
    op.drop_table("assignment_concepts")
    op.drop_index(op.f("ix_assignment_questions_id"), table_name="assignment_questions")
    op.drop_table("assignment_questions")
    op.drop_index(op.f("ix_concepts_id"), table_name="concepts")
    op.drop_table("concepts")
    op.drop_constraint(
        "fk_chat_logs_question_id_assignment_questions", "chat_logs", type_="foreignkey"
    )
    op.drop_column("chat_logs", "question_id")
    op.drop_column("assignments", "structure_approved")
