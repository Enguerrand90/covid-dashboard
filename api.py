from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Autoriser toutes les origines (pour que Streamlit puisse appeler l’API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Charger la data une fois à l’ouverture du serveur
df = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c", sep=";")
df["date"] = pd.to_datetime(df["jour"], format='%Y-%m-%d')
df = df[df['date'] >= '2020-01-01']
df['dep_str'] = df['dep'].astype(str).str.zfill(2)

@app.get("/data")
def get_data(
    dept: str = Query("All"),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    d = df.copy()
    if dept != "All":
        d = d[d["dep_str"] == dept]
    if start_date:
        d = d[d["date"] >= start_date]
    if end_date:
        d = d[d["date"] <= end_date]
    return d.to_dict(orient="records")
