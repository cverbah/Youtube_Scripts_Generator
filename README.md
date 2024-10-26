# Youtube Tools for Automated channels
<img src="./images/banner_option_3.jpeg" alt="Logo" width="800" height="400">
Built using:<br>

- Modal Cloud, Streamlit, Langchain, LLM models: Gemini 1.5 Pro & Flash  (for now)
<br>

You need:
- To set up a modal account (if you want to deploy the app) [Modal: Serverless platform for AI teams](https://modal.com/)
- To have a GCP account with the Vertex AI API enabled for using the LLM Models
- A service account key saved as GCP_key.json in the project folder <br>

<br>
For deploying the app using Modal cloud: <br>
1. `pip install -r requirements.txt`
2. `Create a API token in your Modal Workspace`
3. `modal serve serve_streamlit.py`    For serving the app OR
4. `modal deploy serve_streamlit.py` For deploying the app in the modal cloud
<br>

For running the app in your local PC: <br>:
0. `pip install git+https://github.com/openai/whisper.git`
1. `pip install -r requirements.txt`
2. `streamlit run Inicio.py`

