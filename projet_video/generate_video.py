import os
import pymysql
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# Configurations
BACKGROUND_VIDEO_PATH = "static/nuage.mp4"
FONT_PATH = "static/fonts/Amiri-Regular.ttf"
OUTPUT_VIDEO_PATH = "static/meteo_video.mp4"
FONT_SIZE = 24
VIDEO_DURATION = 5  # Durée de chaque segment en secondes
CITY_POSITIONS = [
    ("القيروان", (100, 100)),
    ("تونس", (300, 100)),
    ("نابل", (500, 100)),
    ("زغوان", (700, 100)),
]

def fetch_weather_data():
    """Récupère les données météo depuis la base de données."""
    try:
        conn = pymysql.connect(
            host='localhost',
            user='flask_user',
            password='FlaskPass!2025',
            database='meteo',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor  # Utilisation de DictCursor pour des résultats plus lisibles
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT ville, temp_min, temp_max, icone FROM donnees_meteo")
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def create_video_clips(weather_data):
    """Crée des clips vidéo avec les données météo superposées."""
    if not os.path.exists(BACKGROUND_VIDEO_PATH):
        print(f"Erreur : La vidéo de fond '{BACKGROUND_VIDEO_PATH}' n'existe pas.")
        return []

    try:
        background_clip = VideoFileClip(BACKGROUND_VIDEO_PATH)
        clips = []

        for step in range(1, len(CITY_POSITIONS) + 1):
            current_clip = background_clip.subclip(0, VIDEO_DURATION)
            overlays = [current_clip]

            for i in range(step):
                city_name, (x, y) = CITY_POSITIONS[i]
                city_data = next((entry for entry in weather_data if entry['ville'] == city_name), None)
                if not city_data:
                    print(f"Aucune donnée trouvée pour la ville : {city_name}")
                    continue

                # Formatage du texte en arabe
                city = get_display(reshape(f"المدينة: {city_data['ville']}"))
                min_temp = get_display(reshape(f"↓ {city_data['temp_min']}°C"))
                max_temp = get_display(reshape(f"↑ {city_data['temp_max']}°C"))
                weather = get_display(reshape(str(city_data['icone'])))

                text = f"{city}\n{min_temp}\n{max_temp}\n{weather}"

                try:
                    text_clip = TextClip(
                        text,
                        fontsize=FONT_SIZE,
                        font=FONT_PATH,
                        color='white',
                        bg_color='rgba(0, 0, 0, 0.6)',  # Fond semi-transparent
                        size=(220, None),
                        method='caption',
                        align='center'
                    ).set_position((x, y)).set_duration(VIDEO_DURATION)
                    overlays.append(text_clip)
                except Exception as e:
                    print(f"Erreur lors de la création du clip texte pour {city_name} : {e}")
                    continue

            composite = CompositeVideoClip(overlays)
            clips.append(composite)

        background_clip.close()  # Fermer la vidéo de fond pour libérer la mémoire
        return clips

    except Exception as e:
        print(f"Erreur lors de la création des clips vidéo : {e}")
        if 'background_clip' in locals():
            background_clip.close()
        return []

def main():
    """Génère la vidéo météo complète."""
    if not os.path.exists(FONT_PATH):
        print(f"Erreur : La police '{FONT_PATH}' n'existe pas.")
        return

    data = fetch_weather_data()
    if not data:
        print("Erreur : Aucune donnée météo disponible.")
        return

    video_clips = create_video_clips(data)
    if not video_clips:
        print("Erreur : Aucun clip vidéo n'a été créé.")
        return

    try:
        final_clip = concatenate_videoclips(video_clips, method="compose")
        final_clip.write_videofile(
            OUTPUT_VIDEO_PATH,
            codec="libx264",
            fps=24,
            audio=False,  # Pas d'audio pour simplifier
            threads=4,    # Utilisation de plusieurs cœurs
            preset="medium"  # Équilibre entre vitesse et qualité
        )
        print(f"🎉 Vidéo créée avec succès : {OUTPUT_VIDEO_PATH}")
    except Exception as e:
        print(f"Erreur lors de la génération de la vidéo finale : {e}")
    finally:
        if 'final_clip' in locals():
            final_clip.close()
        for clip in video_clips:
            clip.close()

if __name__ == "__main__":
    main()