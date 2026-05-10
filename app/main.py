#! /usr/bin/env mpiexec -n 4 python main.py

from mpi4py import MPI

import aiohttp
import asyncio
import json
import joblib
import numpy as np
import pandas as pd
import requests
import time

from ingestion.async_client import AsyncAPIClient
from ingestion.scheduler import Scheduler

from mpi.master import distribute, collect

from config.var import *


model = joblib.load("models/flight_delay_model.pkl")


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

client = AsyncAPIClient()


def extract_features(data):

    location = data["data"]["location"]
    current = data["data"]["current"]

    return {
        "region": location.get("region"),
        "country": location.get("country"),
        "lat": location.get("lat"),
        "lon": location.get("lon"),

        "temp_c": current.get("temp_c"),
        "is_day": current.get("is_day"),
        "condition_code": current["condition"].get("code"),

        "wind_kph": current.get("wind_kph"),
        "wind_degree": current.get("wind_degree"),

        "pressure_mb": current.get("pressure_mb"),
        "precip_mm": current.get("precip_mm"),

        "humidity": current.get("humidity"),
        "cloud": current.get("cloud"),

        "feelslike_c": current.get("feelslike_c"),
        "dewpoint_c": current.get("dewpoint_c"),

        "vis_km": current.get("vis_km"),
        "uv": current.get("uv"),

        "gust_kph": current.get("gust_kph"),

        "chance_of_rain": current.get("chance_of_rain"),
        "chance_of_snow": current.get("chance_of_snow"),

        "short_rad": current.get("short_rad"),
        "diff_rad": current.get("diff_rad"),
        "dni": current.get("dni"),
        "gti": current.get("gti")
    }


def predict_delay(input_data):

    features = extract_features(input_data)

    df = pd.DataFrame([features])

    prediction = model.predict(df)[0]

    return {
        "codigo": input_data["codigo"],
        "region": input_data["data"]["location"]["region"],
        "delay_minutes": round(float(prediction), 2)
    }

def get_w():
    # SOLO rank 0 divide
    if rank == 0:
        chunks = np.array_split(aeropuertos, size)
    else:
        chunks = None

    # repartir chunks
    local_chunk = comm.scatter(chunks, root=0)

    resultados_locales = []

    # cada rank procesa su parte
    for codigo, lat, lon in local_chunk:

        params = {
            'key': API_KEY,
            'q': f'{lat},{lon}',
            'days': '1',
            'aqi': 'no',
            'alerts': 'no'
        }

        response = requests.get(URL, params=params)

        # data = response.json()

        data = {
            "codigo": codigo,
            "data": response.json()
        }
            
        result = predict_delay(data)

        resultados_locales.append(result)

    # juntar resultados
    resultados = comm.gather(resultados_locales, root=0)

    # solo rank 0 reconstruye y guarda
    if rank == 0:

        # flatten
        resultados_completos = []

        for parte in resultados:
            resultados_completos.extend(parte)

        with open("dashboard/predict.json", "w") as f:
            json.dump(resultados_completos, f, indent=4)

def get_f():

    if rank == 0:
        params = {
        'api_key': API_F,
        'bbox': '13.667338,-118.608398,33.063924,-84.682617'
        }
        method = 'flights'
        api_base = 'http://airlabs.co/api/v9/'
        api_result = requests.get(api_base+method, params)
        api_response = api_result.json()

# Extraer response
        response = api_response.get("response", [])

# distribute
        chunks = np.array_split(response, size)
    else:
        chunks = None 
    data = comm.scatter(chunks, root=0)
    return data


async def pipeline():

    data = get_f()
   
    processed = distribute(data)

    final = collect(processed)

async def main():
    
    
    await pipeline()

    get_w()
    
    scheduler = Scheduler(
        interval=30,
        callback=pipeline
    )


    time.sleep(15)
    await scheduler.start()
    

asyncio.run(main())
