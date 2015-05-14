from passlib.hash import bcrypt
import psycopg2
import json


with open("postgres_auth", 'r') as reader:
    auth = json.load(reader)

conn = psycopg2.connect(**auth)
# ** takes a dictionary, and expands it into keyword arguments.
# * is just expansion into positional arguments

cur = conn.cursor()

# users table
cur.execute("""
    create table if not exists users (
        id SERIAL PRIMARY KEY,
        username varchar(256) UNIQUE NOT NULL,
        password varchar(256) NOT NULL,
        joined timestamp NOT NULL
    )""")

# insert some test users
cur.execute(""" INSERT
    INTO users (id, username, password, joined)
    SELECT 0, 'House', 'house', CURRENT_TIMESTAMP
    WHERE 'testuser' NOT IN
        (
        SELECT username
        FROM users
        )""")

cur.execute(""" INSERT
    INTO users (username, password, joined)
    SELECT 'testuser',%s, CURRENT_TIMESTAMP
    WHERE 'testuser' NOT IN
        (
        SELECT username
        FROM users
        )""",
    (bcrypt.encrypt("pass1"),))

cur.execute("""INSERT
    INTO users (username, password, joined)
    SELECT 'testuser2',%s, CURRENT_TIMESTAMP
    WHERE 'testuser2' NOT IN
        (
        SELECT username
        FROM users
        )""",
    (bcrypt.encrypt("pass2"),))

# predictions table
cur.execute("""
    create table if not exists predictions (
        id SERIAL PRIMARY KEY,
        created_by integer NOT NULL references 
            users(id),
        statement varchar(200) NOT NULL, 
        smalltext text,
        created timestamp NOT NULL,
        due timestamp,
        resolved timestamp,
        result boolean
    )""")

# insert some predictions
cur.execute("""INSERT
    INTO predictions (created_by, created, statement)
    SELECT 1, CURRENT_TIMESTAMP, 'once a jolly swagman'
    WHERE 'once a jolly swagman' NOT IN
        (
        SELECT statement
        FROM predictions
        )""")
cur.execute("""INSERT
    INTO predictions (created_by, created, statement)
    SELECT 1, CURRENT_TIMESTAMP, 'elementary, my dear watson'
    WHERE 'elementary, my dear watson' NOT IN
        (
        SELECT statement
        FROM predictions
        )""")

# need to find someway to autocreate
# teh first bet, no?
# CREATE TRIGGER trigger_name AFTER INSERT ON table_name
#   FOR EACH ROW EXECUTE PROCEDURE function_name(arguments)
# next see CREATE FUNCTION

# bets table
cur.execute("""
    create table if not exists bets (
        id SERIAL PRIMARY KEY,
        created_by integer NOT NULL references
            users(id),
        credence numeric(5,3),
        created timestamp NOT NULL,
        prediction integer NOT NULL references
            predictions(id)
    )""")

#sessions and migrations

cur.execute("""
    create table if not exists sessions (
        id char(36) PRIMARY KEY,
        login integer NOT NULL references users(id),
        expiration timestamp
    )""")

conn.commit()

cur.close()
conn.close()
