import logging
import os
import time
from typing import TypedDict

import kafka
import psycopg2
from psycopg2.extensions import cursor as PsycopgCursor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class OutboxMessage(TypedDict):
    id: int
    topic: str
    key: str | None
    value: bytes | None
    headers: list[tuple[str, bytes]] | None
    partition: int | None


def poll_messages(cursor: PsycopgCursor) -> list[OutboxMessage]:
    logger.debug("Polling for unprocessed messages from outbox table.")
    cursor.execute(
        """
        SELECT id, topic, key, value, headers, partition
        FROM general.outbox
        WHERE processed = FALSE
        ORDER BY id ASC
        """,
    )
    rows = cursor.fetchall()
    logger.info("Polled %d unprocessed messages.", len(rows))
    return [
        OutboxMessage(
            id=row[0],
            topic=row[1],
            key=row[2],
            value=row[3],
            headers=row[4] if row[4] is not None else [],
            partition=row[5],
        )
        for row in rows
    ]


def publish_message(producer: kafka.KafkaProducer, message: OutboxMessage):
    logger.info(
        "Publishing message id=%d to topic='%s', partition=%s.",
        message["id"],
        message["topic"],
        message["partition"],
    )
    producer.send(
        topic=message["topic"],
        key=message["key"],
        value=message["value"],
        headers=message["headers"],
        partition=message["partition"],
    )
    producer.flush()  # Ensure the message is sent immediately
    logger.debug("Message id=%d published and flushed.", message["id"])


def mark_as_processed(cursor: PsycopgCursor, messages: list[OutboxMessage]):
    if messages:
        ids = [msg["id"] for msg in messages]
        logger.info("Marking %d messages as processed: %s", len(ids), ids)
        cursor.execute(
            """
            UPDATE general.outbox
            SET processed = TRUE
            WHERE id = ANY(%s)
            """,
            (ids,),
        )
        logger.debug("Messages marked as processed.")


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
        except Exception as e:
            logger.error(
                "Failed to publish message id=%d: %s",
                message["id"],
                str(e),
                exc_info=True,
            )
            continue
    mark_as_processed(cursor, processed_messages)


def main():
    logger.info("Starting polling publisher.")
    db = psycopg2.connect(
        dsn=os.getenv(
            "DATABASE_DSN",
            "postgres://postgres:password@localhost:5432",
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
            logger.debug("Beginning polling cycle.")
            with db.cursor() as cursor:
                polling_publisher(cursor, producer)
            logger.debug("Polling cycle complete. Sleeping for 5 seconds.")
            time.sleep(5)  # Sleep for 5 seconds before polling again
    except KeyboardInterrupt:
        logger.info("Polling publisher interrupted by user. Shutting down.")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", str(e), exc_info=True)
    finally:
        db.close()
        producer.close()
        logger.info("Database and Kafka producer connections closed. Exiting.")


if __name__ == "__main__":
    main()
