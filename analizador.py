import os
import sqlite3
from datetime import datetime
from google.cloud import vision

# Ruta al JSON de credenciales
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'hackaton-segiridad-500d3a7a5a64.json'


# ------------------ BASE DE DATOS ------------------ #

DB_PATH = "alertas.db"

def init_db():
    """Crea la base de datos y la tabla si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            imagen TEXT NOT NULL,
            objeto TEXT NOT NULL,
            confianza REAL NOT NULL,
            x1 REAL,
            y1 REAL,
            x2 REAL,
            y2 REAL
        )
    """)
    conn.commit()
    conn.close()

def guardar_alerta(imagen, objeto, confianza, x1, y1, x2, y2):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alertas (fecha_hora, imagen, objeto, confianza, x1, y1, x2, y2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        imagen,
        objeto,
        confianza,
        x1, y1, x2, y2
    ))
    conn.commit()
    conn.close()

# ------------------ ANÁLISIS DE IMÁGENES ------------------ #
def detectar_amenazas(ruta_imagen):
    """Detecta personas, armas y objetos peligrosos en una imagen."""

    cliente = vision.ImageAnnotatorClient()

    with open(ruta_imagen, 'rb') as f:
        content = f.read()

    image = vision.Image(content=content)

    # Detección de objetos (ARMAS / PERSONAS)
    respuesta = cliente.object_localization(image=image)

    print("\n--- RESULTADOS DEL OJO DE DIOS ---")

    alerta = False

    # Lista de objetos peligrosos que queremos detectar
    OBJETOS_PELIGROSOS = ["gun", "knife", "weapon", "firearm", "rifle"]

    for obj in respuesta.localized_object_annotations:
        nombre = obj.name.lower()

        # (A) Si detecta persona (informativo)
        if "person" in nombre:
            print(f"[OK] Persona detectada (confianza: {obj.score:.2f})")

        # (B) Si detecta un arma (ALERTA)
        for peligro in OBJETOS_PELIGROSOS:
            if peligro in nombre:
                alerta = True
                score = obj.score
                box = obj.bounding_poly.normalized_vertices
                x1, y1 = box[0].x, box[0].y
                x2, y2 = box[2].x, box[2].y

                print(f"\n🚨 ALERTA PELIGROSA (ARMA) 🚨")
                print(f"Objeto detectado: {nombre.upper()}")
                print(f"Confianza: {score:.2f}")
                print(f"Coordenadas: {x1:.2f},{y1:.2f} → {x2:.2f},{y2:.2f}")
                print("----------------------------------")

                # Guarda arma en la BD (como antes)
                guardar_alerta(
                    imagen=ruta_imagen,
                    objeto=nombre,
                    confianza=score,
                    x1=x1, y1=y1, x2=x2, y2=y2
                )

    # ================================
    # 🔥 NUEVO: DETECCIÓN DE INCENDIO
    # ================================
    PATRONES_INCENDIO = [
        "fire", "flames", "flame", "smoke",
        "wildfire", "conflagration", "explosion", "burning"
    ]

    resp_labels = cliente.label_detection(image=image)

    for label in resp_labels.label_annotations:
        desc = label.description.lower()
        score = label.score

        # Ignoramos etiquetas con baja confianza
        if score < 0.70:
            continue

        for palabra in PATRONES_INCENDIO:
            if palabra in desc:
                alerta = True
                print(f"\n🔥🚨 ALERTA DE INCENDIO 🚨🔥")
                print(f"Etiqueta detectada: {desc.upper()}")
                print(f"Confianza: {score:.2f}")
                print("----------------------------------")

                # No hay bounding box, guardamos coordenadas como None
                guardar_alerta(
                    imagen=ruta_imagen,
                    objeto=f"incendio:{desc}",
                    confianza=score,
                    x1=None, y1=None, x2=None, y2=None
                )
                # Para no repetir la misma etiqueta muchas veces
                break

    # Mensaje final (NO lo toqué, solo amplía la condición)
    if alerta:
        print("\n🔥 *** ALERTA ROJA: AMENAZA DETECTADA (ARMA Y/O INCENDIO) *** 🔥\n")
    else:
        print("\n✔️ Imagen analizada: No se detectaron amenazas.\n")



if __name__ == "__main__":
    init_db()
    detectar_amenazas("pruebaimg.jpeg")


