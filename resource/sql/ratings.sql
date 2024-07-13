CREATE TABLE IF NOT EXISTS ratings (
    user_id    BIGINT,
    movie_id   BIGINT,
    rating     FLOAT,
    timestamp  TIMESTAMP(3),
    PRIMARY KEY (user_id, movie_id)
)