import os
import time

import psycopg2
from kafka import KafkaProducer
from psycopg2.extensions import connection as PsycopgConnection
from psycopg2.extensions import cursor as PsycopgCursor


def create_connection(dsn: str) -> PsycopgConnection:
    return psycopg2.connect(dsn)


def create_kafka_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        retries=5,  # Retry up to 5 times
        retry_backoff_ms=1000,  # Retry after 1 second
    )


def poll_messages(cursor: PsycopgCursor):
    cursor.execute(
        """
        SELECT id, topic, key, value, headers, partition
        FROM general.outbox
        WHERE processed = FALSE
        ORDER BY id DESC
        """,
    )
    return cursor.fetchall()


def publish_messages(producer: KafkaProducer, messages):
    for message in messages:
        _, topic, key, value, headers, partition = message
        producer.send(topic, key=key, value=value, headers=headers, partition=partition)
        producer.flush()  # Ensure the message is sent immediately


def mark_as_processed(cursor: PsycopgCursor, message_ids: list[str]):
    if not message_ids:
        return
    cursor.execute(
        """
        UPDATE general.outbox
        SET processed = TRUE
        WHERE id = ANY(%s)
        """,
        (message_ids,),
    )


def main():
    dsn = os.getenv(
        "DATABASE_DSN",
        "postgres://postgres:password@localhost:5432/general",
    )
    kafka_bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092",
    )

    connection = create_connection(dsn)
    producer = create_kafka_producer(kafka_bootstrap_servers)

    try:
        while True:
            with connection.cursor() as cursor:
                messages = poll_messages(cursor)
                publish_messages(producer, messages)
                message_ids = [msg[0] for msg in messages]
                mark_as_processed(cursor, message_ids)
            time.sleep(5)  # Sleep for 5 seconds before polling again
    finally:
        connection.close()
        producer.close()


if __name__ == "__main__":
    main()
