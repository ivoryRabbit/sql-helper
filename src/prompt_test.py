prompts = [
    {
        "role": "system",
        "content": """
            You are a SQL expert. Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. 

            ===Response Guidelines 
            1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question.
            2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql.
            3. If the provided context is insufficient, please explain why it can't be generated.
            4. If the question has been asked and answered before, please repeat the answer exactly as it was given before.
            5. Please use the most relevant table(s) and columns from those tables.
            6. Please format the query before responding.
        """
    },
    {
        "role": "user",
        "content": """
            Please generate a DDL query to to create the table described in the following table summary.

            ===Table summary
            The "movies" table contains data about movies. It has the following columns:
            - id (BIGINT): unique identifier for each movie
            - title (VARCHAR): the title of the movie
            - genres (VARCHAR): the genres of the movie
            - year (SMALLINT): the year the movie was released
        """,
    },
    {
        "role": "assistant",
        "content": """
            CREATE TABLE movies (
                id       BIGINT PRIMARY KEY,
                title    VARCHAR,
                genres   VARCHAR,
                year     SMALLINT
            )
        """,
    },
    {
        "role": "user",
        "content": """
            Please generate a DDL query to to create the table described in the following table summary.

            ===Table summary
            The "ratings" table contains data about user ratings for movies. It has the following columns:
            - user_id (BIGINT): the ID of the user who rated the movie
            - movie_id (BIGINT): the ID of the movie that was rated
            - rating (FLOAT): the rating given by the user for the movie
            - timestamp (TIMESTAMP): the timestamp when the rating was recorded
        """,
    },
    {
        "role": "assistant",
        "content": """
            CREATE TABLE ratings (
                user_id    BIGINT,
                movie_id   BIGINT,
                rating     FLOAT,
                timestamp  TIMESTAMP,
                PRIMARY KEY (user_id, movie_id)
            )
        """,
    },
    {
        "role": "user",
        "content": """
            Please generate a DDL query to to create the table described in the following table summary.

            ===Table summary
            The "users" table contains data about users' gender, age, occupation, and zipcode. It has the following columns:
            - id (BIGINT): unique identifier for each user
            - gender (VARCHAR(4)): gender of the user
            - age (SMALLINT): age of the user
            - occupation (INTEGER): occupation code of the user
            - zipcode (VARCHAR(10)): zipcode of the user
        """,
    },
    {
        "role": "assistant",
        "content": """
            CREATE TABLE users (
                id         BIGINT PRIMARY KEY,
                gender     VARCHAR(4),
                age        SMALLINT,
                occupation INTEGER,
                zipcode    VARCHAR(10)
            )
        """,
    },
    {
        "role": "user",
        "content": """
            Show me average of ratings for each movies
        """,
    }
]

prompts2 = [
    {
        "role": "system",
        "content": """
            You are a data analyst that can help summarize SQL tables.
            Please summarize below table by the given context. The response should ONLY be based on the given context and follow the response guidelines and format instructions.

            ===Table Schema
            CREATE TABLE users (
                id         BIGINT PRIMARY KEY,
                gender     VARCHAR(4),
                age        SMALLINT,
                occupation INTEGER,
                zipcode    VARCHAR(10)
            )

            ===Response guideline
             1. In the first line, please write the table description in 20 words or less only on provided information. The table description should contain the table name.
             2. After the second line, please describe each columns using bullet points.
             3. Do not use any adjective to describe the table.
             4. Your table summary response is going to be used to generate the table DDL in the future. 

            ===Response Format
            The "{table name}" table contains data about {table summary}. It has the following columns:
            - {column name} ({column type}): {column description}
        """
    },
]