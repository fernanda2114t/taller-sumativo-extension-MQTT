# IoT Agro Project

Demo de sensorización agrícola basado en **MQTT**, **MongoDB**, **REST API** y **Streamlit**. Simula nueve sensores de campo agrupados en tres zonas de cultivo, publica telemetría con QoS 1, la persiste en MongoDB y la muestra en un dashboard separado por zonas.

---

## Arquitectura

```
[sensor1..3: tomate] ──┐
      ├──► [Mosquitto MQTT :1883] ──► [subscriber] ──► [MongoDB :27017]
[sensor4..6: zanahoria] ┤                                                     │
[sensor7..9: maiz] ─────┘                                                     ▼
                    [rest_api :5000]
                      │
                      ▼
                     [frontend :8501]
```

| Servicio      | Tecnología         | Puerto |
|---------------|--------------------|--------|
| `mqtt`        | Eclipse Mosquitto  | 1883   |
| `mongodb`     | MongoDB 7.0        | 27017  |
| `rest_api`    | Flask              | 5000   |
| `subscriber`  | paho-mqtt + PyMongo| —      |
| `sensor1..9`  | paho-mqtt (Python) | —      |
| `frontend`    | Streamlit          | 8501   |

---

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0

Verificar instalación:

```bash
docker --version
docker compose version
```

---

## Estructura del proyecto

```
iot_agro_project/
├── docker-compose.yml
├── mosquitto.conf          # Configuración del broker MQTT
├── README.md
├── frontend/
│   ├── Dockerfile
│   └── app.py              # Dashboard Streamlit por zonas
├── mqtt_client/
│   ├── Dockerfile
│   └── subscriber.py       # Suscriptor MQTT → guarda en MongoDB
├── rest_api/
│   ├── Dockerfile
│   └── app.py              # API Flask GET /zonas y GET /logs/<zona>
└── sensors/
    ├── Dockerfile
    └── sensor.py           # Sensor simulado por zona de cultivo
```

---

## Instrucciones de ejecución

### 1. Clonar / posicionarse en el directorio

```bash
cd iot_agro_project
```

### 2. Construir y levantar todos los servicios

```bash
docker compose up --build
```

> La primera vez puede tardar varios minutos mientras se descargan las imágenes base y se instalan dependencias.

### 3. Verificar que los servicios están corriendo

```bash
docker compose ps
```

Deberías ver los 14 servicios con estado `Up` o `running`.

### 4. Abrir el dashboard

Abre el navegador en:

```
http://localhost:8501
```

Presiona el botón **"Actualizar"** para ver las pestañas por zona de cultivo con los últimos 20 registros recibidos.

### 5. Consultar la API directamente (opcional)

```bash
curl http://localhost:5000/zonas
curl http://localhost:5000/logs/tomate
```

Respuesta esperada: array JSON con documentos como:

```json
[
  {
    "sensor_id": "1",
    "zona": "tomate",
    "temperatura": 22.5,
    "humedad": 65.3,
    "timestamp": "2026-04-17 12:00:03"
  }
]
```

### 6. Ver logs de un servicio específico

```bash
# Logs del suscriptor MQTT
docker compose logs -f subscriber

# Logs de un sensor
docker compose logs -f sensor1

# Logs de la API
docker compose logs -f rest_api
```

### 7. Detener el proyecto

```bash
docker compose down
```

Para eliminar también el volumen de logs:

```bash
docker compose down -v
```

---

## Descripción de cada componente

### `sensors/sensor.py`
Simula un sensor de campo. Cada 3 segundos genera valores aleatorios de temperatura (10–35 °C) y humedad (30–90 %), construye el topic `campo/<zona>/sensores` y publica con QoS 1. Con un 20 % de probabilidad simula un fallo de red y omite el envío.

### `mqtt_client/subscriber.py`
Se suscribe al wildcard `campo/+/sensores`, extrae la zona desde el topic y guarda cada mensaje en MongoDB dentro de `agro_iot.lecturas`.

