WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),
restaurants AS (
    SELECT * FROM {{ ref('stg_restaurants') }}
),
couriers AS (
    SELECT * FROM {{ ref('stg_couriers') }}
)

SELECT
    o.*,
    c.full_name AS customer_name,
    c.email AS customer_email,
    r.restaurant_name AS restaurant_name,
    cr.courier_name AS courier_name    
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN couriers cr ON o.courier_id = cr.courier_id