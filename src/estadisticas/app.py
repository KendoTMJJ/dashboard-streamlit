"""Dashboard: Precipitación en Boyacá (IDEAM, 2025).

Lee las tablas de la capa oro que genera el notebook (data/oro/*.csv).
Ejecutar:  streamlit run src/estadisticas/app.py
"""
import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

CARPETA_ORO = Path(__file__).resolve().parents[2] / "data" / "oro"   # dashboard/data/oro
MESES_LLUVIOSOS = [3, 4, 5, 9, 10, 11]          # mismo supuesto del notebook
# LLANO ALARCON y HATO LAGUNA: posible error de escala (notebook, sección 8)
EN_OBSERVACION = ["0035160020", "0035167010"]
MIN_DIAS_P4 = 325                                # cobertura anual mínima para la correlación
MIN_DIAS_MUNICIPIO = 15                          # días-estación por mes para comparar municipios
ORDEN_FRANJAS = ["Madrugada (0-5)", "Mañana (6-11)", "Tarde (12-17)", "Noche (18-23)"]
NOMBRES_MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

AZUL, NARANJA, AGUA, ROJO, GRIS_MEDIO = "#2a78d6", "#eb6834", "#1baf7a", "#e34948", "#f0efec"
COLOR_TEMPORADA = {"Lluviosa": AZUL, "Seca": NARANJA}
COLOR_ZONA = {"MEDIO MAGDALENA": AZUL, "META": NARANJA, "SOGAMOSO": AGUA}
SECUENCIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
DIVERGENTE = [[0.0, ROJO], [0.5, GRIS_MEDIO], [1.0, AZUL]]

st.set_page_config(page_title="Precipitación en Boyacá", page_icon="🌧️", layout="wide")


@st.cache_data
def cargar():
    tipos = {"codigoestacion": str}
    estaciones = pd.read_csv(CARPETA_ORO / "oro_estaciones.csv", dtype=tipos)
    franjas = pd.read_csv(CARPETA_ORO / "oro_franja_estacion.csv", dtype=tipos)
    diario = pd.read_csv(CARPETA_ORO / "oro_diario.csv", dtype=tipos, parse_dates=["fecha"])
    diario["mes"] = diario["fecha"].dt.month
    diario["temporada"] = np.where(diario["mes"].isin(MESES_LLUVIOSOS), "Lluviosa", "Seca")
    diario = diario.merge(estaciones[["codigoestacion", "zonahidrografica"]], on="codigoestacion", how="left")
    return estaciones, franjas, diario


def estilo(fig, alto=380):
    fig.update_layout(template="plotly_white", height=alto, margin=dict(l=10, r=10, t=30, b=10),
                      font=dict(family="system-ui, Segoe UI, sans-serif", size=13, color="#0b0b0b"),
                      hoverlabel=dict(font_size=13), legend_title_text="", separators=",.")
    fig.update_xaxes(showgrid=False, linecolor="#c3c2b7")
    fig.update_yaxes(gridcolor="#e1e0d9", zeroline=False)
    return fig


def numero(x, dec=0):
    """Formato en español: 1.234,56"""
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def correlacion(tabla, metodo):
    if metodo == "Pearson":
        return tabla.corr(min_periods=30)
    # Spearman = Pearson sobre los rangos de los días que comparten las dos estaciones
    m = pd.DataFrame(np.eye(tabla.shape[1]), index=tabla.columns, columns=tabla.columns)
    for i, a in enumerate(tabla.columns):
        for b in tabla.columns[i + 1:]:
            comun = tabla[[a, b]].dropna().rank()
            m.loc[a, b] = m.loc[b, a] = comun[a].corr(comun[b]) if len(comun) >= 30 else np.nan
    return m


faltan = [f for f in ("oro_estaciones", "oro_franja_estacion", "oro_diario") if not (CARPETA_ORO / f"{f}.csv").exists()]
if faltan:
    st.error(f"Faltan archivos en data/oro: {', '.join(faltan)}. Ejecute primero el notebook.")
    st.stop()

