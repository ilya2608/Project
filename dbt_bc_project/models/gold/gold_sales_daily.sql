{{
    config(
        materialized = 'table',
        schema       = 'gold',
    )
}}

-- Daily sales summary — one row per calendar day.
-- Joins header + line + customer so every BI tool has a single flat table to query.

with header as (
    select * from {{ ref('fact_sales_order_header') }}
),

line as (
    select * from {{ ref('fact_sales_order_line') }}
),

customer as (
    select * from {{ ref('dim_customer') }}
),

order_totals as (

    select
        h.order_date,
        h.order_guid,
        h.order_no,
        h.customer_guid,
        h.customer_no,
        h.customer_name,
        c.country_code,
        h.currency_code,
        h.salesperson_code,
        h.order_status,
        h.is_released,

        -- Aggregate lines per order
        count(l.line_guid)                  as line_count,
        sum(l.quantity)                     as total_qty,
        sum(l.gross_line_amount)            as gross_sales_amount,
        sum(l.discount_amount)              as total_discount_amount,
        sum(l.net_line_amount)              as net_sales_amount,
        sum(l.line_amount * l.tax_pct / 100)as total_tax_amount

    from header h
    left join line     l on l.order_guid    = h.order_guid
    left join customer c on c.customer_guid = h.customer_guid
    group by
        h.order_date, h.order_guid, h.order_no,
        h.customer_guid, h.customer_no, h.customer_name,
        c.country_code, h.currency_code, h.salesperson_code,
        h.order_status, h.is_released

),

daily as (

    select
        order_date,
        country_code,
        currency_code,
        salesperson_code,

        count(distinct order_guid)          as order_count,
        count(distinct customer_guid)       as unique_customers,
        sum(total_qty)                      as total_qty_sold,
        sum(gross_sales_amount)             as gross_sales,
        sum(total_discount_amount)          as total_discounts,
        sum(net_sales_amount)               as net_sales,
        sum(total_tax_amount)               as total_tax,
        sum(net_sales_amount) / nullif(count(distinct order_guid), 0)
                                            as avg_order_value,

        getutcdate()                        as _dbt_updated_at

    from order_totals
    group by
        order_date, country_code, currency_code, salesperson_code

)

select * from daily
