INSERT INTO sessions (
    access_token_hash,
    user_identifier,
    creation_timestamp
)
VALUES (
    {access_token_hash},
    {user_identifier},
    now()
)
