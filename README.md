= Flight Monitoring & Delay Prediction System

Proyecto distribuido para monitoreo de vuelos en tiempo real y predicción de retrasos utilizando procesamiento paralelo, programación asíncrona y visualización web.

== Características

- Obtención de vuelos sobre México mediante APIs.
- Procesamiento distribuido con *MPI*.
- Conversión de coordenadas geográficas.
- Consultas concurrentes a APIs de clima.
- Predicción de retrasos de vuelos.
- Dashboard HTML en tiempo real.
- Ejecución periódica mediante scheduler asíncrono.

== Arquitectura

#table(
  columns: (auto, auto),
  inset: 8pt,
  align: horizon,
  [*Componente*], [*Descripción*],

  [Scheduler], [Ejecuta el pipeline periódicamente],
  [Rank 0], [Obtiene y distribuye datos],
  [Ranks Workers], [Procesan vuelos en paralelo],
  [Modelo Predictivo], [Predice retrasos usando clima],
  [Dashboard], [Visualiza información en tiempo real],
)

== Flujo del Sistema

- Rank 0 obtiene datos de vuelos.
- Los datos se distribuyen entre ranks usando MPI.
- Cada rank procesa coordenadas.
- Rank 0 junta resultados y escribe archivos.
- Los ranks consultan clima por aeropuerto.
- El modelo genera predicciones de retraso.
- El dashboard actualiza información continuamente.

== Tecnologías

- Python
- asyncio
- mpi4py
- NumPy
- HTML/CSS/JavaScript
- APIs REST

== Ejecución

Ejemplo de ejecución con MPI:

```bash
mpiexec -n 4 python main.py 
