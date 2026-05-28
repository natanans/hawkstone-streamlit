CREATE OR REPLACE TABLE PROD.DW.CUSTOMERS_DOMAIN AS 


SELECT 
      k.profile_id AS PROFILE_ID
    , o.customer_id
    , min(o.created_At)                                                     as first_order_date 
    , max(o.created_at)                                                     as last_order_date 
    , AVG(o.DAYS_BETWEEN_ORDERS)                                            as avg_Days_Between_orders
    , sum(o.ITEMS_PRICE)                                                    as total_sales
    , datediff('day',last_order_date,current_Date())                        as days_since_last_order
    , datediff('day',first_order_date,current_Date())                       as days_since_first_order
    , count(distinct o.name)                                                as number_of_orders
    , max(case when k.clicks + k.opens > 0 then k.minimum_send_date end)    as email_engaged_date
    , case 
        when days_since_last_order <= 150 then '1'
        when days_since_last_order <= 450 then '2'
        else '3'
      end as recency 
    , case 
        when avg_Days_Between_orders <= 45 then '1'
        when avg_Days_Between_orders <= 150 then '2'
        else '3'
      end as frequency 
    , case 
        when total_sales >= 11000 then '3'
        when total_sales >= 3700 then '2'
        else '1'
      end as monetary 
    , case 
        when datediff('day',email_engaged_date,current_date()) <= 60 then '1' 
        else '2' 
      end as engaged 
    , recency || ' ' || frequency || ' ' || monetary || ' ' || engaged as rfme_score
    , case
      -- Closet obsessed: recent + frequent + high spend
      when recency <= 2 and frequency <= 2 and monetary = 3
        then 'Closet obsessed'
      -- Outfit repeaters: recent + frequent + mid/low spend + engaged
      when recency <= 2 and frequency <= 2 and (monetary = 2 or (monetary = 1 and engaged = 1))
        then 'Outfit repeaters'
      -- Sale rack lurkers: recent but infrequent, or low spend + disengaged
      when recency <= 2 and (frequency = 3 or (monetary = 1 and engaged = 2))
        then 'Sale rack lurkers'
      -- Almost exes: high/mid value + lapsing + still email-engaged
      when monetary >= 2 and (recency = 3 or frequency = 3) and engaged = 1
        then 'Almost exes'
      -- Left on read: lapsing + email disengaged
      when (recency = 3 or frequency = 3) and engaged = 2
        then 'Left on read'
      -- Ghosted: lapsed + low spend + still opening emails
      else 'Ghosted'
    end as persona
    , min(first_click_channel)    as first_click_channel
    , min(last_click_channel)     as last_click_channel
FROM PROD.DW.ORDERS_DOMAIN o
LEFT JOIN PROD.DW.KLAVIYO_PERFORMANCE_DOMAIN k 
    on k.profile_id = o.profile_id
group by 1,2


;
