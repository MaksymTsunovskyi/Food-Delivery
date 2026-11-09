WITH source AS (
    SELECT * FROM {{ source('raw', 'delivery_routes') }}
)
SELECT DISTINCT * FROM source