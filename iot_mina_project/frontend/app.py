import streamlit as st
import requests
import pandas as pd
import time

API_BASE_URL = "http://rest_api:5000"

st.title("Monitoreo de Zona de Perforación - Mina IoT")
st.caption("Últimas 20 lecturas por zona de perforación desde el backend REST API conectado a MongoDB")

st.sidebar.header("MQTT Activo")
st.sidebar.markdown("- Wildcard subscriber: `mina/zona_perforacion/#`")
st.sidebar.markdown("- Topics esperados:")
st.sidebar.markdown("  - `mina/zona_perforacion/produccion`")
st.sidebar.markdown("  - `mina/zona_perforacion/seguridad`")
st.sidebar.markdown("  - `mina/zona_perforacion/quimica`")

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


def obtener_lecturas(sensor):
    respuesta = requests.get(f"{API_BASE_URL}/logs/sensor/{sensor}", timeout=5)
    respuesta.raise_for_status()
    return respuesta.json()




def mostrar_sensor(nombre, unidad):
    data = obtener_lecturas(nombre)
    if not data:
        st.info(f"Sin datos de {nombre} aún.")
        return
    df = pd.DataFrame(data)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp")

    col1, col2 = st.columns(2)
    col1.metric(f"{nombre.title()} (último)", f"{df['valor'].iloc[-1]:.2f} {unidad}")
    col2.metric(f"{nombre.title()} (promedio)", f"{df['valor'].mean():.2f} {unidad}")

    st.line_chart(df.set_index("timestamp")["valor"], use_container_width=True)
    st.dataframe(df[["timestamp", "valor"]].tail(10), use_container_width=True, hide_index=True)


if st.button("Actualizar") or auto_actualizar:
    try:
        tab_seg, tab_qui, tab_pro = st.tabs(["Seguridad", "Quimica", "Produccion"])

        with tab_seg:
            st.subheader("Seguridad Operacional")
            mostrar_sensor("temperatura", "°C")
            mostrar_sensor("humedad", "%")
            mostrar_sensor("vibraciones", "m/s²")

        with tab_qui:
            st.subheader("Condiciones Quimicas")
            mostrar_sensor("CO2", "ppm")
            mostrar_sensor("SO2", "ppm")
            mostrar_sensor("particulado", "µg/m³")

        with tab_pro:
            st.subheader("Produccion")
            mostrar_sensor("toneladas", "t/h")
            mostrar_sensor("ciclos", "ciclos")

    except Exception as e:
        st.error(f"Error al obtener datos: {e}")