estaciones, franjas, diario = cargar()

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
municipios = st.sidebar.multiselect("Municipio", sorted(diario["municipio"].unique()), placeholder="Todos")
zonas = st.sidebar.multiselect("Zona hidrográfica", sorted(diario["zonahidrografica"].unique()), placeholder="Todas")
mes_ini, mes_fin = st.sidebar.select_slider("Periodo", options=list(range(1, 13)), value=(1, 12),
                                            format_func=lambda m: NOMBRES_MES[m - 1])
excluir = st.sidebar.toggle("Excluir estaciones en observación", value=False,
                            help="Llano Alarcón y Hato Laguna marcan 8,8 y 6,5 veces lo de sus vecinas: "
                                 "posible error de escala sin confirmar.")
st.sidebar.caption("Fuente: IDEAM, conjunto Precipitación (s54a-sgyg), datos.gov.co, CC BY-SA 4.0. "
                   "Datos no validados por el IDEAM.")

est_sel = estaciones
if municipios:
    est_sel = est_sel[est_sel["municipio"].isin(municipios)]
if zonas:
    est_sel = est_sel[est_sel["zonahidrografica"].isin(zonas)]
if excluir:
    est_sel = est_sel[~est_sel["codigoestacion"].isin(EN_OBSERVACION)]
ids = est_sel["codigoestacion"]
datos = diario[diario["codigoestacion"].isin(ids) & diario["mes"].between(mes_ini, mes_fin)]
n_meses = mes_fin - mes_ini + 1
dias_periodo = sum(calendar.monthrange(2025, m)[1] for m in range(mes_ini, mes_fin + 1))

# ---------------------------------------------------------------- encabezado y KPI
st.title("Precipitación en Boyacá · IDEAM 2025")
st.caption("Proyecto Integrador Big Data 2026-2 · Jose Julian Tobito Montoya y Andres Felipe Wilches Salas")
if len(datos) < 30:
    st.warning("Hay muy pocos datos con estos filtros. Amplíe la selección.")
    st.stop()

por_mun = datos.groupby("municipio").agg(mm=("precip_mm", "sum"), dias=("precip_mm", "size"),
                                         estaciones=("codigoestacion", "nunique")).reset_index()
por_mun["pct"] = por_mun["mm"] / por_mun["mm"].sum() * 100
por_mun["mm_dia"] = por_mun["mm"] / por_mun["dias"]
por_mun["nombre"] = por_mun["municipio"].str.title()
por_mun = por_mun.sort_values("mm", ascending=False)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Estaciones", numero(datos["codigoestacion"].nunique()))
k2.metric("Días-estación con datos", numero(len(datos)))
k3.metric("Lluvia promedio", f"{numero(datos['precip_mm'].mean(), 2)} mm/día",
          help="Milímetros por día y estación con datos")
k4.metric("Días-estación con lluvia", f"{numero((datos['precip_mm'] > 0).mean() * 100, 1)} %")

t1, t2, t3, t4, t5, t6 = st.tabs(["P1 · Meses", "P2 · Municipios", "P3 · Franjas", "P4 · Correlación",
                                  "P5 · Temporadas", "Datos"])

# ---------------------------------------------------------------- P1
with t1:
    por_mes = datos.groupby("mes").agg(mm=("precip_mm", "sum"), dias=("precip_mm", "size"),
                                       estaciones=("codigoestacion", "nunique")).reset_index()
    por_mes["mm por día-estación"] = por_mes["mm"] / por_mes["dias"]
    por_mes["mm por estación activa"] = por_mes["mm"] / por_mes["estaciones"]
    por_mes["cobertura"] = por_mes["dias"] / por_mes["estaciones"]
    por_mes["temporada"] = np.where(por_mes["mes"].isin(MESES_LLUVIOSOS), "Lluviosa", "Seca")
    por_mes["nombre"] = por_mes["mes"].map(lambda m: NOMBRES_MES[m - 1])
    medida = st.radio("Medida", ["mm por día-estación", "mm por estación activa"], horizontal=True)
    fig = px.bar(por_mes, x="nombre", y=medida, color="temporada", color_discrete_map=COLOR_TEMPORADA,
                 category_orders={"nombre": NOMBRES_MES, "temporada": ["Lluviosa", "Seca"]},
                 labels={"nombre": "", medida: medida}, custom_data=["estaciones", "cobertura"])
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:.2f} mm<br>%{customdata[0]} estaciones · "
                                                         "%{customdata[1]:.0f} días con datos cada una<extra></extra>")
    fig.update_layout(bargap=0.25, legend=dict(orientation="h", y=1.12, x=0))
    st.plotly_chart(estilo(fig), width="stretch")
    st.caption("La medida por día-estación corrige la cobertura. En todo Boyacá, febrero tiene unos 4 días con datos por estación, "
               "así que su acumulado no es comparable.")

