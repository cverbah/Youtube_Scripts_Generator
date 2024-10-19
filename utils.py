import os
import pandas as pd
import streamlit as st
import numpy as np
import json
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
import matplotlib.pyplot as plt
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

GCP_MODEL_ID = "gemini-1.5-flash-001"


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
                       temperature: float, model_name=GCP_MODEL_ID):
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
                f"Eres un experto guionista para videos de Youtube que generará guiones para un determinado canal: {channel_name}.\
                El guión debe ser creativo, original y viral, enfocándose en lograr mantener la atención del espectador en el video.\
                SIEMPRE piensa paso a paso al generar la parte del guión. Este debe ser un guión bien estructurado, tenga coherencia y \
                cohesión entre las distintas partes del guión.",
                f"Asegúrate de que cada parte del guión tenga suficiente contenido para satisfacer la cantidad de {sections} minutos.",
                f"NUNCA hagas introducciones a la siguiente parte del guión en las últimas narraciones de las distintas partes del guión.\
                Es decir, no debes usar frases como: 'En la próxima parte','En la siguiente parte', 'En los próximos videos', \
                'En la siguiente sección','En el siguiente video' ni ninguna frase similar que sean usadas de introducción o nexo a la siguiente partes del guión. \
                ACUÉRDATE que debes generar UN solo guión dividido en {parts} partes: continuo, coherente, sin repeticiones entre las distintas partes y con cohesión.",
                "Nunca generes en la última parte del guión una conclusión o resumen del guión",
                f"El idioma del guión debe ser en el siguiente lenguaje: {language}.",
                f"El guión va a estar separado en: {parts} partes y en total sumando todas las partes, \
                el guión debe tener un total de {time} minutos. Cada parte del guión que generes va a tener \
                una duración de {sections} minutos correspondiente a la parte {section} del guión. \
                EJEMPLO: Si el guión va a tener una duración total de time: 20 minutos y debe tener 10 partes,\
                cada parte del guión debe tener una duración de 2 minutos: parte 1: del minuto 0 al minuto 2,\
                parte 2: del minuto 2 al minuto 4, parte 3: del minuto 4 al 6, hasta llegar al parte 10: del minuto 18 al 20",
                f"Usa tu memoria para unir todas las partes de forma de que sean coherentes y para que cada parte \
                sea la continuación de la anterior. Por ejemplo: Si es la parte 1, la parte 2 del guión debe ser la continuación de la parte 1,\
                y la parte 3 del guión debe ser la continuación de la parte 2, hasta llegar a la última parte: {parts}, que es la parte final del guión.\
                ES DE SUMA IMPORTANCIA que todas las partes del guión estén relacionadas. RECUERDA que es UN SOLO GUIÓN \
                dividido en {parts} partes, por lo que NUNCA deben haber partes con contenido repetido, ni ambiguos.",
                f"Si es la parte 1 del video, al inicio del guión debes dar una Bienvenida al canal: {channel_name} \
                diciendo sobre qué tratará el video.\
                Si debes personificar a alguna persona, has la introducción en primera persona. No hagas introducciones en el resto de las partes",
                f"Si es la parte {parts} del video (la última parte) debes dar un mensaje final sobre el video \
                 procurando ser amistoso e invitando a los espectadores a seguir viendo videos de nuestro canal",
                "Asegúrate de incitar a los espectadores a suscribirse en nuestro canal en distintas partes del video \
                (máximo 2 veces y mínimo 1 vez en la totalidad del guión) mediante el uso de la psicología, \
                y de aplicar técnicas relacionadas al CALL TO ACTION para que los espectadores dejen comentarios en nuestro video.",
                f"Estás generando la parte {section} del guión.",
                f"El guión debe venir de la siguiente manera:\
                Imágen: recomendación de imágen o video acorde a la parte {section} del guión.\
                Debe ser solo UNA recomendación de imágen o video por cada {section}. Recuerda que solo 1 imagén por cada parte del guión.\
                que se usará para hacer una transición a la siguiente parte del guión.\
                Narrador: guión de cada sección correspondiente a la parte: {section} del guión, \
                Tiempo: rango de tiempo para cada sección",
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







