{{
    config(
        materialized = 'table',
        schema       = 'silver',
    )
}}

with source as (

    select * from {{ source('bronze', 'sales_order_header') }}

),

cleaned as (

    select
        -- Natural keys
        id                                                  as order_guid,
        trim(number)                                        as order_no,

        -- Foreign keys
        customerId                                          as customer_guid,
        trim(coalesce(customerNumber, ''))                  as customer_no,
        trim(coalesce(customerName,   ''))                  as customer_name,

        -- Dates
        cast(orderDate              as date)                as order_date,
        cast(coalesce(postingDate, orderDate) as date)      as posting_date,
        cast(requestedDeliveryDate  as date)                as requested_delivery_date,

        -- Financial
        upper(trim(coalesce(currencyCode, 'LCY')))          as currency_code,
        cast(coalesce(totalAmountExcludingTax, 0) as decimal(18,2)) as amount_excl_tax,
        cast(coalesce(totalTaxAmount,          0) as decimal(18,2)) as tax_amount,
        cast(coalesce(totalAmountIncludingTax, 0) as decimal(18,2)) as amount_incl_tax,

        -- Attributes
        trim(coalesce(salesperson, ''))                     as salesperson_code,
        trim(status)                                        as order_status,

        -- Ship-to
        trim(coalesce(shipToName,        ''))               as ship_to_name,
        trim(coalesce(shipToAddressLine1,''))               as ship_to_address,
        trim(coalesce(shipToCity,        ''))               as ship_to_city,
        trim(coalesce(shipToCountry,     ''))               as ship_to_country,

        -- Derived flag
        case when status = 'Released' then 1 else 0 end    as is_released,

        -- Audit
        cast(lastModifiedDateTime as datetime2(0))          as last_modified_at,
        _ingested_at,
        _source_system,
        getutcdate()                                        as _dbt_updated_at

    from source
    where id is not null

)

select * from cleaned
