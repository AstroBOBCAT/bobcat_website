FROM postgres:15

# pg_sphere is in the PostgreSQL apt repository that the base image already
# configures, so this is a one-liner with no extra keyring work.
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-15-pgsphere && \
    rm -rf /var/lib/apt/lists/*
