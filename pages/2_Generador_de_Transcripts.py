import streamlit as st
from utils import *
import pandas as pd
import numpy as np
import json
import whisper

st.set_page_config(
        page_title="Transcripts Gen",
        page_icon=":robot_face:",
        layout="wide",
    )

try:
    st.title(':robot_face: Transcripts de videos/mp3')
    transcript_type = st.selectbox("Seleccione tipo", ['Youtube video', 'Mp3'], index=0)
    model = whisper.load_model("base")  # can be changed to a bigger model
    uploaded_mp3_file = None
    if 'url_name' not in st.session_state:
        st.session_state.url_name = ''

    if transcript_type == 'Youtube video':

        st.subheader('Transcript de videos de Youtube')
        st.markdown("<span style='font-size: 16px;'>Ingrese la url del video a transcribir</span>",
                    unsafe_allow_html=True)
        st.session_state.url_name = st.text_input("Url del video de Youtbe", value=st.session_state.url_name)
        with st.spinner('Convirtiendo video a mp3..'):
            youtube_to_mp3(url=st.session_state.url_name, output_path='youtube_temp.mp3')
            st.write('Listo! Audio Guardado como audio.mp3')
            #st.session_state.url_name = ''

    if transcript_type == 'Mp3':
        st.subheader('Transcript de mp3')
        uploaded_mp3_file = st.file_uploader("Suba archivo en formato mp3", type=["mp3"])

        # Play the audio file if uploaded and save mp3
        if uploaded_mp3_file is not None:
            st.audio(uploaded_mp3_file, format="audio/mp3")
            with open("mp3_temp.mp3", "wb") as f:
                f.write(uploaded_mp3_file.getbuffer())

    if (st.session_state.url_name != '') or (uploaded_mp3_file is not None):

        st.markdown("<span style='font-size: 30px;'>Transcript:</span>", unsafe_allow_html=True)
        with st.spinner('Generando transcript del video..'):
            if transcript_type == 'Youtube video':
                temp_aux = 'youtube_temp.mp3'
            if transcript_type == 'Mp3':
                temp_aux = 'mp3_temp.mp3'

            result = model.transcribe(temp_aux)
            save_dict_to_txt(result, 'transcript_all.txt')
            save_dict_to_txt(result['text'], 'transcript_text.txt')
            # print(result["text"])
            for i in result["segments"]:
                #st.write(f"inicio {i['start']} - termino {i['end']}")
                st.write(i['text'])
                lenght_video = i['end']

            st.markdown("<span style='font-size: 22px;'>Largo del video:</span>", unsafe_allow_html=True)
            video_length = calculate_length_video(lenght_video/60)
            st.write(video_length)

except Exception as e:
    st.warning(f'Se ha producido un error: {e}')




