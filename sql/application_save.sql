INSERT INTO budget_plans (title, income, expense, balance)
VALUES (%s, %s, %s, %s)

RETURNING ID