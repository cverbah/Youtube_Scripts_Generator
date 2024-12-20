import os
import pandas as pd
import streamlit as st
import numpy as np
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
import io
import contextlib
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import aiplatform
from langchain_google_genai import GoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from tqdm import tqdm
import fitz  # PyMuPDF for PDFs
from docx import Document
import yt_dlp
import ffmpeg

#envs
load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["LOCATION"]
GCP_API_KEY = os.environ["GCP_API_KEY"]
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'GCP_key.json'

vertexai.init(project=PROJECT_ID, location=LOCATION)


def generate_youtube_summary(video_transcript: str, language: str,
                             model_name="gemini-1.5-flash-002", temperature=1):
    """generates tags for the user prompt"""
    llm = GoogleGenerativeAI(model=model_name, google_api_key=GCP_API_KEY,
                             generation_config={"max_output_tokens": 100,  # max
                                                "temperature": temperature,
                                                "top_p": 0.95,
                                                })

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", [
                f"Resumen del video de YouTube con el siguiente transcript: {video_transcript}. Estructura el resumen en tres secciones:\
                    \
                  Summary: Proporciona un resumen general del video en 2-3 frases, capturando la esencia y el objetivo principal del contenido.\
                    \
                  Highlights: Enumera los puntos más relevantes del video en forma de lista, resaltando los momentos importantes, temas destacados o secciones clave en orden de aparición.\
                    \
                  Key Insights: Lista los conocimientos clave o ideas principales del video que aporten valor, incluyendo cualquier enseñanza práctica, reflexiones o consejos que puedan ser aplicados por el espectador.\
                    \
                  Organiza el contenido para ofrecer una comprensión rápida y precisa de la información.\
                    \
                  **IDIOMA**: EL resumen debe ser en el siguiente idioma: {language}"
            ],
             ),
            ("human", "{input}"),
        ])

    chain = prompt | llm
    return chain


def translate_script(input_language: str, output_language:str,
                     model_name="gemini-1.5-flash-002", temperature=0.9):
    """parses a text to json"""
    llm = GoogleGenerativeAI(model=model_name, google_api_key=GCP_API_KEY,
                             generation_config={"max_output_tokens": 8192,  # max
                                                "temperature": temperature,
                                                "top_p": 0.95,
                                                })
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", [
                f"Se te entregará un guión para un video de youtube.\
                Debes traducir el guión del idioma: {input_language} al idioma: {output_language}. \
                Verifica que el guión traducido no tenga errores y que sea coherente."
            ],
             ),
            ("human", "{input}"),
        ])

    chain = prompt | llm
    return chain


def save_dict_to_txt_download(dictionary):
    return json.dumps(dictionary, ensure_ascii=False, indent=4)

def save_dict_to_txt(dictionary, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=4)


def calculate_length_video(total_minutes):
    """Converts total minutes to a string in the format 'MM:SS'."""
    minutes = int(total_minutes)
    seconds = int((total_minutes - minutes) * 60)
    return f"{minutes:02}:{seconds:02}"  # Format as MM:SS


def youtube_to_mp3(url: str, output_path: str):
    """
    Downloads a YouTube video, extracts its audio, and converts it to MP3 format using yt-dlp.
    """
    try:
        # Step 1: Download the audio using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Rename the downloaded file to output_path
        temp_path = "temp_audio.mp3"
        if os.path.exists(temp_path):
            os.rename(temp_path, output_path)

        print("Download and conversion successful.")
        return output_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def refine_script(parts: int, model_name="gemini-1.5-pro-002", temperature=0.9):
    """parses a text to json"""
    llm = GoogleGenerativeAI(model=model_name, google_api_key=GCP_API_KEY,
                             generation_config={"max_output_tokens": 8192,  # max
                                                "temperature": temperature,
                                                "top_p": 0.95,
                                                })
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", [
                f"Se te entregará un guión para un video de youtube separado en {parts} partes.\
                Debes editarlo de tal forma de asegurar de que el guión tenga coherencia entre todas sus partes. \
                No deben haber ninguna parte del guión con repetición de información."
            ],
             ),
            ("human", "{input}"),
        ])

    chain = prompt | llm
    return chain


