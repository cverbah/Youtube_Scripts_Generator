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

if 'original_text' not in st.session_state:
    st.session_state.original_text = ''
if 'translation' not in st.session_state:
    st.session_state.translation = None

uploaded_file = st.file_uploader("Suba un archivo con el script (txt o word)", type=["txt", "docx"])

if uploaded_file is not None and st.session_state.original_text == '':
    if uploaded_file.type == "text/plain":
        # Handle .txt file
        st.session_state.original_text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Handle .docx file
        doc = Document(uploaded_file)
        st.session_state.original_text = "\n".join([para.text for para in doc.paragraphs])


# Display the original text if loaded
if st.session_state.original_text:
    st.subheader("Script Original")
    st.write(st.session_state.original_text)

if st.button("Translate"):
    with st.spinner(f"Traduciendo Script de {input_lang} a {target_lang}..."):
        translator = translate_script(
            input_language=input_lang,
            output_language=target_lang,
            model_name="gemini-1.5-flash-002",
            temperature=0.9
        )
        # Perform translation and store in session state
        st.session_state.translation = translator.invoke({"input": st.session_state.original_text})

    if st.session_state.translation:
        st.subheader(f"Script traducido en: {target_lang}")
        st.write(st.session_state.translation)

        # Provide download buttons for the translated text
        file_name = f"translated_script_{aux_translates[target_lang]}.txt"
        st.download_button(
            label="Descargar Script traducido como .txt",
            data=st.session_state.translation.encode('utf-8'),
            file_name=file_name,
            mime="text/plain"
        )

