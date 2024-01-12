FROM python:3.11-bullseye

USER root
WORKDIR /domjudge-utility
COPY . /domjudge-utility
COPY ./docker/bin /

ENV DEBIAN_FRONTEND noninteractive

RUN chmod +x /*.sh \
    && pip install -r requirements.txt \
    && cd ./cmd/dump-to-xcpcio && pip install -r requirements.txt \
    && apt update \
    && apt install --no-install-recommends --no-install-suggests -y vim

ENTRYPOINT ["/docker_entry.sh"]
CMD ["bash"]
