import sqlite3
conn = sqlite3.connect('turd_news.db')
c = conn.cursor()

# Try user_watchlists table
table_name = 'user_watchlists'
try:
    c.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = c.fetchone()[0]
    print(f"Table {table_name}: {count} rows")
    c.execute(f'DELETE FROM {table_name}')
    conn.commit()
    print(f"Deleted all from {table_name}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
print("Done!")
