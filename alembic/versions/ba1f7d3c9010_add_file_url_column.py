"""add file url column

Revision ID: ba1f7d3c9010
Revises: ad9c4ec54b4d
Create Date: 2025-02-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba1f7d3c9010'
down_revision: Union[str, Sequence[str], None] = 'ad9c4ec54b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('files', sa.Column('url', sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column('files', 'url')
