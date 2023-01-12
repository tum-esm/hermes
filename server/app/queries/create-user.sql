INSERT INTO users (
    user_identifier,
    username,
    creation_timestamp,
    password_hash
)
VALUES (
    uuid_generate_v4(),
    {username},
    now(),
    {password_hash}
)
RETURNING user_identifier;
