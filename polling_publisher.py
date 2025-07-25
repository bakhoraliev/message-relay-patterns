import os
import time
from typing import TypedDict

import psycopg2
from kafka import KafkaProducer
from psycopg2.extensions import connection as PsycopgConnection
from psycopg2.extensions import cursor as PsycopgCursor


class OutboxMessage(TypedDict):
    id: str
    topic: str
    key: str | None
    value: str
    headers: list[tuple[str, bytes]] | None
    partition: int | None


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
    return [
        OutboxMessage(
            id=row[0],
            topic=row[1],
            key=row[2],
            value=row[3],
            headers=row[4] if row[4] is not None else [],
            partition=row[5],
        )
        for row in cursor.fetchall()
    ]


def publish_message(producer: KafkaProducer, message: OutboxMessage):
    producer.send(
        topic=message["topic"],
        key=message["key"],
        value=message["value"],
        headers=message["headers"],
        partition=message["partition"],
    )
    producer.flush()  # Ensure the message is sent immediately


def mark_as_processed(cursor: PsycopgCursor, messages: list[OutboxMessage]):
    if not messages:
        return
    message_ids = [msg["id"] for msg in messages]
    cursor.execute(
        """
        UPDATE general.outbox
        SET processed = TRUE
        WHERE id = ANY(%s)
        """,
        (message_ids,),
    )


def polling_publisher(cursor: PsycopgCursor, producer: KafkaProducer):
    messages = poll_messages(cursor)
    processed_messages: list[OutboxMessage] = []
    for message in messages:
        try:
            publish_message(producer, message)
            processed_messages.append(message)
        except:
            continue
    mark_as_processed(cursor, processed_messages)


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
                polling_publisher(cursor, producer)
            time.sleep(5)  # Sleep for 5 seconds before polling again
    finally:
        connection.close()
        producer.close()


if __name__ == "__main__":
    main()
