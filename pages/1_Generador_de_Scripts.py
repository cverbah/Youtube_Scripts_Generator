import streamlit as st
from utils import *
import pandas as pd
import numpy as np

st.set_page_config(
        page_title="Generador de Scripts",
        page_icon=":robot_face:",
        layout="wide",
    )

with st.sidebar:
    st.title(':gear: Parámetros para Script')
    models = ["gemini-1.5-flash-001", "gemini-1.5-flash-002", "gemini-1.5-pro-002"]
    language = ["español", "inglés"]
    time = [10, 15, 20, 25, 30]
    parts = [3, 5, 10, 15, 20, 30]

    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = language[0]

    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = models[1]

    if 'selected_time' not in st.session_state:
        st.session_state.selected_time = time[3]

    if 'selected_parts' not in st.session_state:
        st.session_state.selected_parts = parts[2]

    if 'selected_temperature' not in st.session_state:
        st.session_state.selected_temperature = 0.9

    st.session_state.selected_language = st.radio("Seleccione lenguaje", language,
                                                  index=language.index(st.session_state.selected_language))
    st.session_state.selected_model = st.selectbox("Seleccione modelo", models,
                                                   index=models.index(st.session_state.selected_model))
    st.session_state.selected_time = st.selectbox("Seleccione duración video (mins)", time,
                                                  index=time.index(st.session_state.selected_time))
    st.session_state.selected_parts = st.selectbox("Seleccione cantidad de partes", parts,
                                                   index=parts.index(st.session_state.selected_parts))
    st.session_state.selected_temperature = st.slider("Seleccione Temperatura",
                                                      min_value=0.0, max_value=1.0, step=0.01,
                                                      value=st.session_state.selected_temperature)

try:
    st.title(':robot_face: Generador de Scripts')
    #st.subheader("Primero seleccione los parámetros para la generación del script")
    st.markdown("<span style='font-size: 16px;'>Primero seleccione los parámetros para la generación del script"
                " en el menú de la izquierda</span>",
                unsafe_allow_html=True)

    if 'channel_name' not in st.session_state:
        st.session_state.channel_name = ''

    if 'user_input' not in st.session_state:
        st.session_state.user_input = ''

    st.session_state.channel_name = st.text_input("Ingrese el nombre de su canal", value=st.session_state.channel_name)
    if st.session_state.channel_name != '':
        st.write(f"Nombre del canal: {st.session_state.channel_name}")

    col1, col2 = st.columns([0.8, 0.3], gap='large')
    with col1:
        st.text_input('', key='widget', on_change=submit_query,
                      placeholder='Ingrese el prompt sobre qué tratará su script')
        if st.session_state.user_input:
            st.write(f'Promp utilizado: {st.session_state.user_input}')

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
                script = []
                placeholder = st.empty()
                with st.spinner("Generando Script.."):
                    for i in range(1, st.session_state.selected_parts+1):
                        section = i
                        placeholder.text(f'Generando parte {i}')
                        st.session_state.chain = generate_llm_chain(language=st.session_state.selected_language,
                                                                    channel_name=st.session_state.channel_name,
                                                                    parts=st.session_state.selected_parts,
                                                                    section=section,
                                                                    time=st.session_state.selected_time,
                                                                    temperature=st.session_state.selected_temperature,
                                                                    model_name=st.session_state.selected_model)

                        st.session_state.ai_memory = add_memory_chain(st.session_state.chain, st.session_state.chat_memory)
                        aux = f'Hazme un guión de la parte: {section} del video sobre: {st.session_state.user_input}'
                        if st.session_state.ai_assistant:
                            response = st.session_state.ai_memory.invoke(
                                #{"input": st.session_state.user_input},
                                {"input": aux},
                                {"configurable": {"session_id": "unused"}},
                            )

                        script.append(response)

                    st.write('Script Generado:')
                    for i in script:
                        st.write(i)

        except Exception as e:
            st.warning(f'Se ha producido un error: {e}')

except Exception as e:
    st.warning(f'Se ha producido un error: {e}')
