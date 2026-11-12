WITH source AS (
    SELECT * FROM {{ source('raw', 'food_orders') }}
)

SELECT * FROM source