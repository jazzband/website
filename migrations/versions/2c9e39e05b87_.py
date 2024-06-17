"""

Revision ID: 2c9e39e05b87
Revises: 1083bb6545c9
Create Date: 2017-10-30 20:22:24.721562
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2c9e39e05b87"
down_revision = "1083bb6545c9"


def upgrade():
    op.execute(
        """ CREATE OR REPLACE FUNCTION normalize_pep426_name(text)
            RETURNS text AS
            $$
                SELECT lower(regexp_replace($1, '(\.|_|-)+', '-', 'ig'))
            $$
            LANGUAGE SQL
            IMMUTABLE
            RETURNS NULL ON NULL INPUT;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX project_name_pep426_normalized
            ON projects
            (normalize_pep426_name(name))
    """
    )


def downgrade():
    op.execute("DROP INDEX project_name_pep426_normalized")
    op.execute("DROP FUNCTION normalize_pep426_name(text)")
