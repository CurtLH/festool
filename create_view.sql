drop view festool_view;
create view festool_view as
select 
 id,
 date_trunc('minute', datetime_collected) as datetime_collected,
 product_name,
 original_price::money,
 refurb_price::money,
 discount,
 date_trunc('minute', age(LEAD(datetime_collected, 1) over (order by datetime_collected), datetime_collected)) as time_available
 from festool;
