{{
    config(
        materialized = 'table',
        schema       = 'silver',
    )
}}

with source as (

    select * from {{ source('bronze', 'item') }}

),

cleaned as (

    select
        -- Natural keys
        id                                              as item_guid,
        trim(number)                                    as item_no,

        -- Descriptive attributes
        trim(displayName)                               as item_name,
        trim(coalesce(type, 'Inventory'))               as item_type,
        trim(coalesce(itemCategoryCode, 'UNCATEGORISED')) as item_category_code,
        trim(coalesce(baseUnitOfMeasureCode, 'PCS'))    as base_uom_code,

        -- Pricing / cost
        cast(coalesce(unitPrice, 0) as decimal(18,4))  as unit_price,
        cast(coalesce(unitCost,  0) as decimal(18,4))  as unit_cost,
        cast(coalesce(inventory, 0) as decimal(18,4))  as qty_on_hand,

        -- Flags
        case when blocked = 1 then 1 else 0 end        as is_blocked,

        -- Audit
        cast(lastModifiedDateTime as datetime2(0))     as last_modified_at,
        _ingested_at,
        _source_system,
        getutcdate()                                    as _dbt_updated_at

    from source
    where id is not null

)

select * from cleaned
