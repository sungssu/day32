INSERT INTO shipping_quotes
    (text, weight, fee)
VALUES
    (%s, %s, %s)

ON CONFLICT (REQUEST_KEY) DO NOTHING
RETURNING ID