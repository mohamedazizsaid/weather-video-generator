import streamlit as st
import pandas as pd
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
import tempfile
import os
import gc

# --- Configuration initiale ---
st.set_page_config(page_title="Générateur de Vidéo Météo Multilingue", layout="wide")
st.title("🌤️ Générateur de Vidéo Météo Multilingue")

# --- Constantes ---
LANGUAGES = {
    "fr": "Français",
    "ar": "Arabe"
}

# --- Fonctions utilitaires ---
def validate_temperature(temp):
    """Valide que la température est un nombre valide entre -100 et 100."""
    try:
        temp = float(temp)
        return -100 <= temp <= 100
    except ValueError:
        return False

def generate_weather_text(data, language):
    """Génère le texte pour la voix et l'affichage selon la langue."""
    text_dict = {
        "fr": {
            "voice": lambda d: f"Prévisions météo pour {d['Ville']}. Temps {d['Condition']}, maximum {d['Max']} degrés, minimum {d['Min']} degrés.",
            "display": lambda d: f"{d['Ville']} - {d['Condition']}\nMax: {d['Max']}°C | Min: {d['Min']}°C"
        },
        "ar": {
            "voice": lambda d: f"توقعات الطقس لمدينة {d['Ville']}. الطقس {d['Condition']}, درجة الحرارة العظمى {d['Max']}، والصغرى {d['Min']}.",
            "display": lambda d: f"{d['Ville']} - {d['Condition']}\nالعظمى: {d['Max']}°C | الصغرى: {d['Min']}°C"
        }
    }
    voice_text = "\n".join(text_dict[language]["voice"](meteo) for meteo in data)
    display_texts = [text_dict[language]["display"](meteo) for meteo in data]
    return voice_text, display_texts

def create_text_clip(text, style_params, bg_size, duration):
    """Crée un clip texte avec animation."""
    txt_clip = TextClip(
        text,
        fontsize=style_params["fontsize"],
        font=style_params["font"],
        color=style_params["color"],
        method='caption',
        size=(bg_size[0] * 0.8, None)
    ).set_position("center").set_duration(duration)

    if style_params["animation"] == "fadein":
        txt_clip = txt_clip.fadein(1)
    elif style_params["animation"] == "slide":
        txt_clip = txt_clip.set_position(lambda t: (int(bg_size[0] * (1 - t / duration)), 'center'))
    
    return txt_clip

# --- Interface Streamlit ---
with st.sidebar:
    st.header("Paramètres")
    
    # Choix de la langue
    language = st.selectbox("Langue de la voix", options=LANGUAGES.keys(), format_func=lambda x: LANGUAGES[x])
    
    # Paramètres de style
    st.subheader("Style de la vidéo")
    style_params = {
        "font": st.selectbox("Police", ["Arial", "Courier", "Times New Roman", "Verdana"]),
        "color": st.color_picker("Couleur du texte", "#FFFFFF"),
        "fontsize": st.slider("Taille de la police", 30, 100, 50),
        "duration": st.slider("Durée par ville (s)", 3, 15, 6),
        "animation": st.selectbox("Animation du texte", ["fadein", "slide", "none"]),
        "transition": st.selectbox("Transition entre villes", ["fondu", "aucune"])
    }

# --- Choix de la source des données ---
st.header("Données météo")
mode = st.radio("Entrer les données météo par :", ["Fichier CSV", "Saisie manuelle"])

