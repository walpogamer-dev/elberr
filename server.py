from flask import Flask, request, jsonify, send_from_directory
from albert import AlbertAI

app = Flask(__name__)
albert = AlbertAI()  # instancia de tu IA

# Página HTML
@app.route("/")
def home():
    return send_from_directory(".", "pagina alberr.html")

# Endpoint de chat
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("message", "")
    respuesta = albert.responder_web(mensaje)  # usa el método web que agregamos
    return jsonify({"response": respuesta})

if __name__ == "__main__":
    app.run(debug=True)