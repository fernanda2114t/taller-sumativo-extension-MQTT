import paho.mqtt.client as mqtt
import time, random, os, json

sensor_id = os.getenv("SENSOR_ID", "0")
zona = os.getenv("ZONA", "general")
topic = f"campo/{zona}/sensores"

client = mqtt.Client(client_id=f"sensor-{zona}-{sensor_id}")
client.connect("mqtt", 1883, 60)
client.loop_start()

while True:
    data = {
        "sensor_id": sensor_id,
        "zona": zona,
        "temperatura": round(random.uniform(10, 35), 2),
        "humedad": round(random.uniform(30, 90), 2)
    }

    if random.random() > 0.2:
        publicacion = client.publish(topic, json.dumps(data), qos=1)
        publicacion.wait_for_publish()
        print(f"Enviado a {topic}:", data)
    else:
        print(f"[Sensor {sensor_id}] Fallo de red simulado — mensaje no enviado")

    time.sleep(3)
