# Documento Técnico: Funcionamiento del Sistema IoT Agrícola

## 1. Visión general

El proyecto simula una red de sensores agrícolas organizada por zonas de cultivo. La arquitectura actual usa tres capas:

- Telemetría MQTT con topics jerárquicos por zona.
- Persistencia en MongoDB.
- Consulta vía REST API y visualización en Streamlit.

La extensión implementada agrega tres ideas principales:

1. QoS 1 en la publicación y suscripción MQTT.
2. Topics por zona con la forma `campo/<zona>/sensores`.
3. Wildcard MQTT `campo/+/sensores` para capturar todas las zonas desde un solo suscriptor.

---

## 2. Arquitectura

```text
[sensor1..3: tomate] ──┐
[sensor4..6: zanahoria] ├──► [Mosquitto :1883] ──► [subscriber] ──► [MongoDB :27017]
[sensor7..9: maiz] ────┘                                         │
                                                                  ▼
                                                         [rest_api :5000]
                                                                  │
                                                                  ▼
                                                         [frontend :8501]
```

Componentes:

| Servicio | Rol |
|---|---|
| `mqtt` | Broker Mosquitto para enrutar mensajes |
| `mongodb` | Persistencia de lecturas |
| `subscriber` | Consume MQTT y guarda documentos en MongoDB |
| `sensor1..9` | Simulan sensores distribuidos por zona |
| `rest_api` | Expone lecturas por zona vía HTTP |
| `frontend` | Dashboard Streamlit por zonas de cultivo |

---

## 3. MQTT en el proyecto

MQTT se usa para mover telemetría desde los sensores hacia el backend sin acoplar emisor y receptor. Cada sensor publica en un topic que incluye su zona:

- `campo/tomate/sensores`
- `campo/zanahoria/sensores`
- `campo/maiz/sensores`

### 3.1 Publicación en el sensor

Cada sensor:

- Lee `SENSOR_ID` y `ZONA` desde variables de entorno.
- Genera temperatura y humedad aleatorias.
- Publica un JSON con `qos=1`.
- Espera la confirmación de publicación con `wait_for_publish()`.

Ejemplo de payload:

```json
{
  "sensor_id": "1",
  "zona": "tomate",
  "temperatura": 22.45,
  "humedad": 67.83
}
```

### 3.2 Suscripción con wildcard

El suscriptor escucha:

```text
campo/+/sensores
```

El signo `+` permite recibir todos los topics de una sola zona intermedia. Esto evita crear un subscriber por cultivo.

Cuando llega un mensaje:

- Se decodifica el JSON.
- Se asegura el campo `zona`.
- Se agrega `timestamp`.
- Se inserta en MongoDB en `agro_iot.lecturas`.

### 3.3 QoS

El proyecto usa QoS 1 en publisher y subscriber.

| QoS | Garantía | Uso en este proyecto |
|---|---|---|
| 0 | Como máximo una vez | No |
| 1 | Al menos una vez | Sí |
| 2 | Exactamente una vez | No |

QoS 1 es razonable para telemetría agrícola porque reduce pérdidas sin imponer el costo de QoS 2.

---

## 4. MongoDB como persistencia

MongoDB reemplaza el enfoque anterior basado en un archivo de texto compartido. El subscriber guarda cada lectura como documento.

Base de datos: `agro_iot`

Colección: `lecturas`

Ejemplo de documento:

```json
{
  "sensor_id": "1",
  "zona": "tomate",
  "temperatura": 22.45,
  "humedad": 67.83,
  "timestamp": "2026-04-17 12:00:03"
}
```

La API consulta MongoDB ordenando por `timestamp` en orden descendente y limita la respuesta a 20 registros.

---

## 5. REST API

La API Flask expone la información para el frontend.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/zonas` | Devuelve las zonas disponibles |
| GET | `/logs` | Devuelve las últimas 20 lecturas globales |
| GET | `/logs/<zona>` | Devuelve las últimas 20 lecturas de una zona |

La API es stateless: cada consulta lee directamente MongoDB.

---

## 6. Frontend Streamlit

El dashboard consulta la API cuando el usuario presiona el botón **Actualizar**.

Flujo:

1. Consulta `/zonas`.
2. Crea una pestaña por zona.
3. Consulta `/logs/<zona>` para cada pestaña.
4. Muestra los datos en una tabla.

Las zonas por defecto son:

- tomate
- zanahoria
- maiz

---

## 7. Docker Compose

El archivo `docker-compose.yml` levanta:

- `mqtt`
- `mongodb`
- `subscriber`
- `sensor1` a `sensor9`
- `rest_api`
- `frontend`

Asignación de zonas:

- `sensor1`, `sensor2`, `sensor3` -> tomate
- `sensor4`, `sensor5`, `sensor6` -> zanahoria
- `sensor7`, `sensor8`, `sensor9` -> maiz

---

## 8. Ciclo de vida de un dato

1. Un sensor genera una lectura.
2. Publica el mensaje en `campo/<zona>/sensores` con QoS 1.
3. Mosquitto entrega el mensaje al suscriptor que escucha `campo/+/sensores`.
4. El suscriptor agrega `timestamp` y guarda la lectura en MongoDB.
5. La API consulta MongoDB y devuelve las últimas 20 lecturas.
6. El dashboard consulta la API y muestra los datos por zona.

---

## 9. Resultado de la extensión

Con esta extensión el proyecto deja de usar un topic único y pasa a una estructura más cercana a un despliegue real de IoT agrícola:

- mejor organización semántica de los datos,
- suscripción única para múltiples zonas,
- mayor confiabilidad en la entrega con QoS 1,
- visualización separada por cultivo,
- persistencia estructurada en MongoDB.
