import streamlit as st
from utils import *
import whisper
import json
import base64

st.set_page_config(
    page_title="Transcripts Gen",
    page_icon=":robot_face:",
    layout="wide",
)

try:
    st.title(':robot_face: Transcripts de videos/mp3')
    transcript_type = st.selectbox("Seleccione tipo", ['Youtube video', 'Mp3', ''], index=0)
    model = whisper.load_model("base")  # can be changed to a bigger model

    # Initialize session state for URL and transcript results
    if 'url_name' not in st.session_state:
        st.session_state.url_name = ''
    if 'transcript_all_content' not in st.session_state:
        st.session_state.transcript_all_content = None
    if 'transcript_text_content' not in st.session_state:
        st.session_state.transcript_text_content = None

    # Handle YouTube video input
    if transcript_type == 'Youtube video':
        st.subheader('Transcript de videos de Youtube')
        st.markdown("<span style='font-size: 16px;'>Ingrese la url del video a transcribir</span>",
                    unsafe_allow_html=True)
        st.session_state.url_name = st.text_input("Url del video de YouTube", value=st.session_state.url_name)

    # Handle MP3 file upload
    uploaded_mp3_file = None
    if transcript_type == 'Mp3':
        st.subheader('Transcript de mp3')
        uploaded_mp3_file = st.file_uploader("Suba archivo en formato mp3", type=["mp3"])

        # Save uploaded MP3 to disk only if it changes
        if uploaded_mp3_file is not None:
            with open("mp3_temp.mp3", "wb") as f:
                f.write(uploaded_mp3_file.getbuffer())
            st.audio(uploaded_mp3_file, format="audio/mp3")

    # Generate transcript only when button is pressed
    if st.button("Generate Transcript"):
        with st.spinner('Generando transcript del video...'):
            if transcript_type == 'Youtube video' and st.session_state.url_name:
                youtube_to_mp3(url=st.session_state.url_name, output_path='youtube_temp.mp3')
                temp_aux = 'youtube_temp.mp3'
            elif transcript_type == 'Mp3' and uploaded_mp3_file:
                temp_aux = 'mp3_temp.mp3'
            else:
                st.warning("Por favor, ingrese un URL válido o suba un archivo.")
                st.stop()

            # Generate and save transcript
            result = model.transcribe(temp_aux)
            st.session_state.transcript_all_content = save_dict_to_txt_download(result)
            st.session_state.transcript_text_content = save_dict_to_txt_download(result['text'])

            for i in result["segments"]:
                st.write(i['text'])
            st.markdown("<span style='font-size: 22px;'>Largo del video:</span>", unsafe_allow_html=True)
            video_length = calculate_length_video(result["segments"][-1]['end'] / 60)
            st.write(video_length)

    if st.session_state.transcript_all_content:
        st.download_button(
            label="Descargar Full Transcript",
            data=st.session_state.transcript_all_content.encode('utf-8'),
            file_name="transcript_all.txt",
            mime="text/plain"
        )

    if st.session_state.transcript_text_content:
        st.download_button(
            label="Descargar Text-Only Transcript",
            data=st.session_state.transcript_text_content.encode('utf-8'),
            file_name="transcript_text.txt",
            mime="text/plain"
        )

except Exception as e:
    st.warning(f'Se ha producido un error: {e}')