SELECT vendor_item_id,
    case when is_live = 1 and is_oos = 0 and is_used = 0 then 1 else 0 end as is_sellable
FROM temp.dm_vendor_item