# Utilisez l'image Python officielle en tant que base
FROM python:3.10

# Définissez le répertoire de travail dans le conteneur
WORKDIR /app

# Copiez les fichiers requis dans le conteneur
ADD requirements.txt .

# Installez les dépendances
RUN apt-get update && pip install --no-cache-dir -r requirements.txt

# Copiez le reste de l'application dans le conteneur
COPY ./src/ ./src/

COPY ./metronome-sounds/ ./metronome-sounds/

RUN pip install natten==0.17.3+torch220cu121 -f https://shi-labs.com/natten/wheels

RUN pip install git+https://github.com/CPJKU/madmom && pip install allin1

RUN apt-get install -y ffmpeg 

EXPOSE 9090
# Commande par défaut pour exécuter votre application
# CMD ["streamlit", "run", "app.py"]

RUN cd ./src/

CMD ["bash", "-c", "cd ./src/ && streamlit run app.py --server.port 9090"]