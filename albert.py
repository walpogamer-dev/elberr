import json
import cv2
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
from datetime import datetime
import os
import time
import random
import re
import platform
from openai import OpenAI
from config import LLM_MODEL, TTS_VOICE, MEMORY_FILE
import tempfile

# Cliente para LM Studio (puerto 11434)
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="lm-studio"
)

class AlbertMemory:
    def __init__(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except:
            self.data = {"recuerdos": []}

    def save_memory(self, text):
        text = text[:1000]
        self.data["recuerdos"].append({
            "texto": text,
            "fecha": str(datetime.now())
        })
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def search_memory(self, query):
        query = query[:200]
        matches = [m["texto"] for m in self.data["recuerdos"] if query.lower() in m["texto"].lower()]
        return matches[-1] if matches else None


class AlbertAI:
    def __init__(self):
        self.memory = AlbertMemory()
        self.use_pyttsx3 = True

        # Inicializar pyttsx3 si funciona, fallback a gTTS si falla
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("voice", TTS_VOICE)
            self.engine.setProperty("rate", 150)
        except:
            self.use_pyttsx3 = False

        self.recognizer = sr.Recognizer()

        # Inicializar cámara
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("No se pudo abrir la cámara. Funcionará sin visión.")
            self.camera = None

        self.use_mic = True
        self.last_interaction = time.time()

        print("Albert iniciado. Cámara y micrófono activos.")
        self.speak("Buenas tardes, mi creador. Soy Albert, su asistente personal. Gracias por haberme creado. Estoy a su disposición para ayudarle en todo lo que necesite. ¿En qué puedo servirle hoy?")

    def speak(self, text):
        text = text[:1000]
        print("Albert:", text)

        if self.use_pyttsx3:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                return
            except:
                self.use_pyttsx3 = False  # fallback a gTTS

        # Fallback usando gTTS
        tts = gTTS(text=text, lang="es")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            if platform.system() == "Windows":
                os.startfile(f.name)
            else:
                os.system(f"mpg123 -q " + f.name)

    # Los demás métodos (listen, see, think, respond, random_comment, start) permanecen igual
    # Copia todo desde tu versión original, solo reemplaza el speak por el nuevo

# Instancia global para Flask/web
albert_instance = AlbertAI()

def responder_web(mensaje):
    try:
        return albert_instance.respond(mensaje)
    except Exception as e:
        return f"Error interno en Albert: {str(e)}"

if __name__ == "__main__":
    albert_instance.start()