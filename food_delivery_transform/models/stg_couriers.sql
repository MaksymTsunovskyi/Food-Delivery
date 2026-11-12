WITH source AS (
    SELECT * FROM {{ source('raw', 'couriers') }}
)
SELECT DISTINCT * FROM source