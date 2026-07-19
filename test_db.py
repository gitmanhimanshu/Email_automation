
import psycopg
from remote import config

with psycopg.connect(config.DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute('''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        ''')
        print([r[0] for r in cur.fetchall()])

