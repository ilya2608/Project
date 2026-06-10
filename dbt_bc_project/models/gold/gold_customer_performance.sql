{{
    config(
        materialized = 'table',
        schema       = 'gold',
    )
}}

-- Customer-level performance summary used by the sales team and CRM dashboards.

with header as (
    select * from {{ ref('fact_sales_order_header') }}
),

line as (
    select * from {{ ref('fact_sales_order_line') }}
),

customer as (
    select * from {{ ref('dim_customer') }}
),

order_lines as (

    select
        h.customer_guid,
        h.order_guid,
        h.order_date,
        h.order_status,
        h.currency_code,
        l.line_guid,
        l.gross_line_amount,
        l.discount_amount,
        l.net_line_amount,
        l.quantity

    from header h
    join line l on l.order_guid = h.order_guid

),

aggregated as (

    select
        customer_guid,
        currency_code,

        count(distinct order_guid)                      as total_orders,
        count(line_guid)                                as total_lines,
        sum(quantity)                                   as total_qty_ordered,
        sum(gross_line_amount)                          as gross_revenue,
        sum(discount_amount)                            as total_discounts_given,
        sum(net_line_amount)                            as net_revenue,

        min(order_date)                                 as first_order_date,
        max(order_date)                                 as last_order_date,
        datediff(day, min(order_date), max(order_date)) as customer_tenure_days,

        sum(net_line_amount) / nullif(count(distinct order_guid), 0)
                                                        as avg_order_value,

        -- Simple RFM components
        datediff(day, max(order_date), cast(getutcdate() as date))
                                                        as days_since_last_order,
        count(distinct order_guid)                      as frequency,
        sum(net_line_amount)                            as monetary_value

    from order_lines
    group by customer_guid, currency_code

),

final as (

    select
        c.customer_guid,
        c.customer_no,
        c.customer_name,
        c.country_code,
        c.city,
        c.is_blocked,
        c.credit_limit,
        c.current_balance,

        a.currency_code,
        a.total_orders,
        a.total_lines,
        a.total_qty_ordered,
        a.gross_revenue,
        a.total_discounts_given,
        a.net_revenue,
        a.first_order_date,
        a.last_order_date,
        a.customer_tenure_days,
        a.avg_order_value,
        a.days_since_last_order,
        a.frequency,
        a.monetary_value,

        -- RFM tier (simple banding — adjust thresholds to your business)
        case
            when a.days_since_last_order <= 30  then 'Recent'
            when a.days_since_last_order <= 90  then 'Active'
            when a.days_since_last_order <= 180 then 'At Risk'
            else 'Lapsed'
        end                                             as recency_tier,

        case
            when a.net_revenue >= 100000 then 'High Value'
            when a.net_revenue >= 10000  then 'Mid Value'
            else 'Low Value'
        end                                             as value_tier,

        getutcdate()                                    as _dbt_updated_at

    from customer c
    left join aggregated a on a.customer_guid = c.customer_guid

)

select * from final
