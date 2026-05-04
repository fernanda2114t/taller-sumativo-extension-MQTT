# Grafana y Prometheus - Guía de Implementación

## 🚀 Descripción General

Se han añadido **Grafana** y **Prometheus** al proyecto para monitoreo y visualización de métricas en tiempo real.

## 📊 Componentes Añadidos

### 1. **Prometheus**
- **Imagen**: `prom/prometheus:latest`
- **Puerto**: `9090`
- **Función**: Recopila y almacena métricas de tiempo
- **Archivo de configuración**: `prometheus.yml`

### 2. **Grafana**
- **Imagen**: `grafana/grafana:latest`
- **Puerto**: `3000`
- **Usuario**: `admin`
- **Contraseña**: `admin`
- **Función**: Visualiza métricas en dashboards interactivos

### 3. **MongoDB Exporter**
- **Imagen**: `percona/mongodb_exporter:latest`
- **Puerto**: `9216`
- **Función**: Exporta métricas de MongoDB a Prometheus

### 4. **cAdvisor** (Container Advisor)
- **Imagen**: `gcr.io/cadvisor/cadvisor:latest`
- **Puerto**: `8080`
- **Función**: Monitorea recursos de contenedores Docker

## 🔧 Cambios Realizados

### REST API (rest_api/app.py)
Se añadieron métricas de Prometheus:
- `api_requests_total`: Total de requests por método y endpoint
- `api_request_duration_seconds`: Duración de requests
- `sensors_gauge`: Total de lecturas de sensores
- `zones_gauge`: Total de zonas

Nuevo endpoint disponible:
- `GET /metrics` - Expone métricas en formato Prometheus

### Docker Compose
Nuevos servicios:
- `prometheus`: Sistema de monitoreo
- `grafana`: Plataforma de visualización
- `mongodb-exporter`: Exportador de métricas MongoDB
- `cadvisor`: Monitor de contenedores

Nuevos volúmenes:
- `prometheus_data`: Almacenamiento de datos de Prometheus
- `grafana_data`: Almacenamiento de configuración de Grafana

## 🚀 Cómo Usar

### 1. Iniciar los Servicios

```bash
docker-compose up -d
```

### 2. Acceder a Grafana

1. Abre http://localhost:3000
2. Inicia sesión:
   - **Usuario**: admin
   - **Contraseña**: admin
3. Se te pedirá cambiar la contraseña (opcional)

### 3. Configurar Prometheus como Data Source en Grafana

1. En Grafana, ve a: **Connections > Data sources**
2. Haz click en **Add new data source**
3. Selecciona **Prometheus**
4. En **URL**, escribe: `http://prometheus:9090`
5. Haz click en **Save & test**

### 4. Crear Dashboards

#### Dashboard de REST API
1. Ve a **Dashboards > Create > New dashboard**
2. Crea un panel con las siguientes queries:
   - `rate(api_requests_total[5m])` - Tasa de requests
   - `api_request_duration_seconds_bucket` - Latencia de requests
   - `sensors_gauge` - Lecturas de sensores
   - `zones_gauge` - Zonas activas

#### Dashboard de MongoDB
1. Añade un panel con:
   - `mongodb_up` - Estado de MongoDB
   - `mongodb_connections_current` - Conexiones activas

#### Dashboard de Docker
1. Añade un panel con:
   - `container_cpu_usage_seconds_total` - CPU de contenedores
   - `container_memory_usage_bytes` - Memoria de contenedores

### 5. Acceder a Prometheus

- URL: http://localhost:9090
- Explorador de métricas: http://localhost:9090/graph

## 📈 Métricas Disponibles

### REST API
- `api_requests_total` - Total de requests procesados
- `api_request_duration_seconds` - Duración de cada request
- `sensors_gauge` - Cantidad de lecturas de sensores
- `zones_gauge` - Cantidad de zonas

### MongoDB
- `mongodb_up` - Si MongoDB está disponible (1/0)
- `mongodb_connections_current` - Conexiones activas
- `mongodb_connections_available` - Conexiones disponibles
- `mongodb_memory_resident_megabytes` - Memoria residente

### Docker (cAdvisor)
- `container_cpu_usage_seconds_total` - Uso de CPU
- `container_memory_usage_bytes` - Uso de memoria
- `container_network_receive_bytes_total` - Bytes recibidos en red
- `container_network_transmit_bytes_total` - Bytes transmitidos en red

## 🔍 Troubleshooting

### Prometheus no ve targets

1. Verifica que `prometheus.yml` esté en la carpeta correcta
2. Revisa logs: `docker-compose logs prometheus`
3. Asegúrate que los servicios están corriendo: `docker-compose ps`

### Grafana no se conecta a Prometheus

1. Verifica la URL del data source: `http://prometheus:9090`
2. Desde el contenedor de Grafana, intenta: `curl http://prometheus:9090/-/healthy`
3. Revisa logs: `docker-compose logs grafana`

### Métricas no aparecen en Prometheus

1. Verifica que el endpoint `/metrics` está funcionando:
   ```bash
   curl http://localhost:5000/metrics
   ```
2. Revisa el archivo `prometheus.yml` para asegurar que el job está configurado
3. Espera 15-30 segundos para que Prometheus recolecte las métricas

## 📝 Archivos Modificados

- `docker-compose.yml` - Añadidos servicios de Prometheus, Grafana, MongoDB Exporter y cAdvisor
- `rest_api/app.py` - Añadidas métricas de Prometheus
- `rest_api/Dockerfile` - Añadida dependencia prometheus-client
- `prometheus.yml` - Nuevo archivo de configuración (creado)

## 🎯 Próximos Pasos

1. Crear dashboards personalizados para tus casos de uso
2. Configurar alertas en Prometheus
3. Implementar exportadores personalizados si es necesario
4. Integrar logs con ELK Stack (opcional)
