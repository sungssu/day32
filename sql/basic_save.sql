INSERT INTO shipping_quotes (label, weight, fee, rule_version)
VALUES (%s, %s, %s, %s)

ON CONFLICT (REQUEST_KEY) DO NOTHING
RETURNING ID