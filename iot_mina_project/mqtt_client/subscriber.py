import paho.mqtt.client as mqtt
import json, time
import ssl
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MQTT_TOPIC   = "mina/zona_perforacion/#"
AWS_ENDPOINT = "a2apsmaa0mdv52-ats.iot.us-east-1.amazonaws.com"
AWS_PORT     = 8883
CERTS_PATH   = "/app/certs"
CA_CERT      = f"{CERTS_PATH}/AmazonRootCA1 (2).pem"
CERT_FILE    = f"{CERTS_PATH}/0f5f9f5a67b470a0c1d7dfd00e79c39bca1c7d5dabffb6958d1db1a7377b3387-certificate.pem.crt"
KEY_FILE     = f"{CERTS_PATH}/0f5f9f5a67b470a0c1d7dfd00e79c39bca1c7d5dabffb6958d1db1a7377b3387-private.pem.key"




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
coleccion = mongo["mineria_iot"]["lecturas"]


def extraer_zona(topic):
    partes = topic.split("/")
    if len(partes) >= 3:
        return partes[1]
    return "desconocida"

def on_message(client, userdata, msg):
    try:
        receive_time = time.time()
        data = json.loads(msg.payload.decode())
        if "publish_time" in data:
            data["latency_ms"] = round((receive_time - data["publish_time"]) * 1000, 2)
        data["zona"] = data.get("zona") or extraer_zona(msg.topic)
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data["topic"] = msg.topic
        data["qos"] = msg.qos
        coleccion.insert_one(data)
        print(f"Guardado en MongoDB: {data}")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado a AWS IoT Core | Subscribiendo a: {MQTT_TOPIC}", flush=True)
        client.subscribe(MQTT_TOPIC, qos=1)
    else:
        print(f"Error de conexion: {rc}")

client = mqtt.Client(client_id="subscriber_perforacion")
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(ca_certs=CA_CERT, certfile=CERT_FILE, keyfile=KEY_FILE,
               tls_version=ssl.PROTOCOL_TLSv1_2)
client.connect(AWS_ENDPOINT, AWS_PORT)
client.loop_forever()