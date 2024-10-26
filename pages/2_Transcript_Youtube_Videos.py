import streamlit as st
from utils import *
import pandas as pd
import numpy as np
import json
import whisper

st.set_page_config(
        page_title="Youtube videos to txt",
        page_icon=":robot_face:",
        layout="wide",
    )

try:
    st.title(':robot_face: Transcript de videos de Youtube')
    st.markdown("<span style='font-size: 16px;'>Ingrese la url del video a transcribir"
                " en el menú de la izquierda</span>",
                unsafe_allow_html=True)

    if 'url_name' not in st.session_state:
        st.session_state.url_name = ''

    st.session_state.url_name = st.text_input("Url del video de Youtbe", value=st.session_state.url_name)
    if st.session_state.url_name != '':
        #st.write(f"Url: {st.session_state.url_name}")
        with st.spinner('Convirtiendo video a mp3..'):
            youtube_to_mp3(url=st.session_state.url_name, output_path='audio.mp3')
            st.write('Listo! Audio Guardado como audio.mp3')
            st.session_state.url_name = ''

            st.markdown("<span style='font-size: 30px;'>Transcript:</span>", unsafe_allow_html=True)
            model = whisper.load_model("base")  # se puede cambiar
            with st.spinner('Generando transcript del video..'):
                result = model.transcribe('audio.mp3')
                save_dict_to_txt(result, 'transcript_all.txt')
                # print(result["text"])
                for i in result["segments"]:
                    # print(f"inicio {i['start']} - termino {i['end']}")
                    #st.write(f"inicio {i['start']} - termino {i['end']}")
                    st.write(i['text'])
                    lenght_video = i['end']

                st.markdown("<span style='font-size: 22px;'>Largo del video:</span>", unsafe_allow_html=True)
                video_length = calculate_length_video(lenght_video/60)
                st.write(video_length)

    if st.session_state.url_name == '':
        st.markdown("<span style='font-size: 30px;'>Mp3 Player</span>", unsafe_allow_html=True)
        # File uploader widget
        uploaded_mp3_file = st.file_uploader("Para probar, suba el audio recién generado...", type=["mp3"])

        # Play the audio file if uploaded
        if uploaded_mp3_file is not None:
            # Display the audio player
            st.audio(uploaded_mp3_file, format="audio/mp3")



except Exception as e:
    st.warning(f'Se ha producido un error: {e}')

