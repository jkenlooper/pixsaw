# UPKEEP due: "2025-12-12" label: "Alpine Linux base image" interval: "+3 months"
# podman pull registry.hub.docker.com/library/alpine:3.21.4
# podman image ls --digests alpine
FROM registry.hub.docker.com/library/alpine:3.21.4@sha256:b6a6be0ff92ab6db8acd94f5d1b7a6c2f0f5d10ce3c24af348d333ac6da80685 AS build

RUN echo "Create dev user"; \
  addgroup -g 44444 dev && adduser -u 44444 -G dev -s /bin/sh -D dev

WORKDIR /home/dev/app

RUN echo "apk add package dependencies"; \
  apk update \
  && apk add --no-cache \
    -q --no-progress \
    build-base \
    freetype \
    freetype-dev \
    fribidi \
    fribidi-dev \
    gcc \
    harfbuzz \
    harfbuzz-dev \
    jpeg \
    jpeg-dev \
    lcms2 \
    lcms2-dev \
    libffi-dev \
    libjpeg \
    musl-dev \
    openjpeg \
    openjpeg-dev \
    py3-pip \
    python3 \
    python3-dev \
    tcl \
    tcl-dev \
    tiff \
    tiff-dev \
    tk \
    tk-dev \
    zlib \
    zlib-dev \
    py3-yaml \
  && python -V

RUN echo "Setup for python virtual env"; \
  mkdir -p /home/dev/app \
  && chown -R dev:dev /home/dev/app \
  && su dev -c 'python -m venv /home/dev/app/.venv'

# Activate python virtual env by updating the PATH
ENV VIRTUAL_ENV=/home/dev/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --chown=dev:dev pip-requirements.txt /home/dev/app/pip-requirements.txt

USER dev

RUN echo "Install pip-requirements.txt"; \
  python -m pip install \
    --disable-pip-version-check \
    --no-build-isolation \
    -r /home/dev/app/pip-requirements.txt

COPY --chown=dev:dev pyproject.toml /home/dev/app/pyproject.toml
COPY --chown=dev:dev src/pixsaw/_version.py /home/dev/app/src/pixsaw/_version.py
COPY --chown=dev:dev README.md /home/dev/app/README.md

RUN echo "Download python packages listed in pyproject.toml"; \
  mkdir -p /home/dev/app/dep \
  && python -m pip download --disable-pip-version-check \
    --exists-action i \
    --no-build-isolation \
    --destination-directory /home/dev/app/dep \
    .

RUN echo "Generate the requirements.txt file"; \
  pip-compile \
    --resolver=backtracking \
    --allow-unsafe \
    --extra dev \
    --extra test \
    --output-file ./requirements.txt \
    pyproject.toml

COPY pip-audit.sh /home/dev/app/pip-audit.sh
RUN echo "Audit packages for known vulnerabilities"; \
  /home/dev/app/pip-audit.sh || echo "WARNING: Vulnerabilities found."

CMD ["sh", "-c", "while true; do printf 'z'; sleep 60; done"]


# UPKEEP due: "2025-12-12" label: "Alpine Linux base image" interval: "+3 months"
# podman pull registry.hub.docker.com/library/alpine:3.21.4
# podman image ls --digests alpine
FROM registry.hub.docker.com/library/alpine:3.21.4@sha256:b6a6be0ff92ab6db8acd94f5d1b7a6c2f0f5d10ce3c24af348d333ac6da80685 AS app

RUN echo "Create dev user"; \
  addgroup -g 44444 dev && adduser -u 44444 -G dev -s /bin/sh -D dev

# The chill user is created mostly for backwards compatibility
RUN echo "Create chill user"; \
  addgroup -g 2000 chill \
  && adduser -u 2000 -G chill -s /bin/sh -D chill \
  # Create directory where running chill app database will be.
  && mkdir -p /var/lib/chill/sqlite3 \
  && chown -R chill:chill /var/lib/chill

WORKDIR /home/dev/app

RUN echo "apk add package dependencies"; \
  apk update \
  && apk add --no-cache \
    -q --no-progress \
    build-base \
    freetype \
    freetype-dev \
    fribidi \
    fribidi-dev \
    gcc \
    harfbuzz \
    harfbuzz-dev \
    jpeg \
    jpeg-dev \
    lcms2 \
    lcms2-dev \
    libffi-dev \
    libjpeg \
    musl-dev \
    openjpeg \
    openjpeg-dev \
    py3-pip \
    python3 \
    python3-dev \
    tcl \
    tcl-dev \
    tiff \
    tiff-dev \
    tk \
    tk-dev \
    zlib \
    zlib-dev \
    py3-yaml \
  && python -V

COPY --from=build /home/dev/app /home/dev/app
COPY --chown=dev:dev src/pixsaw/ /home/dev/app/src/pixsaw/
COPY --chown=dev:dev COPYING /home/dev/app/
COPY --chown=dev:dev COPYING.LESSER /home/dev/app/

RUN echo "Init data output dir"; \
  mkdir -p /data/output \
  && chown dev:dev /data/output
VOLUME /data/output

USER dev

# Activate python virtual env by updating the PATH
ENV VIRTUAL_ENV=/home/dev/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN echo "Install pixsaw dependencies"; \
  python -m pip install \
    --disable-pip-version-check \
    --compile \
    --no-build-isolation \
    --find-links="./dep" \
    -r /home/dev/app/requirements.txt

# Using 'csv' for the bandit format since it is the ideal format when committing
# the file to source control.
RUN echo "Use bandit to find common security issues"; \
  bandit \
    --recursive \
    -c pyproject.toml \
    --format csv \
    /home/dev/app/src/ > /home/dev/security-issues-from-bandit.csv || echo "WARNING: Issues found."

RUN echo "Install pixsaw"; \
  python -m pip install --disable-pip-version-check --compile \
    --no-index \
    --no-build-isolation \
    /home/dev/app \
  && pixsaw --version

# For development the app is installed in 'edit' mode. This requires that the
# script start this way.
ENTRYPOINT ["pixsaw"]
CMD ["--help"]
#CMD ["python /home/dev/app/src/pixsaw/script.py"]
