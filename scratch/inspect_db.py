import sqlite3

conn = sqlite3.connect('data/egx.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for t in tables:
    print(f'\n--- {t[0]} ---')
    for row in conn.execute(f'PRAGMA table_info({t[0]})').fetchall():
        print(row)

cursor2 = conn.execute('SELECT COUNT(*) FROM disclosures')
print(f'\nTotal disclosures: {cursor2.fetchone()[0]}')

cursor3 = conn.execute('SELECT COUNT(*) FROM disclosures WHERE pdf_url IS NOT NULL')
print(f'With PDFs: {cursor3.fetchone()[0]}')

# Sample data
print('\n--- Sample rows ---')
for row in conn.execute('SELECT id, article_url, title, pdf_url, published_at FROM disclosures LIMIT 5').fetchall():
    print(row)

conn.close()