### `rest_api/app.py`
API Flask con estos endpoints:

| Método | Ruta    | Descripción                          |
|--------|---------|--------------------------------------|
| GET    | `/zonas` | Devuelve las zonas disponibles |
| GET    | `/logs` | Devuelve las últimas 20 lecturas globales |
| GET    | `/logs/<zona>` | Devuelve las últimas 20 lecturas de una zona |

### `frontend/app.py`
Dashboard Streamlit que consulta `GET /zonas` y `GET /logs/<zona>` al presionar el botón "Actualizar" y muestra las lecturas en pestañas por cultivo.

### `mosquitto.conf`
Configura el broker Mosquitto para escuchar en el puerto 1883 y permitir conexiones anónimas (adecuado para entorno de laboratorio).

---

## 📝 Cambios Aplicados en la Extensión MQTT

Esta sección detalla todas las modificaciones realizadas para implementar la extensión MQTT especificada en `h(4).pdf`.

### 1. **QoS 1 en Publicación (sensors/sensor.py)**

**Cambio:** Implementación de Quality of Service nivel 1 con confirmación de entrega.

```python
# Antes: Publicación sin QoS explícito
# Después:
publicacion = client.publish(topic, json.dumps(data), qos=1)
publicacion.wait_for_publish()  # Espera confirmación del broker
```

**Impacto:** Garantiza "al menos una entrega" de cada lectura semanal de sensores, evitando pérdida de datos críticos en la red.

---

### 2. **Topics Jerárquicos Dinámicos (sensors/sensor.py)**

**Cambio:** Construcción dinámica del topic basada en la zona del cultivo.

```python
# Antes: topic = "campo/sensores"
# Después:
zona = os.getenv("ZONA", "general")
topic = f"campo/{zona}/sensores"
```

**Impacto:** Permite organizar temas por zonas de cultivo (tomate, zanahoria, maíz), facilitando filtrado y análisis por cultivo.

---

### 3. **Wildcard MQTT en Suscripción (mqtt_client/subscriber.py)**

**Cambio:** Suscripción con wildcard `+` para capturar todas las zonas en un único suscriptor.

```python
# Antes: MQTT_TOPIC = "campo/sensores"
# Después:
MQTT_TOPIC = "campo/+/sensores"  # Captura campo/tomate/sensores, campo/zanahoria/sensores, etc.
client.subscribe(MQTT_TOPIC, qos=1)
```

**Ventaja sobre `#`:** El wildcard `+` solo captura mensajes de sensores, evitando procesar temas innecesarios como `campo/alertas` o `campo/actuadores`.

---

### 4. **Campos de Metadatos en MongoDB (mqtt_client/subscriber.py)**

**Cambio:** Persistencia de información MQTT en docucmentos de MongoDB.

```python
# Agregados a cada documento:
data["topic"] = msg.topic              # ej: "campo/tomate/sensores"
data["qos"] = msg.qos                  # ej: 1
data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
```

**Impacto:** Cada registro de sensor ahora incluye metadatos que facilitan auditoría, debugging y análisis por proto.

---

### 5. **Extracción Dinámica de Zona (mqtt_client/subscriber.py)**

**Cambio:** Parsing automático de la zona desde el topic MQTT.

```python
def extraer_zona(topic):
    # topic: "campo/tomate/sensores" → retorna "tomate"
    partes = topic.split("/")
    return partes[1] if len(partes) > 1 else "desconocida"

zona = extraer_zona(msg.topic)
data["zona"] = zona
```

**Impacto:** El subscriber no requiere que el sensor incluya la zona en el payload; la obtiene automáticamente del topic.

---

### 6. **API REST Dinámico sin Hardcoding (rest_api/app.py)**

**Cambio:** Endpoints que obtienen zonas directamente de MongoDB.

```python
@app.route("/zonas", methods=["GET"])
def zonas():
    # Antes: return jsonify(["tomate", "zanahoria", "maiz"])  # Hardcodeado
    # Después:
    resultado = coleccion.distinct("zona")  # Consulta dinámicamente desde BD
    return jsonify(sorted(resultado))
```

