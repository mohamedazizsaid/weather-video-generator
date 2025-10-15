from flask import Flask, render_template, redirect, url_for
import pymysql
from generate_video import main as generate_video

app = Flask(__name__)

# Configuration MySQL
db_config = {
    'host': 'localhost',
    'user': 'flask_user',
    'password': 'FlaskPass!2025',
    'database': 'meteo',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Fonction pour récupérer les données météo
def get_weather_data():
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM donnees_meteo")
            data = cursor.fetchall()
        return data
    except pymysql.MySQLError as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# Route principale
@app.route('/')
def index():
    try:
        weather = get_weather_data()
        return render_template('index.html', weather=weather)
    except Exception as e:
        print(f"Erreur lors du rendu de la page : {e}")
        return render_template('index.html', weather=[], error="Impossible de charger les données météo.")

# Route pour générer la vidéo
@app.route('/generer_video')
def generer_video_route():
    try:
        generate_video()
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Erreur lors de la génération de la vidéo : {e}")
        return render_template('index.html', weather=get_weather_data(), error="Erreur lors de la génération de la vidéo.")

# Lancement de l'application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)