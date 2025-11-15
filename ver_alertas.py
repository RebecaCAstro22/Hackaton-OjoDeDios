import sqlite3

# Abrir la base de datos
conn = sqlite3.connect("alertas.db")
cur = conn.cursor()

# Leer todas las alertas ordenadas por ID (últimas primero)
cur.execute("SELECT * FROM alertas ORDER BY id DESC")

alertas = cur.fetchall()

print("\n=== ALERTAS REGISTRADAS ===\n")

if len(alertas) == 0:
    print("No hay alertas guardadas aún.")
else:
    for alerta in alertas:
        print(alerta)

conn.close()
