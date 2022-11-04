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
    "dsn": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}


########################################################################################
# Query helpers
########################################################################################


def filter_sensor_identifier(conditions, request):
    """Add conditions to constrain the returned sensor identifiers."""
    return conditions + [
        sa.or_(
            MEASUREMENTS.c.sensor_identifier == sensor_identifier
            for sensor_identifier in request.query.sensors
        ),
    ]


def filter_measurement_timestamp(conditions, request):
    """Add conditions to constrain the returned measurement timestamps."""
    res = []
    if request.query.start_timestamp is not None:
        res.append(
            MEASUREMENTS.c.measurement_timestamp >= int(request.query.start_timestamp)
        )
    if request.query.end_timestamp is not None:
        res.append(
            MEASUREMENTS.c.measurement_timestamp < int(request.query.end_timestamp)
        )
    return conditions + res


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

VALUE_IDENTIFIERS = set(MEASUREMENTS.columns.keys()) - {
    "sensor_identifier",
    "measurement_timestamp",
    "receipt_timestamp",
}
