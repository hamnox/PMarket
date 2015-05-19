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
        joined timestamp
                DEFAULT CURRENT_TIMESTAMP
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
    INTO users (username, password)
    SELECT 'testuser',%s
    WHERE 'testuser' NOT IN
        (
        SELECT username
        FROM users
        )""",
    (bcrypt.encrypt("pass1"),))

cur.execute("""INSERT
    INTO users (username, password)
    SELECT 'testuser2',%s
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
        created timestamp DEFAULT CURRENT_TIMESTAMP,
        due timestamp,
        resolved timestamp,
        result boolean,
        private boolean DEFAULT false
    )""")

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

# bets autocreate function
# http://stackoverflow.com/questions/
#     2253357/using-rule-to-insert-into-secondary-table-
#     auto-increments-sequence

cur.execute("""CREATE OR REPLACE FUNCTION housebet()
        RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO bets (created_by, credence,
                        created, prediction)
                SELECT 0, 50, new.created, new.id
                    WHERE (0,new.id) NOT IN
                        (
                        SELECT created_by, prediction
                        FROM bets
                        );
                RETURN NEW;
            END;
        $$
        LANGUAGE plpgsql volatile;
    """)

cur.execute("""DROP TRIGGER IF EXISTS autohousebet
            ON predictions""")

cur.execute("""CREATE TRIGGER autohousebet
            AFTER insert
            ON predictions
            FOR EACH ROW
            EXECUTE PROCEDURE housebet()
            """)

# insert some predictions
cur.execute("""INSERT
    INTO predictions (created_by, statement)
    SELECT 1, 'once a jolly swagman'
    WHERE 'once a jolly swagman' NOT IN
        (
        SELECT statement
        FROM predictions
        )""")

cur.execute("""INSERT
    INTO predictions (created_by, statement)
    SELECT 1, 'elementary, my dear watson'
    WHERE 'elementary, my dear watson' NOT IN
        (
        SELECT statement
        FROM predictions
        )""")

#sessions and migrations

cur.execute("""
    create table if not exists sessions (
        id char(36) PRIMARY KEY,
        login integer NOT NULL references users(id),
        initiated timestamp
                DEFAULT CURRENT_TIMESTAMP,
        expiration timestamp
                DEFAULT CURRENT_TIMESTAMP + interval '7 days'
    )""")

conn.commit()

cur.close()
conn.close()
