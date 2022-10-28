import typing

import databases.interfaces
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

import app.settings as settings
import app.validation as validation


def dictify(result: typing.Sequence[databases.interfaces.Record]) -> typing.List[dict]:
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


def compile(query: sa.sql.elements.ClauseElement) -> str:
    """Compile an SQLAlchemy core schema into a query string."""
    return str(query.compile(dialect=dialect))


CONFIGURATION = {
    "url": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}


########################################################################################
# Table schemas
########################################################################################


metadata = sa.MetaData()
dialect = sa.dialects.postgresql.dialect()


CONFIGURATIONS = sa.Table(
    "configurations",
    metadata,
    sa.Column(
        "node_identifier",
        sa.String(length=validation.Limit.MEDIUM),
        primary_key=True,
    ),
    sa.Column("creation_timestamp", sa.Integer, nullable=False),
    sa.Column("update_timestamp", sa.Integer, nullable=False),
    sa.Column("configuration", sa.JSON, nullable=False),
)

MEASUREMENTS = sa.Table(
    "measurements",
    metadata,
    sa.Column(
        "node_identifier",
        sa.String(length=validation.Limit.MEDIUM),
        sa.ForeignKey(
            CONFIGURATIONS.columns.node_identifier,
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    ),
    sa.Column("measurement_timestamp", sa.Integer, nullable=False),
    sa.Column("receipt_timestamp", sa.Integer, nullable=False),
    sa.Column("value", sa.Integer, nullable=False),
)
