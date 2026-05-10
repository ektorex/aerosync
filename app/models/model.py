import json
import random
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

# =========================================================
# FEATURES QUE EL MODELO VA A UTILIZAR
# =========================================================

FEATURES = [
    "region",
    "country",
    "lat",
    "lon",
    "temp_c",
    "is_day",
    "condition_code",
    "wind_kph",
    "wind_degree",
    "pressure_mb",
    "precip_mm",
    "humidity",
    "cloud",
    "feelslike_c",
    "dewpoint_c",
    "vis_km",
    "uv",
    "gust_kph",
    "chance_of_rain",
    "chance_of_snow",
    "short_rad",
    "diff_rad",
    "dni",
    "gti"
]

# =========================================================
# EXTRAER FEATURES DESDE EL JSON
# =========================================================

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

# =========================================================
# CARGAR JSONS
# =========================================================

FILES = [
    ("AICM", "predict_AICM.json"),
    ("CUN", "predict_CUN.json"),
    ("GDL", "predict_GDL.json"),
    ("MTY", "predict_MTY.json"),
    ("TIJ", "predict_TIJ.json")
]

rows = []

for codigo, file in FILES:

    with open(file, "r") as f:
        raw = json.load(f)

    # adaptar al formato completo
    wrapped = {
        "codigo": codigo,
        "data": raw
    }

    features = extract_features(wrapped)

    # =====================================================
    # GENERAR RETRASO ARTIFICIAL
    # =====================================================

    delay = (
        features["humidity"] * 0.25 +
        features["cloud"] * 0.35 +
        features["wind_kph"] * 0.80 +
        features["gust_kph"] * 0.60 +
        features["chance_of_rain"] * 0.90 +
        features["precip_mm"] * 8 -
        features["vis_km"] * 1.5 -
        features["pressure_mb"] * 0.03 +
        random.uniform(-5, 5)
    )

    delay = max(0, delay)

    features["delay_minutes"] = delay

    rows.append(features)

# =========================================================
# DATA AUGMENTATION
# generar mas ejemplos sintéticos
# =========================================================

dataset = []

for row in rows:

    for _ in range(300):

        r = row.copy()

        r["temp_c"] += np.random.normal(0, 4)
        r["wind_kph"] += np.random.normal(0, 8)
        r["gust_kph"] += np.random.normal(0, 10)

        r["humidity"] = np.clip(
            r["humidity"] + np.random.normal(0, 10),
            0,
            100
        )

        r["cloud"] = np.clip(
            r["cloud"] + np.random.normal(0, 15),
            0,
            100
        )

        r["chance_of_rain"] = np.clip(
            r["chance_of_rain"] + np.random.normal(0, 20),
            0,
            100
        )

        # recalcular retraso
        r["delay_minutes"] = (
            r["humidity"] * 0.25 +
            r["cloud"] * 0.35 +
            r["wind_kph"] * 0.80 +
            r["gust_kph"] * 0.60 +
            r["chance_of_rain"] * 0.90 +
            r["precip_mm"] * 8 -
            r["vis_km"] * 1.5 -
            r["pressure_mb"] * 0.03 +
            np.random.normal(0, 6)
        )

        r["delay_minutes"] = max(0, r["delay_minutes"])

        dataset.append(r)

df = pd.DataFrame(dataset)

# =========================================================
# FEATURES / TARGET
# =========================================================

X = df[FEATURES]
y = df["delay_minutes"]

# =========================================================
# COLUMNAS
# =========================================================

categorical_features = [
    "region",
    "country"
]

numeric_features = [
    col for col in FEATURES
    if col not in categorical_features
]

# =========================================================
# PREPROCESSOR
# =========================================================

preprocessor = ColumnTransformer([
    (
        "num",
        Pipeline([
            ("imputer", SimpleImputer(strategy="median"))
        ]),
        numeric_features
    ),

    (
        "cat",
        Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]),
        categorical_features
    )
])

# =========================================================
# MODELO
# =========================================================

model = Pipeline([
    ("preprocessor", preprocessor),

    ("regressor", RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42
    ))
])

# =========================================================
# TRAIN
# =========================================================

model.fit(X, y)

# =========================================================
# GUARDAR MODELO
# =========================================================

joblib.dump(model, "flight_delay_model.pkl")

print("modelo guardado")

# =========================================================
# FUNCION DE PREDICCION
# =========================================================

def predict_delay(input_data):

    features = extract_features(input_data)

    df = pd.DataFrame([features])

    prediction = model.predict(df)[0]

    return {
        "codigo": input_data["codigo"],
        "region": input_data["data"]["location"]["region"],
        "delay_minutes": round(float(prediction), 2)
    }

# =========================================================
# EJEMPLO
# =========================================================

with open("predict_AICM.json", "r") as f:
    raw = json.load(f)

example = {
    "codigo": "AICM",
    "data": raw
}

result = predict_delay(example)

print(result)
