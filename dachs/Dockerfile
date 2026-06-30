FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget gnupg ca-certificates postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# GAVO packages are not on PyPI — install from GAVO's own Debian repo.
# The distribution name is literally "release" (not a Debian codename).
RUN wget -qO /tmp/gavo-keyring.asc \
        http://vo.ari.uni-heidelberg.de/debian/gavo-archive-keyring.asc && \
    gpg --dearmor -o /usr/share/keyrings/gavo-archive-keyring.gpg \
        /tmp/gavo-keyring.asc && \
    rm /tmp/gavo-keyring.asc && \
    echo "deb [signed-by=/usr/share/keyrings/gavo-archive-keyring.gpg] \
http://vo.ari.uni-heidelberg.de/debian release main" \
        > /etc/apt/sources.list.d/gavo.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3-gavo && \
    rm -rf /var/lib/apt/lists/*

ENV GAVO_ROOT=/var/gavo

# gavo init checks for the 'gavo' system group; create it to avoid that failure
RUN groupadd --system gavo && useradd --system --gid gavo --no-create-home gavo

RUN mkdir -p /var/gavo/logs /var/gavo/inputs

COPY inputs/ /var/gavo/inputs/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
