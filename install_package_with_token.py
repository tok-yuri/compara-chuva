import os
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)

start_time = time.time()

logging.info("**************Iniciando instalação do pacote... ")

## para local 
# Obter o token do Secret Manager
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = 'projects/575836213209/secrets/tok_gcp_tools_token/versions/latest'
response = client.access_secret_version(name=name)
token = response.payload.data.decode('UTF-8')
with open('token.txt', 'w', encoding='utf-8') as file:
    file.write(token)

## para cloud
with open('token.txt', 'r', encoding='utf-8') as file:
    token = file.read()


subprocess.run([
    'pip', 'install',
    f'git+https://{token}@github.com/Tempo-OK/tok-gcp-tools.git@main'
])

logging.info(f"**************Instalação concluída em {time.time() - start_time} segundos.")
