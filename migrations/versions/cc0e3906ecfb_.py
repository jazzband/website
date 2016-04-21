"""
Revision ID: cc0e3906ecfb
Revises: None
Create Date: 2016-04-15 22:29:04.751309
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cc0e3906ecfb'
down_revision = None


def upgrade():
    op.create_table('projects',
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_url', sa.String(length=255), nullable=True),
        sa.Column('subscribers_count', sa.SmallInteger(), nullable=False),
        sa.Column('stargazers_count', sa.SmallInteger(), nullable=False),
        sa.Column('forks_count', sa.SmallInteger(), nullable=False),
        sa.Column('open_issues_count', sa.SmallInteger(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('pushed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_projects_is_active'), 'projects', ['is_active'], unique=False)
    op.create_index(
        op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_table('users',
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('login', sa.String(length=39), nullable=False),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('html_url', sa.String(length=255), nullable=True),
        sa.Column('is_member', sa.Boolean(), nullable=False),
        sa.Column('is_roadie', sa.Boolean(), nullable=False),
        sa.Column('is_banned', sa.Boolean(), nullable=False),
        sa.Column('access_token', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_users_is_banned'), 'users', ['is_banned'], unique=False)
    op.create_index(
        op.f('ix_users_is_member'), 'users', ['is_member'], unique=False)
    op.create_index(
        op.f('ix_users_is_roadie'), 'users', ['is_roadie'], unique=False)
    op.create_index(
        op.f('ix_users_login'), 'users', ['login'], unique=True)
    op.create_index(
        'member_not_banned', 'users', ['is_member', 'is_banned'], unique=False)

    op.create_table('email_addresses',
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('primary', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_email_addresses_primary'), 'email_addresses', ['primary'],
        unique=False,
    )
    op.create_index(
        op.f('ix_email_addresses_verified'), 'email_addresses', ['verified'],
        unique=False,
    )
    op.create_index('verified', 'email_addresses', ['primary'], unique=False)


def downgrade():
    op.drop_index('verified', table_name='email_addresses')
    op.drop_index(
        op.f('ix_email_addresses_verified'),
        table_name='email_addresses',
    )
    op.drop_index(
        op.f('ix_email_addresses_primary'),
        table_name='email_addresses',
    )
    op.drop_table('email_addresses')
    op.drop_index('member_not_banned', table_name='users')
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_index(op.f('ix_users_is_roadie'), table_name='users')
    op.drop_index(op.f('ix_users_is_member'), table_name='users')
    op.drop_index(op.f('ix_users_is_banned'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_index(op.f('ix_projects_is_active'), table_name='projects')
    op.drop_table('projects')
