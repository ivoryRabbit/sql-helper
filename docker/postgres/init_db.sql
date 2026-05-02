CREATE SCHEMA IF NOT EXISTS data_catalog;

GRANT ALL ON SCHEMA data_catalog TO sqlhelper;

ALTER ROLE sqlhelper SET search_path = "data_catalog";

SET search_path = "data_catalog";

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
