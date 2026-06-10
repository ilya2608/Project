{{
    config(
        materialized = 'table',
        schema       = 'silver',
    )
}}

with source as (

    select * from {{ source('bronze', 'sales_order_line') }}

),

cleaned as (

    select
        -- Natural keys
        id                                                      as line_guid,
        documentId                                              as order_guid,
        cast(sequence as int)                                   as line_sequence,

        -- Item reference
        itemId                                                  as item_guid,
        trim(coalesce(itemNumber,   ''))                        as item_no,
        trim(coalesce(description,  ''))                        as line_description,
        trim(coalesce(unitOfMeasureCode, ''))                   as uom_code,

        -- Quantities & pricing
        cast(coalesce(quantity,       0) as decimal(18,4))      as quantity,
        cast(coalesce(unitPrice,      0) as decimal(18,4))      as unit_price,
        cast(coalesce(discountAmount, 0) as decimal(18,2))      as discount_amount,
        cast(coalesce(discountPercent,0) as decimal(5,2))       as discount_pct,
        cast(coalesce(taxPercent,     0) as decimal(5,2))       as tax_pct,
        cast(coalesce(lineAmount,     0) as decimal(18,2))      as line_amount,

        -- Derived
        cast(coalesce(quantity, 0) * coalesce(unitPrice, 0)
             as decimal(18,2))                                   as gross_line_amount,
        cast(coalesce(quantity, 0) * coalesce(unitPrice, 0)
             - coalesce(discountAmount, 0)
             as decimal(18,2))                                   as net_line_amount,

        -- Date
        cast(shipmentDate as date)                              as shipment_date,

        -- Audit
        cast(lastModifiedDateTime as datetime2(0))              as last_modified_at,
        _ingested_at,
        _source_system,
        getutcdate()                                            as _dbt_updated_at

    from source
    where id is not null

)

select * from cleaned
