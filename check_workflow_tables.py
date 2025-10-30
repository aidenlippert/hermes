import sqlite3

conn = sqlite3.connect('c:/Users/aiden/hermes/hermes_dev.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "workflow%" ORDER BY name')
tables = cursor.fetchall()

print('\n📊 Workflow Tables in Database:')
print('=' * 50)
if tables:
    for t in tables:
        print(f'  ✅ {t[0]}')
    print(f'\n✅ Found {len(tables)} workflow table(s)!')
else:
    print('  ❌ No workflow tables found')

# Check all tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
all_tables = cursor.fetchall()
print(f'\n📋 All Tables ({len(all_tables)} total):')
print('=' * 50)
for t in all_tables:
    print(f'  • {t[0]}')

conn.close()
