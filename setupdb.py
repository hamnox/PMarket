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

cur.execute(""" insert into users (username,
    password, datejoined) values ('testuser',
    'very secure hash', CURRENT_TIMESTAMP)""")

cur.execute("""
    create table if not exists predictions (
        id SERIAL PRIMARY KEY,
        created_by integer NOT NULL references 
            users(id),
        statement char(200) NOT NULL, 
        smalltext text,
        datecreated timestamp NOT NULL,
        expectresolved timestamp,
        dateresolved timestamp,
        result boolean,
        initial_bet numeric(5,3) DEFAULT 50
    )""")

cur.execute("""insert into predictions (created_by,
    datecreated, statement) values (1, CURRENT_TIMESTAMP,
    'the rain in spain stays mainly in the plains'),
    (1, CURRENT_TIMESTAMP,
    'elementary, my dear watson'),
    (1, CURRENT_TIMESTAMP, 'he''s a jolly good fellow')""")

# need to find someway to autocreate
# teh first bet, no?

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
