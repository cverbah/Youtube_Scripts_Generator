import streamlit as st
import pandas as pd
import numpy as np
from utils import *
from datetime import datetime, timedelta
from PIL import Image


st.set_page_config(
    page_title="Herramientas para Youtube usando GenAI",
    page_icon=":robot_face:",
    layout="wide",
)
st.title('Bienvenido! En esta aplicación encontrarás herramientas para:')
image = Image.open('./images/banner_option_3.jpeg')

st.markdown("<span style='font-size: 20px;'>1 - Generación de **Scripts** para tus videos</span>",
                unsafe_allow_html=True)
st.markdown("<span style='font-size: 20px;'>2 - Generación de **Descripciones** para tus videos (ToDo)  :building_construction:</span>",
                unsafe_allow_html=True)
st.markdown("<span style='font-size: 20px;'>3 - Generación de **Imágenes** para tus videos (ToDo)  :building_construction:</span>",
                unsafe_allow_html=True)
st.image(image, caption='Genera la vida que siempre deseaste', use_column_width=True)

#@st.cache_data
#def load_dataframe(file_path: str, file):
#    try:
#        if file_path.endswith('.csv'):
#            try:
#                df = pd.read_csv(file, index_col=0)
#            except:
#                df = pd.read_csv(file, index_col=0, delimiter=';')
#
#        elif file_path.endswith(('.xls', '.xlsx')):
#
#            df = pd.read_excel(file, engine='openpyxl', index_col=0)
#
#        df = df.convert_dtypes()
#        df.columns = (df.columns.str.replace(' ', '_').str.lower().
#                      str.normsalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
#
#        return df
#
#    except Exception as e:
#        output = {
#            "error": str(e),
#        }
#        return output


SESSION_TIMEOUT_MINUTES = 15

# Initialize session state variables
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()
    st.session_state.df = None


def check_session_timeout():
    now = datetime.now()
    session_start = st.session_state.session_start
    if now - session_start > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        st.warning("La sesión ha expirado. Vuelva a recargar la página.")
        return False
    return True


def reset_session():
    st.session_state.session_start = datetime.now()
    st.session_state.df = None


# Check session timeout
if check_session_timeout():
    try:
        pass
    #    uploaded_file = st.file_uploader("Seleccione un archivo PDF o Doc (#ToDo)", type=["xlsx", "xls", "csv"])
    #
    #    try:
    #        if uploaded_file:
    #            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, } #"FileSize": uploaded_file.size
    #            st.write(file_details)

    #            # Load file
    #            if 'df' not in st.session_state:
    #                df = load_dataframe(uploaded_file.name, uploaded_file)
    #                st.session_state.df = df
    #            else:
    #                df = load_dataframe(uploaded_file.name, uploaded_file)
    #                st.session_state.df = df
    #
    #            st.subheader("DataFrame Head:")
    #            st.dataframe(st.session_state.df.head(10))
    #
    #            st.subheader("DataFrame Stats:")
    #            st.dataframe(st.session_state.df.describe())
    #
    #    except Exception as e:
    #        st.error(f"Error: {e}")
    #
    except Exception as e:
        st.error(f"Error: {e}")

else:
    # Button to reset the session
    if st.button("Resetear Sesión"):
        reset_session()
        st.experimental_rerun()

