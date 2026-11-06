"""Dashboard: Precipitación en Boyacá (IDEAM, 2025).

Lee las tablas de la capa oro que genera el notebook (data/oro/*.csv).
Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CARPETA_ORO = Path(__file__).resolve().parents[2] / "data" / "oro"   # dashboard/data/oro
MESES_LLUVIOSOS = [3, 4, 5, 9, 10, 11]          # mismo supuesto del notebook
# PISBA: falla de sensor (ver documento, sección 4)
ESTACION_FALLA = "0035215030"
MUNICIPIO_FALLA = "PISVA"                        # su único municipio
ORDEN_FRANJAS = ["Madrugada (0-5)", "Mañana (6-11)",
                 "Tarde (12-17)", "Noche (18-23)"]
NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May",
               "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Colores (paleta validada: azul y naranja como categóricas, azul como secuencial)
AZUL, NARANJA, ROJO, GRIS_MEDIO = "#2a78d6", "#eb6834", "#e34948", "#f0efec"
COLOR_TEMPORADA = {"Lluviosa": AZUL, "Seca": NARANJA}
SECUENCIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
DIVERGENTE = [[0.0, ROJO], [0.5, GRIS_MEDIO], [1.0, AZUL]]

st.set_page_config(page_title="Precipitación en Boyacá",
                   page_icon="🌧️", layout="wide")


@st.cache_data
def cargar():
    tipos = {"codigoestacion": str}
    mensual = pd.read_csv(CARPETA_ORO / "oro_mensual.csv")
    franja = pd.read_csv(CARPETA_ORO / "oro_franja.csv")
    estaciones = pd.read_csv(CARPETA_ORO / "oro_estaciones.csv", dtype=tipos)
    diario = pd.read_csv(CARPETA_ORO / "oro_diario.csv",
                         dtype=tipos, parse_dates=["fecha"])
    diario["mes"] = diario["fecha"].dt.month
    diario["temporada"] = np.where(
        diario["mes"].isin(MESES_LLUVIOSOS), "Lluviosa", "Seca")
    return mensual, franja, estaciones, diario


def estilo(fig, alto=340):
    fig.update_layout(template="plotly_white", height=alto, margin=dict(l=10, r=10, t=10, b=10),
                      font=dict(family="system-ui, Segoe UI, sans-serif",
                                size=13, color="#0b0b0b"),
                      hoverlabel=dict(font_size=13), legend_title_text="", separators=",.")
    fig.update_xaxes(showgrid=False, linecolor="#c3c2b7")
    fig.update_yaxes(gridcolor="#e1e0d9", zeroline=False)
    return fig


faltan = [f for f in ("oro_mensual", "oro_franja", "oro_estaciones", "oro_diario")
          if not (CARPETA_ORO / f"{f}.csv").exists()]
if faltan:
    st.error(
        f"Faltan archivos en data/oro: {', '.join(faltan)}. Ejecute primero el notebook.")
    st.stop()

mensual, franja, estaciones, diario = cargar()

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
excluir = st.sidebar.toggle("Excluir estación PISBA (falla de sensor)", value=True,
                            help="Suma el 68,8 % de toda la lluvia por un sensor dañado. Ver documento, sección 4.")
municipios_todos = sorted(mensual["municipio"].unique())
if excluir:
    municipios_todos = [m for m in municipios_todos if m != MUNICIPIO_FALLA]
municipios = st.sidebar.multiselect(
    "Municipio", municipios_todos, placeholder="Todos los municipios")
mes_ini, mes_fin = st.sidebar.select_slider("Periodo", options=list(range(1, 13)), value=(1, 12),
                                            format_func=lambda m: NOMBRES_MES[m - 1])
st.sidebar.caption(
    "Fuente: IDEAM, conjunto Precipitación (s54a-sgyg), datos.gov.co. Capa oro del notebook.")

sel_mun = municipios or municipios_todos
f_mensual = mensual[mensual["municipio"].isin(
    sel_mun) & mensual["mes"].between(mes_ini, mes_fin)]
f_diario = diario[diario["municipio"].isin(
    sel_mun) & diario["mes"].between(mes_ini, mes_fin)]
f_estaciones = estaciones[estaciones["municipio"].isin(sel_mun)]
if excluir:
    f_diario = f_diario[f_diario["codigoestacion"] != ESTACION_FALLA]
    f_estaciones = f_estaciones[f_estaciones["codigoestacion"]
                                != ESTACION_FALLA]

# ---------------------------------------------------------------- encabezado y KPI
st.title("Precipitación en Boyacá · IDEAM 2025")
st.caption("Proyecto Integrador Big Data 2026-2 · Jose Julian Tobito Montoya y Andres Felipe Wilches Salas")

acumulado_mun = f_mensual.groupby(
    "municipio")["precip_mm"].sum().sort_values(ascending=False)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Registros analizados",
          f"{int(f_mensual['n_registros'].sum()):,}".replace(",", "."))
k2.metric("Lluvia acumulada",
          f"{f_mensual['precip_mm'].sum():,.0f} mm".replace(",", "."))
k3.metric("Días-estación con lluvia",
          f"{(f_diario['precip_mm'] > 0).mean() * 100:.1f} %".replace(".", ","))
k4.metric("Municipio con mayor acumulado",
          acumulado_mun.index[0].title() if len(acumulado_mun) else "—")

# ---------------------------------------------------------------- fila 1: P1 y P2
c1, c2 = st.columns(2)
with c1:
    st.subheader("Lluvia por mes y temporada (P1, P5)")
    por_mes = f_mensual.groupby("mes", as_index=False)[
        ["precip_mm", "n_estaciones"]].sum()
    por_mes["mm_por_estacion"] = por_mes["precip_mm"] / por_mes["n_estaciones"]
    por_mes["temporada"] = np.where(
        por_mes["mes"].isin(MESES_LLUVIOSOS), "Lluviosa", "Seca")
    por_mes["nombre"] = por_mes["mes"].map(lambda m: NOMBRES_MES[m - 1])
    fig = px.bar(por_mes, x="nombre", y="mm_por_estacion", color="temporada", color_discrete_map=COLOR_TEMPORADA,
                 category_orders={"nombre": NOMBRES_MES,
                                  "temporada": ["Lluviosa", "Seca"]},
                 labels={"nombre": "", "mm_por_estacion": "mm por estación"},
                 custom_data=["precip_mm", "n_estaciones"])
    fig.update_traces(hovertemplate="%{x}: %{y:.1f} mm por estación<br>Total %{customdata[0]:,.0f} mm · "
                                    "%{customdata[1]} estación(es)<extra></extra>", marker_line_width=0)
    fig.update_layout(bargap=0.25, legend=dict(orientation="h", y=1.08, x=0))
    st.plotly_chart(estilo(fig), width="stretch")
with c2:
    st.subheader("Municipios con mayor acumulado (P2)")
    top = acumulado_mun.head(10).rename("precip_mm").reset_index()
    top["pct"] = top["precip_mm"] / f_mensual["precip_mm"].sum() * 100
    top["municipio"] = top["municipio"].str.title()
    fig = px.bar(top.iloc[::-1], x="precip_mm", y="municipio", orientation="h", custom_data=["pct"],
                 labels={"precip_mm": "mm acumulados", "municipio": ""}, color_discrete_sequence=[AZUL])
    fig.update_traces(hovertemplate="%{y}: %{x:,.0f} mm (%{customdata[0]:.1f} % del total)<extra></extra>",
                      marker_line_width=0)
    fig.update_xaxes(showgrid=True, gridcolor="#e1e0d9")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(estilo(fig), width="stretch")

# ---------------------------------------------------------------- fila 2: P3 y P5
c3, c4 = st.columns(2)
with c3:
    st.subheader("% de registros con lluvia por franja (P3)")
    fr = franja.set_index("franja").loc[ORDEN_FRANJAS].reset_index()
    fr["pct"] = fr["n_lluvia"] / fr["n_registros"] * 100
    fig = px.bar(fr, x="franja", y="pct", labels={"franja": "", "pct": "% de registros con lluvia"},
                 color_discrete_sequence=[AZUL], custom_data=["n_lluvia", "n_registros"])
    fig.update_traces(hovertemplate="%{x}: %{y:.2f} %<br>%{customdata[0]:,} de %{customdata[1]:,} registros"
                                    "<extra></extra>", marker_line_width=0)
    fig.update_layout(bargap=0.45)
    st.plotly_chart(estilo(fig), width="stretch")
    st.caption(
        "Total de Boyacá: la tabla oro_franja no se desagrega por municipio, así que no responde a los filtros.")
with c4:
    st.subheader("Lluvia diaria por temporada (P5)")
    temp = (f_diario.groupby("temporada")["precip_mm"].agg(["mean", "count"]).reindex(["Lluviosa", "Seca"])
            .reset_index())
    fig = px.bar(temp, x="temporada", y="mean", color="temporada", color_discrete_map=COLOR_TEMPORADA,
                 labels={"temporada": "", "mean": "mm por estación y día"}, custom_data=["count"])
    fig.update_traces(hovertemplate="%{x}: %{y:.2f} mm/día<br>%{customdata[0]:,} días-estación<extra></extra>",
                      marker_line_width=0, texttemplate="%{y:.2f} mm", textposition="outside")
    fig.update_layout(bargap=0.55, showlegend=False)
    st.plotly_chart(estilo(fig), width="stretch")

# ---------------------------------------------------------------- fila 3: mapa y correlación
c5, c6 = st.columns(2)
with c5:
    st.subheader("Estaciones según lluvia acumulada (P2)")
    mapa = f_estaciones.assign(nombre=f_estaciones["nombreestacion"].str.title(),
                               municipio_t=f_estaciones["municipio"].str.title())
    fig = px.scatter_map(mapa, lat="latitud", lon="longitud", size="precip_mm", color="precip_mm",
                         color_continuous_scale=SECUENCIAL, size_max=26, zoom=7,
                         center=dict(lat=5.75, lon=-73.1), map_style="carto-positron",
                         custom_data=["nombre", "municipio_t", "precip_mm"])
    fig.update_traces(
        hovertemplate="%{customdata[0]} (%{customdata[1]})<br>%{customdata[2]:,.0f} mm<extra></extra>")
    fig.update_layout(coloraxis_colorbar=dict(title="mm"))
    st.plotly_chart(estilo(fig, 380), width="stretch")
with c6:
    st.subheader("Correlación de la lluvia diaria (P4)")
    top8 = f_diario["nombreestacion"].value_counts().head(8).index
    tabla = f_diario[f_diario["nombreestacion"].isin(top8)].pivot_table(index="fecha", columns="nombreestacion",
                                                                        values="precip_mm")
    if tabla.shape[1] >= 2:
        corr = tabla.corr()
        corr.index = corr.columns = [c.title() for c in corr.columns]
        fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
                                   colorscale=DIVERGENTE, xgap=2, ygap=2,
                                   texttemplate="%{z:.2f}",
                                   hovertemplate="%{y} vs %{x}: r = %{z:.2f}<extra></extra>",
                                   colorbar=dict(title="r")))
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(estilo(fig, 380), width="stretch")
        pares = corr.values[np.triu_indices_from(corr.values, k=1)]
        promedio = f"{np.nanmean(pares):.2f}".replace(".", ",")
        st.caption(f"Pearson entre las {tabla.shape[1]} estaciones con más días de datos. "
                   f"Promedio entre pares: {promedio}")
    else:
        st.info(
            "Seleccione municipios con al menos dos estaciones para ver la correlación.")

# ---------------------------------------------------------------- vista de tabla
with st.expander("Ver los datos de la selección"):
    st.dataframe(por_mes[["nombre", "temporada", "precip_mm", "n_estaciones", "mm_por_estacion"]]
                 .rename(columns={"nombre": "mes"}), hide_index=True, width="stretch")
    st.dataframe(top, hide_index=True, width="stretch")
