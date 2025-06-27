from flask import Flask,jsonify
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) #Pozwala reactowi łączyć się lokalnie 

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Siema z backendu!"})

if __name__ == "__main__":
    app.run(debug=True)