# Precipitación en Boyacá · Dashboard en Streamlit

Dashboard del **Proyecto Integrador de Big Data 2026-2** (Universidad Santo Tomás, Seccional Tunja). Muestra cómo se
distribuye la lluvia en Boyacá durante 2025 por mes, municipio, franja horaria, estación y temporada, a partir de los
registros de precipitación del IDEAM.

**Integrantes:** Jose Julian Tobito Montoya · Andres Felipe Wilches Salas
**Docente:** Martha Susana Contreras Ortiz

## Preguntas que responde

| # | Pregunta | Gráfico |
|---|----------|---------|
| P1 | ¿Cómo varía la precipitación mes a mes y cuáles son los meses con mayor y menor acumulado? | Lluvia por mes y temporada |
| P2 | ¿Qué municipios registran la mayor precipitación acumulada y qué porcentaje del total representan? | Municipios con mayor acumulado · Mapa de estaciones |
| P3 | ¿En qué franja horaria es más frecuente la lluvia? | % de registros con lluvia por franja |
| P4 | ¿Qué tan correlacionada está la lluvia diaria entre las principales estaciones? | Correlación de la lluvia diaria |
| P5 | ¿Cuánto difiere la precipitación entre la temporada lluviosa y la seca? | Lluvia diaria por temporada |

**KPI:** registros analizados, lluvia acumulada, porcentaje de días-estación con lluvia y municipio con mayor acumulado.
**Filtros:** municipio, rango de meses y exclusión de la estación PISBA.

## Estructura

```
dashboard/
├── src/estadisticas/app.py     # aplicación de Streamlit
├── .streamlit/config.toml      # tema claro
├── data/
│   └── oro/                    # tablas agregadas que lee el dashboard
│       ├── oro_mensual.csv     # lluvia por municipio, año y mes
│       ├── oro_franja.csv      # registros con lluvia por franja horaria
│       ├── oro_estaciones.csv  # acumulado y coordenadas por estación
│       └── oro_diario.csv      # lluvia diaria por estación
├── pyproject.toml · uv.lock    # dependencias (uv)
└── requirements.txt            # dependencias (pip / Streamlit Community Cloud)
```

Los CSV de `data/oro/` los genera el notebook de ingesta y limpieza con PySpark (capas bronce → plata → oro).

## Cómo ejecutarlo

Requiere Python 3.12 o superior.

**Con [uv](https://docs.astral.sh/uv/)** (recomendado):

```bash
uv sync
uv run streamlit run src/estadisticas/app.py
```

**Con pip:**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/estadisticas/app.py
```

El dashboard se abre en <http://localhost:8501>.

## Datos

- **Fuente:** Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM). *Precipitación* (s54a-sgyg),
  Portal de Datos Abiertos de Colombia: <https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg>
- **Licencia:** Creative Commons Atribución-CompartirIgual 4.0 Internacional (CC BY-SA 4.0).
- **Filtro:** departamento de Boyacá, 1 de enero a 31 de diciembre de 2025. Descargado el 4 de noviembre de 2026.
- **Volumen:** 2.311.516 registros en bronce; 2.118.725 en plata, tras eliminar 192.791 duplicados.
- **Datos personales:** no contiene; son mediciones de estaciones meteorológicas.

> **Estación PISBA (código 0035215030).** Su sensor registra 118.535 mm en 2025, el 68,8 % de toda la lluvia del
> departamento, con valores repetidos y días de más de 4.000 mm. Es una falla de sensor, por lo que el dashboard la
> excluye por defecto. El interruptor de la barra lateral permite incluirla para comparar.

Los datos del IDEAM son crudos y no están validados por la entidad; los resultados son exploratorios.

## Tecnologías

Python · pandas · NumPy · Plotly · Streamlit · PySpark (en el notebook de procesamiento).
