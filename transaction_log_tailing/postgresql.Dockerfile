FROM postgres:17

# Install the wal2json output plugin for logical replication
RUN apt-get update && \
    apt-get install -y postgresql-17-wal2json && \
    rm -rf /var/lib/apt/lists/*

# Configure PostgreSQL to allow logical replication
RUN echo "wal_level = logical" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "max_wal_senders = 1" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "max_replication_slots = 1" >> /usr/share/postgresql/postgresql.conf.sample
