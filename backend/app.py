import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Vital para que React pueda comunicarse desde el otro servidor

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "message": "Backend conectado con éxito"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)