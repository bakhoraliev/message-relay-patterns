import json
import logging
import os
from typing import TypedDict

import kafka
import psycopg2
from psycopg2.extras import (LogicalReplicationConnection, ReplicationCursor,
                             ReplicationMessage)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class OutboxMessage(TypedDict):
    id: int
    topic: str
    key: str | None
    value: str | None
    headers: list[tuple[str, str]] | None
    partition: int | None


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


def parse_replication_message(
    replication_message: ReplicationMessage,
) -> list[OutboxMessage]:
    logger.info("Parsing replication message: %s", replication_message.payload)
    parsed_payload = json.loads(
        replication_message.payload
    )  # Assume wal2json plugin is used
    outbox_messages = []
    for change in parsed_payload.get("change", []):
        if (
            change["kind"] == "insert"
            and change["schema"] == "general"
            and change["table"] == "outbox"
        ):
            outbox_messages.append(
                OutboxMessage(
                    **dict(
                        zip(
                            change["columnnames"],
                            change["columnvalues"],
                        )
                    )
                )
            )
    return outbox_messages


def transaction_log_tailing(
    replication_slot: str, cursor: ReplicationCursor, producer: kafka.KafkaProducer
):
    """
    Implements the Transaction Log Tailing pattern.

    Starts a logical replication stream from the specified replication slot,
    and consumes changes from the database. Consumer function processes each
    replication message by parsing it, selecting only `insert` changes, and publishing
    them to Kafka one by one. Acknowledgment is sent back to the database after each
    message is processed.
    """

    def consumer(replication_message: ReplicationMessage):
        logger.debug("Consuming replication message: %s", replication_message.payload)
        outbox_messages = parse_replication_message(replication_message)
        for outbox_message in outbox_messages:
            publish_message(producer, outbox_message)
        cursor.send_feedback(
            flush_lsn=replication_message.data_start,
            reply=True,
        )
        logger.debug("Sent feedback for replication message: %s", replication_message)

    cursor.start_replication(slot_name=replication_slot, decode=True)
    cursor.consume_stream(consumer)


def main():
    logger.info("Starting transaction log tailing.")
    replication_slot_name = os.getenv("REPLICATION_SLOT_NAME", "outbox")
    db = psycopg2.connect(
        dsn=os.getenv(
            "DATABASE_DSN",
            "postgres://postgres:password@localhost:5432",
        ),
        connection_factory=LogicalReplicationConnection,
    )
    producer = kafka.KafkaProducer(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        ),
        value_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
        key_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
    )

    try:
        with db.cursor() as cursor:
            transaction_log_tailing(replication_slot_name, cursor, producer)
    except KeyboardInterrupt:
        logger.info("Transaction log tailing interrupted by user. Shutting down.")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", str(e), exc_info=True)
    finally:
        db.close()
        producer.close()
        logger.info("Database and Kafka producer connections closed. Exiting.")


if __name__ == "__main__":
    main()
