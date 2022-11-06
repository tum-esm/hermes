SELECT
    sensor_identifier,
    measurement_timestamp,
    measurement  -- implement selecting different values of this JSONB column
FROM measurements
{%- if request.query.sensors or request.query.start is not none or request.query.end is not none %}
WHERE
    TRUE
    {%- if request.query.sensors %} AND sensor_identifier = ANY($1::TEXT[]){% endif %}
    {%- if request.query.start is not none %} AND measurement_timestamp >= $2::INT{% endif %}
    {%- if request.query.end is not none %} AND measurement_timestamp < $3::INT{% endif %}
{%- endif %}
ORDER BY measurement_timestamp ASC
OFFSET $4
LIMIT $5
