import paho.mqtt.client as mqtt
import json
import time
import random
import ssl

AWS_ENDPOINT = "a2apsmaa0mdv52-ats.iot.us-east-1.amazonaws.com"
AWS_PORT = 8883
TOPIC = "mina/zona_perforacion/quimica"
CLIENT_ID = "sensor_SO2"

CERTS_PATH = "/app/certs"
CA_CERT   = f"{CERTS_PATH}/AmazonRootCA1 (2).pem"
CERT_FILE = f"{CERTS_PATH}/0f5f9f5a67b470a0c1d7dfd00e79c39bca1c7d5dabffb6958d1db1a7377b3387-certificate.pem.crt"
KEY_FILE  = f"{CERTS_PATH}/0f5f9f5a67b470a0c1d7dfd00e79c39bca1c7d5dabffb6958d1db1a7377b3387-private.pem.key"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado a AWS IoT Core | Topic: {TOPIC}", flush=True)
    else:
        print(f"Error de conexion: {rc}")

client = mqtt.Client(client_id=CLIENT_ID)
client.on_connect = on_connect
client.tls_set(ca_certs=CA_CERT, certfile=CERT_FILE, keyfile=KEY_FILE,
               tls_version=ssl.PROTOCOL_TLSv1_2)
client.connect(AWS_ENDPOINT, AWS_PORT)
client.loop_start()

try:
    while True:
        valor = round(random.uniform(0.5, 15.0), 2)
        mensaje = json.dumps({"sensor": "SO2", "valor": valor, "grupo": "zona_perforacion", "publish_time": time.time()})
        client.publish(TOPIC, mensaje)
        print(f"Publicado: {mensaje}", flush=True)
        time.sleep(3)
except KeyboardInterrupt:
    print("Detenido.")
    client.loop_stop()
    client.disconnect()
