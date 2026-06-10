{{
    config(
        materialized = 'table',
        schema       = 'gold',
    )
}}

-- Fully-denormalised sales order flat table.
-- One row per order line enriched with customer and item attributes.
-- Ideal as the single source for ad-hoc reporting and Power BI semantic models.

with header as (
    select * from {{ ref('fact_sales_order_header') }}
),

line as (
    select * from {{ ref('fact_sales_order_line') }}
),

customer as (
    select * from {{ ref('dim_customer') }}
),

item as (
    select * from {{ ref('dim_item') }}
)

select
    -- Order identifiers
    h.order_no,
    h.order_guid,
    l.line_guid,
    l.line_sequence,

    -- Dates
    h.order_date,
    h.posting_date,
    h.requested_delivery_date,
    l.shipment_date,
    year(h.order_date)                          as order_year,
    month(h.order_date)                         as order_month,
    datepart(quarter, h.order_date)             as order_quarter,
    format(h.order_date, 'yyyy-MM')             as order_year_month,

    -- Customer
    c.customer_no,
    c.customer_name,
    c.country_code                              as customer_country,
    c.city                                      as customer_city,
    c.currency_code                             as customer_currency,

    -- Salesperson & status
    h.salesperson_code,
    h.order_status,
    h.is_released,

    -- Item / product
    i.item_no,
    i.item_name,
    i.item_category_code,
    i.item_type,
    l.uom_code,

    -- Financials (line level)
    l.quantity,
    l.unit_price,
    l.discount_pct,
    l.discount_amount,
    l.gross_line_amount,
    l.net_line_amount,
    l.tax_pct,
    l.line_amount                               as line_amount_incl_tax,

    -- Derived
    i.unit_cost,
    l.quantity * i.unit_cost                    as line_cost,
    l.net_line_amount - (l.quantity * i.unit_cost)
                                                as line_gross_margin,
    case
        when l.net_line_amount > 0
        then (l.net_line_amount - l.quantity * i.unit_cost) / l.net_line_amount * 100
    end                                         as line_gross_margin_pct,

    -- Order totals (header level — repeated per line for slice-and-dice)
    h.amount_excl_tax                           as order_amount_excl_tax,
    h.tax_amount                                as order_tax_amount,
    h.amount_incl_tax                           as order_amount_incl_tax,
    h.currency_code                             as order_currency,

    getutcdate()                                as _dbt_updated_at

from header h
join line     l on l.order_guid    = h.order_guid
left join customer c on c.customer_guid = h.customer_guid
left join item     i on i.item_guid     = l.item_guid
