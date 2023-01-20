SELECT user_identifier, network_identifier  -- TODO: return role/level as well
FROM sessions
LEFT JOIN permissions USING (user_identifier)
WHERE access_token_hash = {access_token_hash}
