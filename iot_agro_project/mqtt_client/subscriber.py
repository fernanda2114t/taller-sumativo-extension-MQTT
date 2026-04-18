import paho.mqtt.client as mqtt
import json, time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MQTT_TOPIC = "campo/+/sensores"

def conectar_mongo(reintentos=10, espera=3):
    for intento in range(1, reintentos + 1):
        try:
            cliente = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=3000)
            cliente.admin.command("ping")
            print("Conectado a MongoDB")
            return cliente
        except ConnectionFailure:
            print(f"MongoDB no disponible, reintento {intento}/{reintentos}...")
            time.sleep(espera)
    raise RuntimeError("No se pudo conectar a MongoDB tras varios intentos")

mongo = conectar_mongo()
coleccion = mongo["agro_iot"]["lecturas"]


def extraer_zona(topic):
    partes = topic.split("/")
    if len(partes) >= 3:
        return partes[1]
    return "desconocida"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        data["zona"] = data.get("zona") or extraer_zona(msg.topic)
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data["topic"] = msg.topic
        data["qos"] = msg.qos
        coleccion.insert_one(data)
        print(f"Guardado en MongoDB: {data}")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt", 1883, 60)
client.subscribe(MQTT_TOPIC, qos=1)
client.loop_forever()