def extract_text_from_docx(file):
    """transforms docx to text"""
    doc = Document(file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_text_from_pdf(file):
    """transforms pdf to text"""
    try:
        file_bytes = io.BytesIO(file.read())  # Leer el archivo como bytes
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text("text")
        return text
    except Exception as e:
        return f"Error al extraer texto del PDF: {e}"


def reset_memory():
    """resets assistant memory"""
    st.session_state.ai_assistant = 0
    st.session_state.user_input = ''
    st.session_state.chat_memory = ChatMessageHistory()


def submit_query():
    """submits query"""
    st.session_state.user_input = st.session_state.widget
    st.session_state.widget = ''


def generate_llm_chain_v2(language: str, channel_name: str, parts: int, section: int,  words: int,
                          temperature: float, model_name: str, target_audience: str, video_style: str,
                          context: str, previous_part: str):
    """generates a script for Youtube video"""
    assert 0 <= temperature <= 1, 'temperature must be between 0 and 1'
    llm = GoogleGenerativeAI(model=model_name, google_api_key=GCP_API_KEY,
                             generation_config={"max_output_tokens": 8192,  # max
                                                "temperature": temperature,
                                                "top_p": 0.95,
                                                },
                             safety_settings={
                                 HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                             })
    words_per_section = int(words/parts)+1
    parts_up_to = [i for i in range(1, section+1)]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", [f"Eres un guionista experto en crear contenido para YouTube, enfocado en desarrollar guiones efectivos y originales para el canal {channel_name}.\
                       El idioma del guión será {language}.\
                       El guión estará separado en {parts} partes.\
                       Estás generando la parte: {section} del guión.\
                       El guión que debes continuar  y que corresponde a la parte {section-1} es: {previous_part}.\
                       \
                       **Objetivo:**Crear un guion atractivo y coherente para una audiencia específica: {target_audience}, usando un estilo de narración {video_style} que mantenga la atención del espectador mediante un flujo continuo entre secciones y una estructura de causa-efecto.\
                        \
                      **Desglose y Cohesión de Partes:** \
                        - Desglosa el tema en subtemas lógicos y atractivos que sean relevantes para {target_audience}.Cada subtema debe avanzar hacia la resolución del tema central y conectar fluidamente con la parte anterior del guión: {section-1}.  \
                        - **Continuidad:** La parte: {section} debe ser una continuación directa del guion generado en la parte {section - 1}, sin introducir nuevamente temas ya vistos ni hacer recapitulaciones. Nunca hagas introducciones o conclusiones en cada sección; el objetivo es mantener la narrativa como un solo guion continuo dividido en {parts} partes.\
                        - Crea transiciones naturales entre las partes: {section} con {section - 1}, para que el cambio ocurra de forma imperceptible y se mantenga el interés. Nunca remarques que se inicia una nueva sección.\
                        - **Importante:** En el párrafo inicial de cada parte: {section}, nunca hagas referencia a temas ya tratados en las partes anteriores. El guion debe leerse como un solo texto fluido, sin recordar o resumir el contenido previo.\
                        \
                       **Uso del Contexto:** Basándote en el contexto proporcionado: {context}, construye cada sección del guion en torno a este, evitando repeticiones y manteniendo una narrativa coherente.\
                        \
                        **Técnicas Virales:**\
                        - Introduce elementos que fomenten la curiosidad y el “factor sorpresa,” tales como preguntas intrigantes, datos inesperados o conceptos novedosos en cada parte.\
                        \
                       **Estructura por Parte:**\
                       - **Duración por sección:** Cada seccion debe tener alrededor de: {words_per_section} palabras.\
                       - **Inicio y Cierre:** Solo si es la primera parte (parte 1) incluye una bienvenida en el canal {channel_name}, introduciendo el tema y sus beneficios. Nunca incluyas introducciones en las demás partes. En la última sección, cierra emocionalmente, invitando a los espectadores a seguir viendo y compartiendo el contenido del canal.\
                       - **Interacción con el público:** Incita a suscribirse y anima a comentar usando técnicas de CALL TO ACTION solo en la parte más importante del guión (solo 1 vez en total).\
                        \
                       **Formato por Parte:**\
                       - **Narrador:** Guión narrado para la parte: {section}, siguiendo el siguiente estilo de narración: {video_style}.\
                       - **Imagen o Video:** Sugerencias de imagenes o videos relevantes acorde a al párrafo que se está narrando.\
                       - **Tiempo:** Rango de tiempo estimado para esta sección.\
                        \
                       **Nota 1:** Revisa constantemente las partes previas: {parts_up_to}. Revisa el contenido generado para evitar repeticiones y asegurar coherencia en todo el guión, manteniendo un flujo continuo en la narrativa sin introducciones a la siguiente parte al final de cada sección.\
                       **Nota 2: ** Solo has una introducción en la parte 1 y un cierre del guión en  la parte: {parts} "
                ],
             ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

    chain = prompt | llm
    return chain


