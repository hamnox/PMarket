import psycopg2
import json


with open("postgres_auth", 'r') as reader:
    auth = json.load(reader)

conn = psycopg2.connect(**auth)
# ** takes a dictionary, and expands it into keyword arguments.
# * is just expansion into positional arguments

cur = conn.cursor()

cur.execute("""
    create table if not exists users (
        id SERIAL PRIMARY KEY,
        username char(256) UNIQUE NOT NULL,
        password char(64) NOT NULL,
        datejoined timestamp NOT NULL
    )""")

cur.execute("""
    create table if not exists predictions (
        id SERIAL PRIMARY KEY,
        created_by integer NOT NULL references 
            users(id),
        statement char(200) NOT NULL, 
        description text,
        datecreated timestamp NOT NULL,
        dateresolved timestamp,
        result boolean,
        initial_bet numeric(5,3)
    )""")

cur.execute("""
    create table if not exists bets (
        id SERIAL PRIMARY KEY,
        created_by integer NOT NULL references
            users(id),
        credence numeric(5,3),
        timestamp timestamp NOT NULL,
        prediction_id integer NOT NULL references
            predictions(id)
    )""")

#sessions and migrations

conn.commit()

cur.close()
conn.close()
