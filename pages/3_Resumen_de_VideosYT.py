import streamlit as st
from utils import *
import whisper
import json
import base64

st.set_page_config(
    page_title="Transcripts Summary",
    page_icon=":robot_face:",
    layout="wide",
)

try:
    st.title(':robot_face: Resumen de video de Youtube')
    if st.session_state.transcript_text_content:
        st.success("Perfecto, Ya fue generado un transcript previamente!")
        #st.write(st.session_state.transcript_text_content)

    if st.button('Generar resumen'):
        with st.spinner('Generando resumen'):
            st.session_state.chain_summary = generate_youtube_summary(video_transcript=st.session_state.transcript_text_content,
                                                                      language='español',
                                                                      model_name="gemini-1.5-flash-8b", temperature=0) # gemini-1.5-flash-002
            response = st.session_state.chain_summary.invoke({"input": 'Genera un resumen'})
            st.session_state.video_summary = save_dict_to_txt_download(response)
            st.write(response)

        youtube_url = st.session_state.url_name
        if '/watch?v=' in youtube_url:
            filename = youtube_url.split('/watch?v=')[-1]
        else:
            filename = youtube_url.split('/')[-1]

        if st.session_state.video_summary:
            st.download_button(
                label="Descargar Resumen",
                data=st.session_state.video_summary.encode('utf-8'),
                file_name=f"resumen_video_{filename}.txt",
                mime="text/plain"
            )

except Exception as e:
    st.warning(f'Se ha producido un error: {e}')