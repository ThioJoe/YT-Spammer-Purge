FROM python:3

WORKDIR /usr/src/app
RUN apt update
RUN apt install -y python3-tk
ADD Scripts ./Scripts
ADD assets ./assets
COPY requirements.txt YTSpammerPurge.py ./
RUN pip install --no-cache-dir -r requirements.txt



CMD [ "python", "./YTSpammerPurge.py" ]
