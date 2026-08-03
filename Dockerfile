FROM python:3-slim AS builder

RUN apt-get update && \
    apt-get install -y gcc \
    cmake \
    python3-dev \
    libffi-dev \
    libssl-dev \
    build-essential
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Build argument to download AI dependencies
ARG AI_FT=0

RUN if [ $AI_FT -eq "1" ] ; then \
        echo "Downloading AI dependencies..." && \
        pip install --no-cache-dir --user torch huggingface-hub transformers; \
    fi

FROM python:3-slim

WORKDIR /usr/src/app
RUN apt-get update && \
    apt-get install -y libtk8.6 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local

COPY YTSpammerPurge.py ./
ADD Scripts ./Scripts
ADD assets ./assets

CMD [ "python", "./YTSpammerPurge.py" ]
