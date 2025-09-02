import streamlit as st
import pandas as pd
import numpy as np
import ast
import json
import joblib

def clean_embedding(x):
    """Clean and convert embedding data to numpy array"""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    if isinstance(x, (list, np.ndarray)):
        return np.asarray(x, dtype=np.float32)
    s = str(x).strip()
    if s.lower() in {"none", "null", "nan", ""}:
        return None
    for parser in (lambda y: ast.literal_eval(y), lambda y: json.loads(y.replace(" ", ",")), lambda y: [float(tok) for tok in y.strip("[]").replace(",", " ").split()]):
        try:
            return np.asarray(parser(s), dtype=np.float32)
        except Exception:
            continue
    return None

@st.cache_data()
def load_data():
    """Load and preprocess movie data"""
    df = pd.read_csv("data/movie_data.csv")
    df["text_embedding"] = df["text_embedding"].apply(clean_embedding)
    df = df[df["text_embedding"].notna()].reset_index(drop=True)
    return df

@st.cache_data()
def load_model():
    """Load the clustering model"""
    return joblib.load("data/kmeans_model.pkl") 