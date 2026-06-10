{{
    config(
        materialized = 'table',
        schema       = 'silver',
    )
}}

with source as (

    select * from {{ source('bronze', 'customer') }}

),

cleaned as (

    select
        -- Natural keys
        id                                          as customer_guid,
        trim(number)                                as customer_no,

        -- Descriptive attributes
        trim(displayName)                           as customer_name,
        trim(coalesce(addressLine1, ''))            as address_line_1,
        trim(coalesce(addressLine2, ''))            as address_line_2,
        trim(coalesce(city, ''))                    as city,
        trim(coalesce(state, ''))                   as state_province,
        trim(coalesce(country, ''))                 as country_code,
        trim(coalesce(postalCode, ''))              as postal_code,
        upper(trim(coalesce(currencyCode, 'LCY'))) as currency_code,
        trim(coalesce(phoneNumber, ''))             as phone_number,
        lower(trim(coalesce(email, '')))            as email,

        -- Flags & financial
        case
            when blocked in ('All', 'Ship', 'Invoice') then 1
            else 0
        end                                         as is_blocked,
        blocked                                     as blocked_reason,
        cast(coalesce(creditLimit, 0) as decimal(18,2))  as credit_limit,
        cast(coalesce(balance, 0)     as decimal(18,2))  as current_balance,

        -- Audit
        cast(lastModifiedDateTime as datetime2(0)) as last_modified_at,
        _ingested_at,
        _source_system,
        getutcdate()                                as _dbt_updated_at

    from source
    where id is not null

)

select * from cleaned
