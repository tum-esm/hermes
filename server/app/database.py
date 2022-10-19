import sqlalchemy as sa
import sqlalchemy.dialects.postgresql
import typing
import databases.interfaces

import app.settings as settings

CONFIGURATION = {
    "url": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}


def dictify(result: typing.List[databases.interfaces.Record]) -> typing.List[dict]:
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


def compile(query: sa.sql.elements.ClauseElement) -> str:
    """Compile an SQLAlchemy core schema into a query string."""
    return str(query.compile(dialect=dialect))


########################################################################################
# Table schemas
########################################################################################


metadata = sa.MetaData()
dialect = sa.dialects.postgresql.dialect()


MEASUREMENTS = sa.Table(
    "measurements",
    metadata,
    sa.Column("node", sa.String(length=32)),
    sa.Column("measurement_timestamp", sa.Integer),
    sa.Column("receipt_timestamp", sa.Integer),
    sa.Column("value", sa.Integer),
)
