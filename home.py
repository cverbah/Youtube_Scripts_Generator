import streamlit as st
import pandas as pd
import numpy as np
from utils import *
from langchain_community.chat_message_histories import ChatMessageHistory


st.set_page_config(
    page_title="Youtube Scripts GenAI",
    page_icon=":robot_face:",
    layout="wide",
)
st.title(':wrench: Carga de tablas - Cambiar por DOC o PDF (#TODO):')

##
@st.cache_data
def load_dataframe(file_path: str, file):
    try:
        if file_path.endswith('.csv'):
            try:
                df = pd.read_csv(file, index_col=0)
            except:
                df = pd.read_csv(file, index_col=0, delimiter=';')

        elif file_path.endswith(('.xls', '.xlsx')):

            df = pd.read_excel(file, engine='openpyxl', index_col=0)
            # especial pa prueba con json col:
            if 'Información extendida' in df.columns:
                df['Información extendida'] = df['Información extendida'].apply(json.loads)
                json_df = pd.json_normalize(df['Información extendida'])
                df = df.drop(columns=['Información extendida'])
                df = pd.concat([df, json_df], axis=1)

        df = df.convert_dtypes()
        df.columns = (df.columns.str.replace(' ', '_').str.lower().
                      str.normsalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))

        return df

    except Exception as e:
        output = {
            "error": str(e),
        }
        return output
##