**Impacto:** Agregar una nueva zona de cultivo requiere solo modificar `docker-compose.yml`; la API la detecta automáticamente.

---

### 7. **Sidebar MQTT en Frontend (frontend/app.py)**

**Cambio:** Información visual de configuración MQTT en la barra lateral.

```python
with st.sidebar:
    st.markdown("### ⚙️ Configuración MQTT")
    st.info(f"""
    🔗 **Wildcard:** `campo/+/sensores`  
    📍 **Topics esperados:**  
    - `campo/tomate/sensores`
    - `campo/zanahoria/sensores`
    - `campo/maiz/sensores`  
    🔐 **QoS:** 1 (At least once delivery)
    """)
```

**Impacto:** Los usuarios pueden verificar la configuración MQTT sin ver código.

---

### 8. **Toggle Auto-actualización cada 10 segundos (frontend/app.py)**

**Cambio:** Refresco automático del dashboard con librería `streamlit-autorefresh`.

```python
from streamlit_autorefresh import st_autorefresh

auto_actualizar = st.sidebar.toggle("🔄 Auto-actualizar cada 10s", value=True)
if auto_actualizar:
    st_autorefresh(interval=10_000)  # 10,000 ms = 10 segundos
```

**Impacto:** Datos siempre frescos sin que el usuario tenga que presionar "Actualizar" manualmente.

---

### 9. **Tabs Dinámicos por Zona (frontend/app.py)**

**Cambio:** Creación automática de pestañas basada en zonas consultadas desde API.

```python
# Antes: tabs = st.tabs(["Tomate", "Zanahoria", "Maíz"])  # Hardcodeado
# Después:
zonas = obtener_zonas()  # Consulta GET /zonas
tab_labels = [f"{z.capitalize()}" for z in zonas]
tabs = st.tabs(tab_labels)
```

**Impacto:** El dashboard es 100% dinámico; agregar una zona la muestra automáticamente.

---

### 10. **Métricas por Zona (frontend/app.py)**

**Cambio:** Cálculo y visualización de promedios e indicadores clave.

```python
promedio_temp = df["temperatura"].mean()
promedio_humedad = df["humedad"].mean()
cantidad_registros = len(df)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Temp Promedio", f"{promedio_temp:.2f} °C")
with col2:
    st.metric("💧 Humedad Promedio", f"{promedio_humedad:.2f} %")
with col3:
    st.metric("📈 Registros", f"{cantidad_registros}")
```

**Impacto:** Resumen visual rápido de condiciones por zona.

---

### 11. **Gráfico de Línea Temporal (frontend/app.py)**

**Cambio:** Visualización de evolución de temperatura y humedad.

```python
st.subheader(f"📈 Evolución Temporal - {zona.title()}")
df_grafico = df.sort_values("timestamp").tail(30)  # Últimas 30 lecturas
st.line_chart(
    df_grafico.set_index("timestamp")[["temperatura", "humedad"]]
)
```

**Impacto:** Identificar tendencias, picos y anomalías en los datos de sensores.

---

### 12. **Tab Global "Todas las Zonas" (frontend/app.py)**

**Cambio:** Pestaña adicional para análisis comparativo.

```python
with tabs[0]:  # Primera tab = "Todas las Zonas"
    st.markdown("### 🌍 Comparativa de Todas las Zonas")
    logs_globales = requests.get(f"{API}/logs").json()
    df_global = pd.DataFrame(logs_globales)
    # Gráfico comparativo...
```

**Impacto:** Comparar condiciones de temperatura entre cultivos en un solo vistazo.

---

### 13. **Gráfico Comparativo de Temperatura (frontend/app.py)**

**Cambio:** Visualización agrégada de temperatura por cultivo.

```python
fig = px.line(
    df_global,
    x="timestamp",
    y="temperatura",
    color="zona",
    title="Temperatura por Cultivo",
    markers=True
)
st.plotly_chart(fig, use_container_width=True)
```

