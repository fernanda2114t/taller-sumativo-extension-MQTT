from flask import Flask, jsonify, Response
import time
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime, timedelta

app = Flask(__name__)

latencia_gauge  = Gauge("mina_latencia_ms",       "Latencia promedio de transmision en ms")
frecuencia_gauge = Gauge("mina_frecuencia_por_min", "Mensajes recibidos en el ultimo minuto")


def conectar_mongo(reintentos=10, espera=3):
    for intento in range(1, reintentos + 1):
        try:
            cliente = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=3000)
            cliente.admin.command("ping")
            print("Conectado a MongoDB", flush=True)
            return cliente
        except ConnectionFailure:
            print(f"MongoDB no disponible, reintento {intento}/{reintentos}...", flush=True)
            time.sleep(espera)
    raise RuntimeError("No se pudo conectar a MongoDB tras varios intentos")


mongo     = conectar_mongo()
coleccion = mongo["mineria_iot"]["lecturas"]


def obtener_lecturas(nombre, limite=20):
    return list(
        coleccion.find({"sensor": nombre}, {"_id": 0})
                 .sort("timestamp", DESCENDING)
                 .limit(limite)
    )


def obtener_zonas():
    return sorted([z for z in coleccion.distinct("zona") if z])


@app.route("/zonas")
@app.route("/zones")
def zonas():
    try:
        return jsonify(obtener_zonas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logs/sensor/<nombre>")
def logs(nombre):
    try:
        return jsonify(obtener_lecturas(nombre))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/metrics")
def metrics():
    # Latencia promedio de los ultimos 20 mensajes
    docs = list(coleccion.find(
        {"latency_ms": {"$exists": True}}, {"_id": 0, "latency_ms": 1}
    ).sort("timestamp", DESCENDING).limit(20))
    if docs:
        latencia_gauge.set(round(sum(d["latency_ms"] for d in docs) / len(docs), 2))

    # Frecuencia: mensajes recibidos en el ultimo minuto
    hace_un_minuto = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    frecuencia_gauge.set(coleccion.count_documents({"timestamp": {"$gte": hace_un_minuto}}))

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
