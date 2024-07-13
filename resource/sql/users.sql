CREATE TABLE IF NOT EXISTS users (
    id         BIGINT PRIMARY KEY,
    gender     VARCHAR(4),
    age        SMALLINT,
    occupation INTEGER,
    zipcode    VARCHAR(10)
)