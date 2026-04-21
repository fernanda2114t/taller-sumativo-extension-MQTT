import streamlit as st
import requests
import pandas as pd
import time

API_BASE_URL = "http://rest_api:5000"

st.title("Monitoreo Agrónomo IoT")
st.caption("Últimas 20 lecturas por zona de cultivo registradas en MongoDB")

st.sidebar.header("MQTT Activo")
st.sidebar.markdown("- Wildcard subscriber: `campo/cebolla/#`")
st.sidebar.markdown("- Topics esperados:")
st.sidebar.markdown("  - `campo/cebolla/temperatura`")
st.sidebar.markdown("  - `campo/cebolla/humedad`")
st.sidebar.markdown("  - `campo/cebolla/ph`")
st.sidebar.markdown("  - `campo/cebolla/luz`")
st.sidebar.markdown("  - `campo/cebolla/aire`")

auto_actualizar = st.sidebar.toggle("Auto-actualizar cada 10s", value=False)
if auto_actualizar:
    time.sleep(10)
    st.rerun()


def obtener_zonas():
    try:
        respuesta = requests.get(f"{API_BASE_URL}/zonas", timeout=5)
        respuesta.raise_for_status()
        return respuesta.json()
    except Exception:
        return []


def obtener_lecturas(zona):
    respuesta = requests.get(f"{API_BASE_URL}/logs/{zona}", timeout=5)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_lecturas_globales():
    respuesta = requests.get(f"{API_BASE_URL}/logs", timeout=5)
    respuesta.raise_for_status()
    return respuesta.json()

if st.button("Actualizar") or auto_actualizar:
    try:
        data = obtener_lecturas("cebolla")

        if not data:
            st.info("Aún no hay lecturas de cebolla. Esperá unos segundos y volvé a actualizar.")
            st.stop()

        df = pd.DataFrame(data)

        sensores = ["temperatura", "humedad", "ph", "luz", "aire"]
        for sensor in sensores:
            if sensor in df.columns:
                df[sensor] = pd.to_numeric(df[sensor], errors="coerce")

        cols = st.columns(len(sensores))
        unidades = {"temperatura": "°C", "humedad": "%", "ph": "", "luz": "lux", "aire": "ppm"}
        for col, sensor in zip(cols, sensores):
            if sensor in df.columns:
                promedio = df[sensor].mean()
                col.metric(sensor.title(), f"{promedio:.2f} {unidades[sensor]}" if pd.notna(promedio) else "N/A")

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df_grafico = df.dropna(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
            cols_grafico = [s for s in sensores if s in df_grafico.columns]
            if cols_grafico:
                st.subheader("Histórico de sensores")
                st.line_chart(df_grafico[cols_grafico], use_container_width=True)

        col_orden = ["timestamp", "sensor", "valor"]
        columnas = [c for c in col_orden if c in df.columns]
        restantes = [c for c in df.columns if c not in columnas]
        st.dataframe(df[columnas + restantes], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
