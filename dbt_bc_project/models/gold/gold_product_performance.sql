{{
    config(
        materialized = 'table',
        schema       = 'gold',
    )
}}

-- Product-level sales performance — used by purchasing, inventory, and product dashboards.

with line as (
    select * from {{ ref('fact_sales_order_line') }}
),

header as (
    select * from {{ ref('fact_sales_order_header') }}
),

item as (
    select * from {{ ref('dim_item') }}
),

line_with_header as (

    select
        l.item_guid,
        l.item_no,
        l.line_description,
        l.uom_code,
        l.quantity,
        l.unit_price,
        l.discount_amount,
        l.discount_pct,
        l.gross_line_amount,
        l.net_line_amount,
        l.shipment_date,
        h.order_date,
        h.customer_guid,
        h.order_guid,
        h.currency_code

    from line l
    join header h on h.order_guid = l.order_guid

),

aggregated as (

    select
        item_guid,
        currency_code,

        count(distinct order_guid)                      as times_ordered,
        count(distinct customer_guid)                   as unique_customers,
        sum(quantity)                                   as total_qty_sold,
        avg(unit_price)                                 as avg_selling_price,
        sum(gross_line_amount)                          as gross_revenue,
        sum(discount_amount)                            as total_discounts,
        sum(net_line_amount)                            as net_revenue,
        sum(discount_amount) / nullif(sum(gross_line_amount), 0) * 100
                                                        as avg_discount_pct,

        min(order_date)                                 as first_sold_date,
        max(order_date)                                 as last_sold_date,
        datediff(day, max(order_date), cast(getutcdate() as date))
                                                        as days_since_last_sale,

        -- Rolling windows — last 30 / 90 days
        sum(case when order_date >= dateadd(day, -30, cast(getutcdate() as date))
                 then net_line_amount else 0 end)       as net_revenue_l30d,
        sum(case when order_date >= dateadd(day, -90, cast(getutcdate() as date))
                 then net_line_amount else 0 end)       as net_revenue_l90d,
        sum(case when order_date >= dateadd(day, -30, cast(getutcdate() as date))
                 then quantity else 0 end)              as qty_sold_l30d

    from line_with_header
    group by item_guid, currency_code

),

final as (

    select
        i.item_guid,
        i.item_no,
        i.item_name,
        i.item_type,
        i.item_category_code,
        i.base_uom_code,
        i.unit_price                                    as list_price,
        i.unit_cost,
        i.qty_on_hand,
        i.is_blocked,

        a.currency_code,
        a.times_ordered,
        a.unique_customers,
        a.total_qty_sold,
        a.avg_selling_price,
        a.gross_revenue,
        a.total_discounts,
        a.net_revenue,
        a.avg_discount_pct,
        a.first_sold_date,
        a.last_sold_date,
        a.days_since_last_sale,
        a.net_revenue_l30d,
        a.net_revenue_l90d,
        a.qty_sold_l30d,

        -- Margin (requires cost data on item)
        a.net_revenue - (i.unit_cost * a.total_qty_sold)
                                                        as gross_margin,
        case
            when a.net_revenue > 0
            then (a.net_revenue - (i.unit_cost * a.total_qty_sold)) / a.net_revenue * 100
        end                                             as gross_margin_pct,

        -- Velocity tier
        case
            when a.qty_sold_l30d > 100 then 'Fast Moving'
            when a.qty_sold_l30d > 10  then 'Regular'
            when a.qty_sold_l30d > 0   then 'Slow Moving'
            else 'No Sales'
        end                                             as velocity_tier,

        getutcdate()                                    as _dbt_updated_at

    from item i
    left join aggregated a on a.item_guid = i.item_guid

)

select * from final
