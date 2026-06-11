import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from engine import optimizar_canasta

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "message": "Backend conectado con éxito"}), 200

@app.route('/api/planificar', methods=['POST'])
def planificar():
    data = request.get_json() or {}
    
    objetivo = data.get("objetivo", "bajar_grasa")
    user_lat = float(data.get("lat", -33.4126))
    user_lng = float(data.get("lng", -70.6018))
    
    # Llamamos al módulo optimizador
    resultado = optimizar_canasta(objetivo, user_lat, user_lng)
    
    return jsonify(resultado), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)