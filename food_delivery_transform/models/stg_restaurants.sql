WITH source AS (
    SELECT * FROM {{ source('raw', 'restaurants') }}
)
SELECT DISTINCT * FROM source