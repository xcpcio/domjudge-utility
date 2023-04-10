FROM python:3.11-bullseye

USER root
WORKDIR /domjudge-tools
COPY . /domjudge-tools
COPY ./bin /

ENV DEBIAN_FRONTEND noninteractive

RUN chmod +x /*.sh \
    && pip install -r requirements.txt

ENTRYPOINT ["/docker_entry.sh"]
CMD ["bash"]
