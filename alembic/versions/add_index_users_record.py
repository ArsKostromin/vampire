"""
add index on users.record
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'addindexusersrecord'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_index('idx_users_record', 'users', ['record'])

def downgrade():
    op.drop_index('idx_users_record', table_name='users') 