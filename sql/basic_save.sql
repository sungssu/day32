INSERT INTO shipping_quotes (label, weight, fee, rule_version)
VALUES (%s, %s, %s, %s)

RETURNING ID