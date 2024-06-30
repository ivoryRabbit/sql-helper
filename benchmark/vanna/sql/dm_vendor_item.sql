CREATE TABLE IF NOT EXISTS temp.dm_vendor_item (
    vendor_item_id BIGINT PRIMARY KEY,
    vendor_id VARCHAR,
    first_created_dt TIMESTAMP(3),
    first_listing_dt TIMESTAMP(3),
    first_stowed_dt TIMESTAMP(3),
    first_sales_dt TIMESTAMP(3),
    sales INT,
    price INT,
    is_live SMALLINT,
    is_oos SMALLINT,
    is_used SMALLINT
)