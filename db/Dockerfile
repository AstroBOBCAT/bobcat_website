FROM docker.io/library/postgres:15

#USER root

#RUN groupadd -r myuser && useradd -r -g myuser -m -d /home/myuser -s /sbin/nologin myuser

# pg_sphere is in the PostgreSQL apt repository that the base image already
# configures, so this is a one-liner with no extra keyring work.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-15-pgsphere \
        postgresql-15-q3c && \
    rm -rf /var/lib/apt/lists/*

#USER myuser
