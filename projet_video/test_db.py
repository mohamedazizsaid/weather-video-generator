import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',              # Ou 'flask_user' si tu l’as créé
        password='FlaskPass!2025',# Ton mot de passe
        database='meteo'          # Le nom correct de la base
    )
    print("✅ Connexion réussie avec mysql.connector !")
    conn.close()
except Exception as e:
    print("❌ Erreur de connexion :", e)
