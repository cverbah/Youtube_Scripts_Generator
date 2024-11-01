import streamlit as st
from utils import *
import pandas as pd
import numpy as np
import json

st.set_page_config(
        page_title="Scripts Gen",
        page_icon=":robot_face:",
        layout="wide",
    )

with st.sidebar:
    st.title(':gear: Parámetros para Script')
    models = ["gemini-1.5-flash-002", "gemini-1.5-pro-002", "gemini-1.5-flash-8b"]
    language = ["español", "inglés"]
    audience = ["Público general", "Público interesado en desarrollo personal",
                "Público interesado en desarrollo personal y el autoconocimiento"
                "Practicantes de meditación y mindfulness", "Exploradores de la mente y sueños",
                "Personas en búsqueda de bienestar emocional"]
    script_style = ["Storytelling", "Guía paso a paso", "Desmitificación", "Meditación guiada", "Comparación y elección"
                    "Análisis o exploración de temas"]

    words = [1000, 1500, 2000, 3000, 3500, 4000, 5000, 6000]
    parts = [1, 3, 5, 7, 10, 15, 20, 30]

    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = language[0]

    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = models[0]

    if 'selected_words' not in st.session_state:
        st.session_state.selected_words = words[3]

    if 'selected_parts' not in st.session_state:
        st.session_state.selected_parts = parts[0]

    if 'selected_audience' not in st.session_state:
        st.session_state.selected_audience = audience[0]

    if 'selected_script_style' not in st.session_state:
        st.session_state.selected_script_style = script_style[0]

    if 'selected_temperature' not in st.session_state:
        st.session_state.selected_temperature = 0.9

    st.session_state.selected_language = st.radio("Seleccione lenguaje", language,
                                                  index=language.index(st.session_state.selected_language))
    st.session_state.selected_audience = st.selectbox("Seleccione tipo de audiencia", audience,
                                                  index=audience.index(st.session_state.selected_audience))
    st.session_state.selected_script_style = st.selectbox("Seleccione estilo", script_style,
                                                   index=script_style.index(st.session_state.selected_script_style))
    st.session_state.selected_model = st.selectbox("Seleccione modelo", models,
                                                   index=models.index(st.session_state.selected_model))
    st.session_state.selected_words = st.selectbox("Seleccione cantidad de palabras", words,
                                                  index=words.index(st.session_state.selected_words))
    st.session_state.selected_parts = st.selectbox("Seleccione cantidad de partes", parts,
                                                   index=parts.index(st.session_state.selected_parts))
    st.session_state.selected_temperature = st.slider("Seleccione Temperatura",
                                                      min_value=0.0, max_value=1.0, step=0.01,
                                                      value=st.session_state.selected_temperature)

try:
    st.title(':robot_face: Generador de Scripts')
    st.markdown("<span style='font-size: 16px;'>Primero seleccione los parámetros para la generación del script"
                " en el menú de la izquierda</span>",
                unsafe_allow_html=True)

    if 'channel_name' not in st.session_state:
        st.session_state.channel_name = ''

    if 'user_input' not in st.session_state:
        st.session_state.user_input = ''

    if 'context' not in st.session_state:
        st.session_state.context = ''

    st.session_state.channel_name = st.text_input("Ingrese el nombre de su canal", value=st.session_state.channel_name)
    if st.session_state.channel_name != '':
        st.write(f"Nombre del canal: {st.session_state.channel_name}")

    st.markdown("<span style='font-size: 20px;'>Contexto para prompt (Solo si lo necesita): </span>", unsafe_allow_html=True)

    st.session_state.context_file = st.file_uploader("Suba un archivo PDF o Word", type=["pdf", "docx"])
    if st.session_state.context_file:
        if st.session_state.context_file.name.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(st.session_state.context_file)
            st.write("Texto extraído del PDF para usar como contexto")
        elif st.session_state.context_file.name.endswith(".docx"):
            extracted_text = extract_text_from_docx(st.session_state.context_file)
            st.write("Texto extraído del Word para usar como contexto")

        st.session_state.context = extracted_text

    col1, col2 = st.columns([0.8, 0.3], gap='large')
    with col1:
        st.text_input('', key='widget', on_change=submit_query,
                      placeholder='Generame un script sobre:')
        if st.session_state.user_input:
            st.write(f'Prompt utilizado: {st.session_state.user_input}')

    with col2:
        st.write('')
        st.button('Empezar de nuevo', on_click=reset_memory)

    if st.session_state.user_input != '':
        try:

            if 'ai_assistant' not in st.session_state:
                st.session_state.ai_assistant = 0

            if st.session_state.ai_assistant == 0:
                st.session_state.chat_memory = ChatMessageHistory()
                st.session_state.ai_assistant = 1

            if st.button('Generar Script:'):
                script = []
                placeholder = st.empty()
                with st.spinner("Generando Script.."):
                    previous_part = "**Inicio del Guión**"
                    for i in range(1, st.session_state.selected_parts+1):
                        section = i
                        placeholder.text(f'Generando parte {i}')
                        st.session_state.chain = generate_llm_chain_v2(language=st.session_state.selected_language,
                                                                       channel_name=st.session_state.channel_name,
                                                                       parts=st.session_state.selected_parts,
                                                                       words=st.session_state.selected_words,
                                                                       target_audience=st.session_state.selected_audience,
                                                                       video_style=st.session_state.selected_script_style,
                                                                       temperature=st.session_state.selected_temperature,
                                                                       model_name=st.session_state.selected_model,
                                                                       context=st.session_state.context,
                                                                       section=section,
                                                                       previous_part=previous_part)

                        st.session_state.ai_memory = add_memory_chain(st.session_state.chain, st.session_state.chat_memory)
                        aux = (f'Hazme la parte: {section} del guión sobre: {st.session_state.user_input}. '
                               f'El guión debe ser uno solo y estará separado en {st.session_state.selected_parts} partes manteniendo '
                               f'un solo guión de forma continua')

                        if st.session_state.ai_assistant:
                            response = st.session_state.ai_memory.invoke(
                                #{"input": st.session_state.user_input},
                                {"input": aux},
                                {"configurable": {"session_id": "unused"}},
                            )
                            previous_part = response

                        script.append(response)

                    st.write('Script Generado:')
                    for i in script:
                        st.write(i)

        except Exception as e:
            st.warning(f'Se ha producido un error: {e}')

except Exception as e:
    st.warning(f'Se ha producido un error: {e}')
