import typing

import databases.interfaces
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

import app.constants as constants
import app.settings as settings


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
        "sensor_identifier",
        sa.String(length=constants.Limit.MEDIUM),
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
        "sensor_identifier",
        sa.String(length=constants.Limit.MEDIUM),
        sa.ForeignKey(
            CONFIGURATIONS.columns.sensor_identifier,
            onupdate="CASCADE",
            ondelete="CASCADE",  # cascade is so fucking sexy
        ),
        nullable=False,
    ),
    sa.Column("measurement_timestamp", sa.Integer, nullable=False),
    sa.Column("receipt_timestamp", sa.Integer, nullable=False),
    # TODO implement as JSON for maximum flexibility?
    sa.Column("value", sa.Integer, nullable=False),
)

CONF = CONFIGURATIONS
MEAS = MEASUREMENTS

VALUE_IDENTIFIERS = set(MEASUREMENTS.columns.keys()) - {
    "sensor_identifier",
    "measurement_timestamp",
    "receipt_timestamp",
}
