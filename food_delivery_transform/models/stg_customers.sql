WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

cleaned_customers AS (
    SELECT DISTINCT
        customer_id,
        full_name,
        email
    FROM source
    WHERE email IS NOT NULL
)

SELECT * FROM cleaned_customers