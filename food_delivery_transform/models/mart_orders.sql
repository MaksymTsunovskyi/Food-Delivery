WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
)

SELECT
    o.*,
    c.full_name AS customer_name,
    c.email AS customer_email
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id