data = []
if mode == "Fichier CSV":
    fichier_csv = st.file_uploader("Téléverser un fichier CSV", type=["csv"])
    if fichier_csv is not None:
        try:
            df = pd.read_csv(fichier_csv)
            required_columns = ["Ville", "Condition", "Max", "Min"]
            if not all(col in df.columns for col in required_columns):
                st.error("Le fichier CSV doit contenir les colonnes : Ville, Condition, Max, Min")
            else:
                df["Max"] = df["Max"].astype(str)
                df["Min"] = df["Min"].astype(str)
                if not all(df["Max"].apply(validate_temperature) & df["Min"].apply(validate_temperature)):
                    st.error("Les températures doivent être des nombres valides entre -100 et 100.")
                else:
                    st.write(df)
                    data = df.to_dict(orient="records")
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
else:
    with st.form("manual_input"):
        nb_villes = st.number_input("Nombre de villes", min_value=1, max_value=10, step=1)
        for i in range(nb_villes):
            st.markdown(f"**Ville #{i+1}**")
            cols = st.columns(4)
            with cols[0]:
                ville = st.text_input(f"Ville", key=f"ville_{i}")
            with cols[1]:
                condition = st.text_input(f"Condition", key=f"condition_{i}")
            with cols[2]:
                max_temp = st.text_input(f"Max (°C)", key=f"max_{i}")
            with cols[3]:
                min_temp = st.text_input(f"Min (°C)", key=f"min_{i}")

            if ville and condition and max_temp and min_temp:
                if not (validate_temperature(max_temp) and validate_temperature(min_temp)):
                    st.warning(f"Les températures pour {ville} doivent être des nombres valides entre -100 et 100.")
                else:
                    data.append({"Ville": ville, "Condition": condition, "Max": max_temp, "Min": min_temp})
        submit = st.form_submit_button("Valider les données")

# --- Fond ---
st.header("Fond de la vidéo")
background_file = st.file_uploader("Fond (image ou vidéo)", type=["mp4", "jpg", "png"])

# --- Génération de la vidéo ---
if st.button("Générer la vidéo", disabled=not (data and background_file)):
    if not data:
        st.error("Veuillez entrer des données météo valides.")
    elif not background_file:
        st.error("Veuillez uploader un fichier de fond.")
    else:
        with st.spinner("Génération de la vidéo en cours..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Génération du texte
                    voice_text, display_texts = generate_weather_text(data, language)
                    
                    # Génération de la voix avec NamedTemporaryFile
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
                        audio_path = audio_file.name
                        tts = gTTS(voice_text, lang=language)
                        tts.save(audio_path)
                    
                    # Préparation du fond
                    bg_path = os.path.join(tmpdir, background_file.name)
                    with open(bg_path, "wb") as f:
                        f.write(background_file.read())

                    if background_file.name.endswith(".mp4"):
                        clip_bg = VideoFileClip(bg_path).resize(height=720)
                    else:
                        clip_bg = ImageClip(bg_path).set_duration(style_params["duration"] * len(data)).resize(height=720)

                    # Création des clips pour chaque ville
                    clips = []
                    for i, (meteo, txt) in enumerate(zip(data, display_texts)):
                        txt_clip = create_text_clip(txt, style_params, (clip_bg.w, clip_bg.h), style_params["duration"])
                        if isinstance(clip_bg, VideoFileClip):
                            scene_bg = clip_bg.subclip(0, style_params["duration"]).set_duration(style_params["duration"])
                        else:
                            scene_bg = clip_bg.set_duration(style_params["duration"])
                        scene = CompositeVideoClip([scene_bg, txt_clip])
                        
                        if style_params["transition"] == "fondu" and i < len(data) - 1:
                            scene = scene.crossfadeout(1)
                        
                        clips.append(scene)

                    # Concaténation et ajout de l'audio
                    final_clip = concatenate_videoclips(clips, method="compose")
                    audio = AudioFileClip(audio_path)
                    final_clip = final_clip.set_audio(audio)
                    
                    output_path = os.path.join(tmpdir, "video_finale.mp4")
                    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

                    # Affichage de la vidéo
                    st.success("Vidéo générée avec succès !")
                    st.video(output_path)

                    # Option de téléchargement
                    with open(output_path, "rb") as f:
                        st.download_button("Télécharger la vidéo", f, file_name="video_meteo.mp4")

            except Exception as e:
                st.error(f"Erreur lors de la génération de la vidéo : {e}")
            finally:
                # Nettoyage explicite
                if 'final_clip' in locals():
                    final_clip.close()
                if 'clip_bg' in locals():
                    clip_bg.close()
                if 'audio' in locals():
                    audio.close()
                # Suppression manuelle du fichier audio
                try:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                except PermissionError:
                    st.warning("Le fichier audio est encore verrouillé. Il sera supprimé lors de la fermeture du programme.")
                gc.collect()  # Forcer le garbage collector