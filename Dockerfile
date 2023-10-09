# syntax=docker/dockerfile:1.6.0

# Modified from the original in python-worker directory in https://git.sr.ht/~jkenlooper/cookiecutters .

# UPKEEP due: "2023-12-13" label: "Alpine Linux base image" interval: "+3 months"
# docker pull alpine:3.18.3
# docker image ls --digests alpine
FROM alpine:3.18.3@sha256:7144f7bab3d4c2648d7e59409f15ec52a18006a128c733fcff20d3a4a54ba44a

RUN <<DEV_USER
# Create dev user
set -o errexit
addgroup -g 44444 dev
adduser -u 44444 -G dev -s /bin/sh -D dev
DEV_USER

WORKDIR /home/dev/app

RUN <<PACKAGE_DEPENDENCIES
# apk add package dependencies
set -o errexit
apk update
apk add --no-cache \
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
  py3-yaml
PACKAGE_DEPENDENCIES

RUN  <<PYTHON_VIRTUALENV
# Setup for python virtual env
set -o errexit
mkdir -p /home/dev/app
chown -R dev:dev /home/dev/app
su dev -c '/usr/bin/python -m venv /home/dev/app/.venv'
PYTHON_VIRTUALENV
# Activate python virtual env by updating the PATH
ENV VIRTUAL_ENV=/home/dev/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --chown=dev:dev pip-requirements.txt /home/dev/app/pip-requirements.txt
COPY --chown=dev:dev dep /home/dev/app/dep

USER dev

RUN <<PIP_INSTALL
# Install pip-requirements.txt
set -o errexit
python -m pip install --disable-pip-version-check \
  -r /home/dev/app/pip-requirements.txt
PIP_INSTALL

COPY --chown=dev:dev pyproject.toml /home/dev/app/pyproject.toml
COPY --chown=dev:dev src/pixsaw/_version.py /home/dev/app/src/pixsaw/_version.py
COPY --chown=dev:dev README.md /home/dev/app/README.md
COPY --chown=dev:dev COPYING /home/dev/app/
COPY --chown=dev:dev COPYING.LESSER /home/dev/app/

RUN <<PIP_DOWNLOAD
# Download python packages listed in pyproject.toml
set -o errexit
python -m pip download --disable-pip-version-check \
    --exists-action i \
    --no-build-isolation \
    --find-links /home/dev/app/dep/ \
    --destination-directory /home/dev/app/dep \
    .[dev,test]
PIP_DOWNLOAD

COPY --chown=dev:dev requirements.txt /home/dev/app/requirements.txt
COPY --chown=dev:dev requirements-dev.txt /home/dev/app/requirements-dev.txt
COPY --chown=dev:dev requirements-test.txt /home/dev/app/requirements-test.txt
RUN <<PIP_INSTALL_APP
# Install the local python packages.
set -o errexit

# Only pip install with the local python packages cache.
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements.txt
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements-dev.txt
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements-test.txt
PIP_INSTALL_APP

COPY --chown=dev:dev src /home/dev/app/src
RUN <<PIP_INSTALL_SRC
# Install app source code in editable mode (-e) for local development.
set -o errexit
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -e /home/dev/app
mkdir -p /home/dev/app/output
PIP_INSTALL_SRC


# For development the app is installed in 'edit' mode. This requires that the
# script start this way.
ENTRYPOINT ["pixsaw"]
#CMD ["python /home/dev/app/src/pixsaw/script.py"]
