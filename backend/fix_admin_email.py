import sqlite3

conn = sqlite3.connect('./data/wms_client_ready.sqlite3')
conn.row_factory = sqlite3.Row

conn.execute("UPDATE users SET email = 'admin@whitfieldwms.com' WHERE email = 'admin@whitfield.local'")
conn.commit()

print("Updated rows. Current users:")
rows = conn.execute("SELECT email, role FROM users").fetchall()
for r in rows:
    print(dict(r))

conn.close()
