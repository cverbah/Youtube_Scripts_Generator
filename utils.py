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

#envs
load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["LOCATION"]
GCP_API_KEY = os.environ["GCP_API_KEY"]
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'GCP_key.json'

vertexai.init(project=PROJECT_ID, location=LOCATION)


def reset_memory():
    """resets assistant memory"""
    st.session_state.ai_assistant = 0
    st.session_state.user_input = ''
    st.session_state.chat_memory = ChatMessageHistory()


def submit_query():
    """submits query"""
    st.session_state.user_input = st.session_state.widget
    st.session_state.widget = ''


def generate_llm_chain(language: str, channel_name: str, parts: int, section: int, time: int,
                       temperature: float, model_name: str):
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
                f"El guión debe venir de la siguiente manera:\
                   Imágen: recomendación de imágen o video acorde a la parte {section} del guión.\
                   Debe ser solo UNA recomendación de imágen o video por cada {section}. Recuerda que solo 1 imagén por cada parte del guión, \
                   que se usará para hacer una transición a la siguiente parte del guión.\
                   Narrador: guión de cada sección correspondiente a la parte: {section} del guión,\
                   Tiempo: rango de tiempo para cada sección,\
                   Conteo de palabras: cuenta la cantidad de palabras generadas en Narrador.\
                   Ten en consideración que en promedio deben haber entre 250 a 300 palabras por cada minuto narrado.\
                   Por ejemplo: para Tiempo: 0:00 - 1:00 del guión deben haber al menos 250 palabras."
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