def generate_llm_chain(language: str, channel_name: str, parts: int, section: int, time: int,
                       temperature: float, model_name: str, context: str):
    """generates a script for Youtube video"""
    assert 0 <= temperature <= 1, 'temperature must be between 0 and 1'
    llm = GoogleGenerativeAI(model=model_name, google_api_key=GCP_API_KEY,
                             generation_config={"max_output_tokens": 8192,  # max
                                                "temperature": temperature,
                                                "top_p": 0.95,
                                                },
                             safety_settings={
                                 HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                 HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                             })
    sections = int(round(time / parts, 0))
    if section == parts:
        last_section = True

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", [
                f"Eres un experto guionista para videos de Youtube que generará guiones para un determinado canal: {channel_name}. \
                   El idioma del guión debe ser en el siguiente lenguaje: {language}. \
                   El guión debe ser creativo, original y viral, enfocándose en lograr mantener la atención del espectador en todo momento del video. \
                   Desglosa el tema principal del guión en subtemas. Cada subtema debe ser un paso lógico hacia la respuesta o resolución del problema planteado, \
                   conectando bien con la parte anterior: {section - 1}. Si este valor es 0, significa que es la primera parte del guión. \
                   Conecta cada parte: {section} del guión de manera que la siguiente parte surja de forma natural a partir de lo anterior, \
                   sin marcarlo como un nuevo comienzo. Usa frases o conceptos que enlacen ambos puntos sin mencionar explícitamente \
                   que se está avanzando a la siguiente parte, de tal manera que el cambio de una parte a la otra ocurra de forma \
                   orgánica y sin interrupciones visibles. \
                   Usa una estructura de causa-efecto para que cada parte fluya naturalmente a la siguiente parte del guión. \
                   Nunca generes en la última parte del guión una conclusión o resumen del guión. \
                   Cada parte del guión que generes va a tener una duración de {sections} minutos correspondiente a la parte {section} del guión.\
                   Por Ejemplo: Si el guión va a tener una duración total de: 20 minutos y debe tener 10 partes, \
                   cada parte del guión debe tener una duración de 2 minutos: parte 1: del minuto 0 al minuto 2, \
                   parte 2: del minuto 2 al minuto 4, parte 3: del minuto 4 al 6, hasta llegar al parte 10: del minuto 18 al 20. \
                   Si es la primera parte del video, al inicio del guión debes dar una Bienvenida al canal: {channel_name} \
                   diciendo sobre qué tratará el video y cuáles serán los beneficios para el espectador. \
                   Si debes personificar a alguna persona, haz la introducción en primera persona. No hagas introducciones en el resto de las partes. \
                   Si es la parte {parts} del video (la última parte) debes dar un mensaje final sobre el video \
                   procurando cerrar con una conexión emocional, siendo amistoso e invitando a los espectadores a \
                   seguir viendo y compartiendo nuestros videos de nuestro canal. \
                   Asegúrate de incitar a los espectadores a suscribirse en nuestro canal en distintas partes del video \
                   (máximo 2 veces si {time} es mayor a 20 y 1 vez si {time} es menor a 20) mediante el uso de la psicología, \
                   y aplicando técnicas relacionadas al CALL TO ACTION para que los espectadores dejen comentarios en nuestro video."
                f"Estás generando la parte {section} del guión.",
                f"Debes usar como contexto para generar el guión: {context}. Si {context} es '', \
                  No uses contexto para el guión",
                f"Revisa siempre todas las partes anteriores del guión, de forma que no haya información repetida",
                f"El guión debe venir de la siguiente manera:\
                   Imágen: recomendación de imágen o video acorde a la parte {section} del guión.\
                   Debe ser solo UNA recomendación de imágen o video por cada {section}. Recuerda que solo 1 imagén por cada parte del guión, \
                   que se usará para hacer una transición a la siguiente parte del guión.\
                   Narrador: guión de cada sección correspondiente a la parte: {section} del guión,\
                   Tiempo: rango de tiempo para cada sección,\
                   Conteo de palabras: cuenta la cantidad de palabras generadas en Narrador.\
                   Ten en consideración que en promedio deben haber entre 280 a 300 palabras por cada minuto narrado.\
                   Por ejemplo: \
                   Si usas rangos de Tiempo de 1 minuto: 0:00 - 1:00,  la parte {section} del guión deben haber al menos 280 palabras. \
                   Si usas rangos de Tiempo de 2 minutos: 2:00 - 4:00,  la parte {section} del guión deben haber al menos 560 palabras."
            ],
             ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

    chain = prompt | llm
    return chain


def add_memory_chain(chain, chat_history):
    """adds memory for adding more context for the queries """
    # demo_ephemeral_chat_history_for_chain = ChatMessageHistory()

    chain_with_message_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    return chain_with_message_history







