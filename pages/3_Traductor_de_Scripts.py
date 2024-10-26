import streamlit as st
from utils import *
import pandas as pd
import numpy as np
import json
from io import StringIO
from docx import Document

st.set_page_config(
        page_title="Transcripts Gen",
        page_icon=":robot_face:",
        layout="wide",
    )


st.title(":robot_face: Traductor de Scripts")
# Select target language
input_lang = st.selectbox("Idioma del Script:", ["Español", "Inglés", "Portugués"])
target_lang = st.selectbox("A qué idioma desea traducir?", ["Inglés", "Español", "Francés", "Portugués"])
aux_translates = {} # for saving file
aux_translates['Inglés'] = 'en'
aux_translates['Español'] = 'es'
aux_translates['Francés'] = 'fr'
aux_translates['Portugués'] = 'pr'

uploaded_file = st.file_uploader("Suba un archivo con el script (txt o word)", type=["txt", "docx"])

if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        # Handle .txt file
        text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Handle .docx file
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])

    st.subheader("Script Original")
    st.write(text)
    with st.spinner(f"Traduciendo Script de {input_lang} a {target_lang}.."):
        # Translate the script
        translator = translate_script(input_language=input_lang, output_language=target_lang,
                                      model_name="gemini-1.5-flash-002", temperature=0.9)
        translation = translator.invoke({"input": text})

        # Display the translated text
        st.subheader(f"Script traducido en: {target_lang}")
        st.write(translation)
        save_dict_to_txt(translation, f'translated_script_{aux_translates[target_lang]}.txt')