**Impacto:** Detectar qué zona tiene variaciones de temperatura más extremas.

---

### 14. **Tabla Ordenada de Últimas Lecturas (frontend/app.py)**

**Cambio:** Tabla interactiva con detalles completos.

```python
df_display = df[["timestamp", "sensor_id", "temperatura", "humedad", "topic", "qos"]].copy()
st.dataframe(df_display, use_container_width=True)
```

**Impacto:** Acceso granular a todos los datos con metadatos MQTT.

---

### 15. **Dependencia de Auto-refresh (frontend/Dockerfile)**

**Cambio:** Instalación de librería para refresco automático.

```dockerfile
RUN pip install streamlit==1.35.0 \
                requests==2.32.3 \
                pandas==2.2.2 \
                plotly==5.18.0 \
                streamlit-autorefresh==1.0.1  # ← NUEVO
```

**Impacto:** Frontend puede implementar auto-actualización sin necesidad de JavaScript personalizado.

---

### 16. **Configuración Multi-Zona en docker-compose.yml**

**Cambio:** Asignación de variable `ZONA` a cada sensor.

```yaml
sensor1:
  environment:
    - ZONA=tomate
    - SENSOR_ID=1

sensor2:
  environment:
    - ZONA=tomate
    - SENSOR_ID=2

# ... (sensor3: tomate, sensor4-6: zanahoria, sensor7-9: maiz)
```

**Impacto:** Sistema simula 3 zonas de cultivo con 3 sensores por zona.

---

### 17. **Documentación Actualizada (README.md y FUNCIONAMIENTO.md)**

**Cambios:**
- `README.md`: Agregada esta sección de "Cambios Aplicados"
- `FUNCIONAMIENTO.md`: Reescrito completamente con nueva arquitectura MQTT

**Impacto:** Documentación reflejaperfectamente la implementación actual.

---

## Resumen de Cambios

| Componente | Cambios | Beneficio |
|-----------|---------|-----------|
| **sensor.py** | QoS 1 + topic dinámico | Confiabilidad + organización por zona |
| **subscriber.py** | Wildcard + metadatos (topic, qos) | Captura flexible + auditoría |
| **rest_api/app.py** | `/zonas` dinámico, endpoints sin hardcoding | Escalabilidad automática |
| **frontend/app.py** | Sidebar + tabs dinámicos + auto-refresh + gráficos | UX profesional y reactiva |
| **docker-compose.yml** | Multi-zona por variable ZONA | Simulación realista |
| **Documentación** | Actualizada | Claridad para mantenedores |

---

## Validación

Todos los cambios fueron validados con:

```bash
✅ Build Docker exitoso (97.3s)
✅ 14 servicios corriendo sin errores
✅ GET /zonas → ["maiz","tomate","zanahoria"] (dinámico)
✅ GET /logs → Documentos con campo "qos": 1
✅ Dashboard con 4 tabs + auto-refresh funcionando
✅ Gráficos de línea y comparativos renderizados correctamente
✅ Tablas con datos filtrados por zona
```

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| El frontend muestra lista vacía | Los sensores aún no enviaron datos | Esperar ~5 segundos y volver a presionar "Actualizar" |
| `Error: No se pudo conectar al backend` | La API no está lista | Verificar `docker compose logs rest_api` |
| Los sensores no se conectan | Mosquitto tardó en iniciar | Reiniciar: `docker compose restart sensor1 sensor2` |
| Puerto 8501 o 5000 ocupado | Otro proceso usa ese puerto | Cambiar el puerto en `docker-compose.yml` |

---

## Notas de diseño

- Los documentos se guardan en MongoDB en la base `agro_iot` y la colección `lecturas`.
- Las versiones de dependencias están fijadas en los `Dockerfile` para asegurar builds reproducibles.
- El servidor de desarrollo de Flask es suficiente para este demo; en producción se recomienda usar `gunicorn`.