# ---------------------------------------------------------------- P2
with t2:
    izq, der = st.columns(2)
    with izq:
        criterio = st.radio("Criterio", ["Acumulado", "mm por día-estación"], horizontal=True)
        if criterio == "Acumulado":
            top, col, etiqueta = por_mun, "mm", "mm acumulados"
        else:
            top = por_mun[por_mun["dias"] >= MIN_DIAS_MUNICIPIO * n_meses].sort_values("mm_dia", ascending=False)
            col, etiqueta = "mm_dia", "mm por día-estación"
        if len(top):
            fig = px.bar(top.head(10), x=col, y="nombre", orientation="h", color_discrete_sequence=[AZUL],
                         labels={col: etiqueta, "nombre": ""}, custom_data=["pct", "estaciones", "dias"])
            fig.update_traces(marker_line_width=0,
                              hovertemplate="%{y}: %{x:,.2f}<br>%{customdata[0]:.1f} % del total · %{customdata[1]} "
                                            "estación(es) · %{customdata[2]} días-estación<extra></extra>")
            fig.update_yaxes(autorange="reversed", showgrid=False)
            st.plotly_chart(estilo(fig, 420), width="stretch")
        else:
            st.info("Ningún municipio tiene suficientes días con datos en este periodo.")
        st.caption(f"Top 5 por acumulado: {numero(por_mun['pct'].head(5).sum(), 1)} % del total de la selección. El "
                   "acumulado favorece a los municipios con más estaciones.")
    with der:
        mapa = datos.groupby("codigoestacion").agg(mm_dia=("precip_mm", "mean"), dias=("precip_mm", "size")).reset_index()
        mapa = mapa.merge(estaciones[["codigoestacion", "nombreestacion", "municipio", "latitud", "longitud"]], on="codigoestacion")
        mapa["nombre"], mapa["mun"] = mapa["nombreestacion"].str.title(), mapa["municipio"].str.title()
        fig = px.scatter_map(mapa, lat="latitud", lon="longitud", size="mm_dia", color="mm_dia", size_max=24, zoom=6.5,
                             center=dict(lat=5.75, lon=-73.25), map_style="carto-positron",
                             color_continuous_scale=SECUENCIAL, custom_data=["nombre", "mun", "mm_dia", "dias"])
        fig.update_traces(hovertemplate="%{customdata[0]} (%{customdata[1]})<br>%{customdata[2]:.2f} mm/día · "
                                        "%{customdata[3]} días<extra></extra>")
        fig.update_layout(coloraxis_colorbar=dict(title="mm/día"))
        st.plotly_chart(estilo(fig, 500), width="stretch")

# ---------------------------------------------------------------- P3
with t3:
    f = franjas[franjas["codigoestacion"].isin(ids)]
    fr = f.groupby("franja")[["n_registros", "n_lluvia"]].sum().reindex(ORDEN_FRANJAS).reset_index()
    fr["pct"] = fr["n_lluvia"] / fr["n_registros"] * 100
    fig = px.bar(fr, x="franja", y="pct", text_auto=".2f", color_discrete_sequence=[AZUL],
                 labels={"franja": "", "pct": "% de registros con lluvia"}, custom_data=["n_lluvia", "n_registros"])
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:.2f} %<br>%{customdata[0]:,} de %{customdata[1]:,} "
                                                         "registros<extra></extra>")
    fig.update_layout(bargap=0.45)
    st.plotly_chart(estilo(fig), width="stretch")
    st.caption("Mide frecuencia, no cantidad. Responde a municipio, zona y estaciones en observación, pero no al "
               "periodo: la tabla oro no separa las franjas por mes.")

