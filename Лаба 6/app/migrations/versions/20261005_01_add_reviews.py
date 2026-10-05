"""Add course reviews.

Revision ID: 20261005_01
Revises:
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = '20261005_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_reviews_course_id_courses'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_reviews_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_reviews'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_reviews_course_user'),
    )


def downgrade():
    op.drop_table('reviews')
