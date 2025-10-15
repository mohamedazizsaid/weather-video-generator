import mysql.connector

# Connexion à la base MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="flask_user",          # ou ton utilisateur MySQL
    password='FlaskPass!2025',# ou votre mot de passe root
   
    database="meteo"      # ta base MySQL déjà créée
)

cursor = conn.cursor()

# Création de la table
cursor.execute("""
CREATE TABLE IF NOT EXISTS donnees_meteo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ville VARCHAR(100) NOT NULL,
    temp_min INT NOT NULL,
    temp_max INT NOT NULL,
    icone VARCHAR(10)
)
""")

# Vérifie si la table contient des données
cursor.execute("SELECT COUNT(*) FROM donnees_meteo")
count = cursor.fetchone()[0]

if count == 0:
    sample_data = [
        ("القيروان", 29, 41, "☀️"),
        ("تونس", 19, 28, "☁️🌧️"),
        ("نابل", 25, 41, "☀️"),
        ("زغوان", 26, 43, "⚪"),
        ("تونس", 19, 29, "🌬️"),
    ]

    cursor.executemany(
        "INSERT INTO donnees_meteo (ville, temp_min, temp_max, icone) VALUES (%s, %s, %s, %s)",
        sample_data
    )
    print("✅ Données insérées dans MySQL.")
else:
    print(f"ℹ️ {count} enregistrements déjà présents dans MySQL.")

conn.commit()
conn.close()
