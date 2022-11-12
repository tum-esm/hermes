SELECT
    sensor_identifier,
    measurement_timestamp,
    measurement  -- implement selecting different values of this JSONB column, or not?
FROM measurements
{%- if request.query.sensors or request.query.start is not none or request.query.end is not none %}
WHERE
    TRUE
    {%- if request.query.sensors %} AND sensor_identifier = ANY({sensor_identifiers}){% endif %}
    {%- if request.query.start is not none %} AND measurement_timestamp >= {start_timestamp}{% endif %}
    {%- if request.query.end is not none %} AND measurement_timestamp < {end_timestamp}{% endif %}
{%- endif %}
ORDER BY measurement_timestamp ASC
OFFSET {skip}
LIMIT {limit};
