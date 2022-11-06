import typing

import databases.interfaces
import sqlalchemy as sa
import jinja2
import sqlalchemy.dialects.postgresql

import app.constants as constants
import app.settings as settings


CONFIGURATION = {
    "dsn": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}

templates = jinja2.Environment(
    loader=jinja2.PackageLoader(package_name="app", package_path="queries"),
    autoescape=jinja2.select_autoescape(),
)


def dictify(result: typing.Sequence[databases.interfaces.Record]) -> typing.List[dict]:
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


async def initialize(database_client):
    """Create tables, and error out if existing tables don't match the schema."""
    await database_client.execute(
        query=templates.get_template("create_table_configurations.sql").render()
    )
    await database_client.execute(
        query=templates.get_template("create_table_measurements.sql").render()
    )
