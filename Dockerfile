# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# There is probably a better way to do this, but I just copied the example Dockerfile

# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:latest

WORKDIR /usr/src/app

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
RUN uv sync --locked --compile-bytecode

CMD [ "uv", "run", "./src/YTSpammerPurge.py" ]