# ---------------------------------------------------------------- P4
with t4:
    metodo = st.radio("Método", ["Pearson", "Spearman"], horizontal=True)
    dia = datos.pivot_table(index="fecha", columns="codigoestacion", values="precip_mm")
    minimo = round(MIN_DIAS_P4 * dias_periodo / 365)
    principales = sorted(dia.columns[dia.count() >= minimo])
    if len(principales) >= 2:
        nombres = estaciones.set_index("codigoestacion")["nombreestacion"]
        tabla = dia[principales].rename(columns=lambda c: nombres[c].title())
        corr = correlacion(tabla, metodo)
        fig = px.imshow(corr.round(2), text_auto=".2f", color_continuous_scale=DIVERGENTE, zmin=-1, zmax=1, aspect="auto")
        fig.update_traces(xgap=2, ygap=2, hovertemplate="%{y} y %{x}: r = %{z:.2f}<extra></extra>")
        fig.update_xaxes(tickangle=-40, title="")
        fig.update_yaxes(title="")
        st.plotly_chart(estilo(fig, 620), width="stretch")
        pares = corr.values[np.triu_indices(len(principales), k=1)]
        st.caption(f"{len(principales)} estaciones con {minimo} días o más. Promedio entre pares: "
                   f"{numero(np.nanmean(pares), 2)} ({metodo}). Correlación no es causalidad.")
    else:
        st.info(f"Se necesitan al menos dos estaciones con {minimo} días de datos en el periodo.")

# ---------------------------------------------------------------- P5
with t5:
    izq, der = st.columns(2)
    with izq:
        temp = datos.groupby("temporada")["precip_mm"].agg(["mean", "size"]).reindex(["Lluviosa", "Seca"]).dropna().reset_index()
        fig = px.bar(temp, x="temporada", y="mean", color="temporada", color_discrete_map=COLOR_TEMPORADA, text_auto=".2f",
                     labels={"temporada": "", "mean": "mm por día-estación"}, custom_data=["size"])
        fig.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:.2f} mm/día<br>%{customdata[0]:,} días-estación<extra></extra>")
        fig.update_layout(bargap=0.55, showlegend=False)
        st.plotly_chart(estilo(fig), width="stretch")
        if len(temp) == 2 and temp["mean"].iloc[1] > 0:
            dif = (temp["mean"].iloc[0] / temp["mean"].iloc[1] - 1) * 100
            st.caption(f"Diferencia de la temporada lluviosa frente a la seca: {'+' if dif >= 0 else ''}{numero(dif, 1)} %")
    with der:
        z = datos.groupby(["zonahidrografica", "mes"])["precip_mm"].mean().reset_index()
        fig = px.line(z, x="mes", y="precip_mm", color="zonahidrografica", markers=True, color_discrete_map=COLOR_ZONA,
                      labels={"mes": "", "precip_mm": "mm por día-estación", "zonahidrografica": ""})
        fig.update_traces(line_width=2, marker_size=8)
        fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=NOMBRES_MES)
        fig.update_layout(legend=dict(orientation="h", y=1.12, x=0))
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("En todo Boyacá, junio y julio, clasificados como secos, superan a varios meses lluviosos: el supuesto de temporadas "
                   "no encaja igual en todas las zonas.")

# ---------------------------------------------------------------- datos
with t6:
    salida = datos.drop(columns=["mes"]).sort_values(["fecha", "municipio"])
    salida["fecha"] = salida["fecha"].dt.date
    st.caption(f"{numero(len(salida))} filas de lluvia diaria por estación (se muestran 500).")
    st.dataframe(salida.head(500), hide_index=True, width="stretch")
    st.download_button("Descargar CSV filtrado", salida.to_csv(index=False).encode("utf-8-sig"),
                       file_name="lluvia_boyaca_filtrada.csv", mime="text/csv")
