SELECT *  -- TODO: only return role/level
FROM permissions
WHERE user_identifier = {user_identifier} AND network_identifier = {network_identifier};
