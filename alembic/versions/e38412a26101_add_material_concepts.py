"""add material concepts

Revision ID: e38412a26101
Revises: e1d387cae82d
Create Date: 2026-01-09 18:47:02.870949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e38412a26101'
down_revision: Union[str, Sequence[str], None] = 'e1d387cae82d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'material_concepts',
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('material_id', 'concept_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('material_concepts')
