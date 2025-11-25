"""add file metadata columns

Revision ID: ad9c4ec54b4d
Revises: 4c72891dfda0
Create Date: 2025-02-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad9c4ec54b4d'
down_revision: Union[str, Sequence[str], None] = '4c72891dfda0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('files', sa.Column('mime_type', sa.String(length=255), nullable=True))
    op.add_column('files', sa.Column('size', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('files', 'size', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('files', 'size')
    op.drop_column('files', 'mime_type')
