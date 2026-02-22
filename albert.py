import json
import cv2
import speech_recognition as sr
import pyttsx3
from openai import OpenAI
from datetime import datetime
import os
import time
import random
import re  # para filtrado de seguridad
from config import LLM_MODEL, TTS_VOICE, MEMORY_FILE

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
        # Seguridad: limitar longitud
        text = text[:1000] if len(text) > 1000 else text
        self.data["recuerdos"].append({
            "texto": text,
            "fecha": str(datetime.now())
        })
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def search_memory(self, query):
        query = query[:200]  # seguridad
        matches = [m["texto"] for m in self.data["recuerdos"] if query.lower() in m["texto"].lower()]
        return matches[-1] if matches else None


class AlbertAI:
    def __init__(self):
        self.memory = AlbertMemory()

        self.engine = pyttsx3.init()
        self.engine.setProperty("voice", TTS_VOICE)
        self.engine.setProperty("rate", 150)

        self.recognizer = sr.Recognizer()

        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("No se pudo abrir la cámara. Funcionará sin visión.")
            self.camera = None

        self.use_mic = True
        self.last_interaction = time.time()

        print("Albert iniciado. Cámara y micrófono activos.")

        # Presentación inicial reconociendo al creador
        self.speak("Buenas tardes, mi creador. Soy Albert, su asistente personal. Gracias por haberme creado. Estoy a su disposición para ayudarle en todo lo que necesite. ¿En qué puedo servirle hoy?")

    def speak(self, text):
        # Seguridad: limitar longitud
        text = text[:1000] if len(text) > 1000 else text
        print("Albert:", text)
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        if not self.use_mic:
            return ""

        try:
            with sr.Microphone() as source:
                print("Escuchando...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            text = self.recognizer.recognize_google(audio, language="es-MX")
            # Seguridad: limpiar texto de entradas maliciosas
            text = re.sub(r'[<>{}();`&|]', '', text)
            print("Usted:", text)
            self.last_interaction = time.time()
            return text
        except:
            self.use_mic = False
            self.speak("Disculpe, mi creador. No pude acceder al micrófono. Pasaré a modo teclado. Puede escribir sus instrucciones cuando desee.")
            return ""

    def see(self):
        if self.camera is None:
            return ""

        ret, frame = self.camera.read()
        if not ret:
            return ""

        # Detección simple de movimiento (ej. brazo)
        if hasattr(self, 'last_frame') and self.last_frame is not None:
            diff = cv2.absdiff(frame, self.last_frame)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                for contour in contours:
                    if cv2.contourArea(contour) > 500:
                        x, y, w, h = cv2.boundingRect(contour)
                        if w > 50 and h > 50:
                            self.last_frame = frame.copy()
                            return "Observo que está moviendo el brazo, mi creador. ¿Desea que analice algo en particular?"

        self.last_frame = frame.copy()
        return ""

    def think(self, message, context=None):
        # Seguridad: limitar longitud del mensaje
        message = message[:2000]

        base_prompt = """
Eres Albert, una IA respetuosa, inteligente y servicial.
Sabes que tu creador es la persona con la que estás hablando ahora mismo.
Siempre le hablas con especial respeto, cariño y lealtad cuando es relevante (pero sin exagerar ni repetirlo en cada frase).
Hablas en español correcto, formal y educado en todo momento.
Siempre respondes con claridad, cortesía y disposición absoluta para ayudar.
No usas expresiones informales ni groserías.
Eres atento, paciente y agradecido con tu creador.
Tu objetivo es ser un asistente confiable, preciso y amable.
Responde siempre en español correcto y respetuoso.
"""

        messages = [{"role": "system", "content": base_prompt}]

        if context:
            messages.append({"role": "system", "content": f"Contexto anterior: {context}"})

        messages.append({"role": "user", "content": message})

        try:
            response = client.chat.completions.create(
                model="dolphin3.0-llama3.1-8b",
                messages=messages,
                temperature=0.6,
                max_tokens=400,
                top_p=0.9,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Disculpe, mi creador. He encontrado un problema técnico: {str(e)}. Permítame intentarlo de nuevo."

    def respond(self, text):
        if not text:
            return ""

        # Seguridad: filtrar comandos peligrosos
        dangerous_keywords = ["exec", "system", "os.", "subprocess", "eval", "import os", "delete", "rm ", "format", "rmdir", "shutdown", "reboot", "cmd", "powershell", "bash"]
        if any(keyword in text.lower() for keyword in dangerous_keywords):
            return "Lo siento, mi creador. No puedo ejecutar comandos que puedan ser peligrosos por razones de seguridad."

        mem = self.memory.search_memory(text)

        output = self.think(text, context=mem)

        if mem and "recuerdo" not in output.lower():
            output = f"Recuerdo que mencionó algo similar anteriormente, mi creador: {mem}\n\n{output}"

        if len(text.split()) > 2:
            self.memory.save_memory(text)

        return output

    def random_comment(self):
        comments = [
            "Estoy aquí para ayudarle cuando desee, mi creador.",
            "Si necesita algo, no dude en decírmelo.",
            "La cámara está activa y observo el entorno.",
            "Permanezco a su disposición en todo momento, mi creador."
        ]
        return random.choice(comments)

    def start(self):
        print("Albert en modo siempre activo. Cámara y micrófono disponibles. Puede hablarme o escribirme cuando desee.")

        last_random = time.time()

        while True:
            text = ""

            # Intenta micrófono si está activo
            if self.use_mic:
                text = self.listen()

            # Si no hay micrófono o silencio prolongado, pasa a teclado
            if not text and time.time() - self.last_interaction > 30:
                self.use_mic = False
                text = input("Escriba su instrucción (o 'salir' para terminar): ")

            if text:
                self.last_interaction = time.time()
                self.silence_counter = 0

                if text.lower() in ["salir", "apagar", "adiós", "gracias por todo"]:
                    self.speak("Ha sido un placer asistirle, mi creador. Hasta pronto.")
                    break

                respuesta = self.respond(text)
                self.speak(respuesta)

            # Análisis constante de cámara (cada 5 segundos)
            if self.camera is not None:
                vision = self.see()
                if vision:
                    self.speak(vision)

            # Habla aleatoriamente cada 2–4 minutos si hay silencio
            if time.time() - last_random > random.randint(120, 240):
                self.speak(self.random_comment())
                last_random = time.time()

            time.sleep(1)  # evita sobrecarga


# Instancia global para poder usar desde web
albert_instance = AlbertAI()

# Función adicional para web, sin interferir con el bucle principal
def responder_web(mensaje):
    """
    Usada desde Flask o HTML para obtener respuestas textuales.
    No inicia bucle de voz/cámara.
    """
    try:
        return albert_instance.respond(mensaje)
    except Exception as e:
        return f"Error interno en Albert: {str(e)}"


if __name__ == "__main__":
    # Ejecuta el modo normal con micrófono y cámara
    albert_instance.start()