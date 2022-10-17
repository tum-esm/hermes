import sqlalchemy as sa

import app.settings as settings


def dictify(result):
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


CONFIGURATION = {
    "url": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}


########################################################################################
# Table schemas
########################################################################################


metadata = sa.MetaData()

MEASUREMENTS = sa.Table(
    "measurements",
    metadata,
    sa.Column("node", sa.String(length=32)),
    sa.Column("measurement_timestamp", sa.Integer),
    sa.Column("receipt_timestamp", sa.Integer),
    sa.Column("value", sa.Integer),
)
