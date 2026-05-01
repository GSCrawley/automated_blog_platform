"""PR 6.4: add affiliate_url and tracking_id to Product

Revision ID: 65ce81a88136
Revises: 0004
Create Date: 2026-05-01 11:16:41.892598

NOTE: Alembic autogenerate also flagged drops on blueprints/serp_profiles and
index churn on article_revisions/budgets — those were phantom diffs caused by
the BlueprintRow/SerpProfile models not being imported at autogenerate time.
The migration has been hand-trimmed to ONLY add the two new affiliate columns.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65ce81a88136'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('affiliate_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('tracking_id', sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('tracking_id')
        batch_op.drop_column('affiliate_url')
