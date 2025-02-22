import textwrap

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer

from model.ddl_collection import DDLCollection


URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
SCHEMA = "vectordb"

engine = create_engine(
    url=URL,
    connect_args={"options": f"-csearch_path={SCHEMA}"},
    echo=True,
)

session_maker = sessionmaker(bind=engine, expire_on_commit=False)


LOCAL_CACHE_PREFIX = "/tmp/text-to-sql/model"
embedding_model = SentenceTransformer(
    model_name_or_path="sentence-transformers/paraphrase-albert-small-v2",
    cache_folder=LOCAL_CACHE_PREFIX,
)

movies_ddl_content = textwrap.dedent(
    """
    CREATE TABLE movies (
        id       BIGINT PRIMARY KEY,
        title    VARCHAR,
        genres   VARCHAR,
        year     SMALLINT
    )
    """
)

users_ddl_content = textwrap.dedent(
    """
    CREATE TABLE users (
        id         BIGINT PRIMARY KEY,
        gender     VARCHAR(4),
        age        SMALLINT,
        occupation INTEGER,
        zipcode    VARCHAR(10)
    )
    """
)

ratings_ddl_content = textwrap.dedent(
    """
    CREATE TABLE ratings (
        user_id    BIGINT,
        movie_id   BIGINT,
        rating     FLOAT,
        timestamp  TIMESTAMP(3),
        PRIMARY KEY (user_id, movie_id)
    )
    """
)

movies_ddl = DDLCollection(
    table_name="movies",
    ddl_content=movies_ddl_content,
    embedding=embedding_model.encode(movies_ddl_content),
)

users_ddl = DDLCollection(
    table_name="users",
    ddl_content=users_ddl_content,
    embedding=embedding_model.encode(users_ddl_content),
)

ratings_ddl = DDLCollection(
    table_name="ratings",
    ddl_content=ratings_ddl_content,
    embedding=embedding_model.encode(ratings_ddl_content),
)

with session_maker.begin() as session:
    session.add_all([movies_ddl, users_ddl, ratings_ddl])
    session.commit()
