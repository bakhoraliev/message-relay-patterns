import os
import time
from typing import TypedDict

import kafka
import psycopg2
from psycopg2.extensions import cursor as PsycopgCursor


class OutboxMessage(TypedDict):
    id: int
    topic: str
    key: str | None
    value: bytes | None
    headers: list[tuple[str, bytes]] | None
    partition: int | None


def poll_messages(cursor: PsycopgCursor) -> list[OutboxMessage]:
    # `ORDER BY id ASC` ensures that messages are processed in the order they were added.
    cursor.execute(
        """
        SELECT id, topic, key, value, headers, partition
        FROM general.outbox
        WHERE processed = FALSE
        ORDER BY id ASC
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


def publish_message(producer: kafka.KafkaProducer, message: OutboxMessage):
    producer.send(
        topic=message["topic"],
        key=message["key"],
        value=message["value"],
        headers=message["headers"],
        partition=message["partition"],
    )
    producer.flush()  # Ensure the message is sent immediately


def mark_as_processed(cursor: PsycopgCursor, messages: list[OutboxMessage]):
    if messages:
        ids = [msg["id"] for msg in messages]
        cursor.execute(
            """
            UPDATE general.outbox
            SET processed = TRUE
            WHERE id = ANY(%s)
            """,
            (ids,),
        )


def polling_publisher(cursor: PsycopgCursor, producer: kafka.KafkaProducer):
    """
    Implements the Polling Publisher pattern.

    Polls the outbox table for unprocessed messages,
    publishes them to Kafka one by one, and marks them as processed.

    If a message fails to publish, it is skipped,
    and the next message is processed.
    """
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
    db = psycopg2.connect(
        dsn=os.getenv(
            "DATABASE_DSN",
            "postgres://postgres:password@localhost:5432/general",
        ),
    )
    producer = kafka.KafkaProducer(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        ),
    )

    try:
        while True:
            with db.cursor() as cursor:
                polling_publisher(cursor, producer)
            time.sleep(5)  # Sleep for 5 seconds before polling again
    finally:
        db.close()
        producer.close()


if __name__ == "__main__":
    main()
