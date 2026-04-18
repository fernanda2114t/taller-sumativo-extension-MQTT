import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

API_BASE_URL = "http://rest_api:5000"

st.title("Monitoreo Agrónomo IoT")
st.caption("Últimas 20 lecturas por zona de cultivo registradas en MongoDB")

st.sidebar.header("MQTT Activo")
st.sidebar.markdown("- Wildcard subscriber: `campo/+/sensores`")
st.sidebar.markdown("- Topics esperados:")
st.sidebar.markdown("  - `campo/tomate/sensores`")
st.sidebar.markdown("  - `campo/zanahoria/sensores`")
st.sidebar.markdown("  - `campo/maiz/sensores`")

auto_actualizar = st.sidebar.toggle("Auto-actualizar cada 10s", value=False)
if auto_actualizar:
    st_autorefresh(interval=10_000, key="auto_refresh_10s")


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
        zonas = obtener_zonas()

        if not zonas:
            st.warning("No hay zonas disponibles aún. Esperá lecturas nuevas y volvé a actualizar.")
            st.stop()

        etiquetas = ["Todas las zonas"] + [zona.title() for zona in zonas]
        pestañas = st.tabs(etiquetas)

        with pestañas[0]:
            data_global = obtener_lecturas_globales()

            if not data_global:
                st.info("Aún no hay lecturas globales. Esperá unos segundos y volvé a actualizar.")
            else:
                df_global = pd.DataFrame(data_global)
                if "temperatura" in df_global.columns:
                    df_global["temperatura"] = pd.to_numeric(df_global["temperatura"], errors="coerce")

                if {"timestamp", "zona", "temperatura"}.issubset(df_global.columns):
                    df_comp = df_global[["timestamp", "zona", "temperatura"]].copy()
                    df_comp["timestamp"] = pd.to_datetime(df_comp["timestamp"], errors="coerce")
                    df_comp = df_comp.dropna(subset=["timestamp", "zona", "temperatura"])
                    if not df_comp.empty:
                        serie_comparativa = (
                            df_comp.sort_values("timestamp")
                            .pivot_table(index="timestamp", columns="zona", values="temperatura", aggfunc="mean")
                        )
                        st.subheader("Comparativo de temperatura por cultivo")
                        st.line_chart(serie_comparativa, use_container_width=True)

                col_orden = ["timestamp", "sensor_id", "zona", "temperatura", "humedad", "topic", "qos"]
                columnas = [c for c in col_orden if c in df_global.columns]
                restantes = [c for c in df_global.columns if c not in columnas]
                df_global = df_global[columnas + restantes]
                st.dataframe(df_global, use_container_width=True, hide_index=True)

        for zona, pestaña in zip(zonas, pestañas[1:]):
            with pestaña:
                data = obtener_lecturas(zona)

                if not data:
                    st.info(f"Aún no hay lecturas en la zona {zona}. Esperá unos segundos y volvé a actualizar.")
                    continue

                df = pd.DataFrame(data)
                if "temperatura" in df.columns:
                    df["temperatura"] = pd.to_numeric(df["temperatura"], errors="coerce")
                if "humedad" in df.columns:
                    df["humedad"] = pd.to_numeric(df["humedad"], errors="coerce")

                promedio_temp = df["temperatura"].mean() if "temperatura" in df.columns else None
                promedio_humedad = df["humedad"].mean() if "humedad" in df.columns else None
                cantidad_lecturas = len(df)

                m1, m2, m3 = st.columns(3)
                m1.metric("Temperatura promedio", f"{promedio_temp:.2f} °C" if pd.notna(promedio_temp) else "N/A")
                m2.metric("Humedad promedio", f"{promedio_humedad:.2f} %" if pd.notna(promedio_humedad) else "N/A")
                m3.metric("Lecturas", cantidad_lecturas)

                if {"timestamp", "temperatura", "humedad"}.issubset(df.columns):
                    df_grafico = df[["timestamp", "temperatura", "humedad"]].copy()
                    df_grafico["timestamp"] = pd.to_datetime(df_grafico["timestamp"], errors="coerce")
                    df_grafico = df_grafico.dropna(subset=["timestamp"]).sort_values("timestamp")
                    if not df_grafico.empty:
                        st.line_chart(
                            df_grafico.set_index("timestamp")[["temperatura", "humedad"]],
                            use_container_width=True,
                        )

                col_orden = ["timestamp", "sensor_id", "zona", "temperatura", "humedad"]
                columnas = [c for c in col_orden if c in df.columns]
                restantes = [c for c in df.columns if c not in columnas]
                df = df[columnas + restantes]
                st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
