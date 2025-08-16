import json
import logging
import os
import sys

import psycopg2
from psycopg2.extras import (LogicalReplicationConnection, ReplicationCursor,
                             ReplicationMessage)

# Add parent directory to path to import shared module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import OutboxMessage, create_kafka_producer, publish_message

logger = logging.getLogger(__name__)




def parse_replication_message(replication_message: ReplicationMessage) -> list[OutboxMessage]:
    """Parse wal2json replication message and extract outbox messages."""
    logger.info("Parsing replication message: %s", replication_message.payload)
    parsed_payload = json.loads(replication_message.payload)  # Assume wal2json plugin is used
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


def transaction_log_tailing(replication_slot: str, cursor: ReplicationCursor, producer):
    """
    Implements the Transaction Log Tailing pattern.

    Starts a logical replication stream from the specified replication slot,
    and consumes changes from the database. Processes each replication message 
    by parsing it and publishing outbox messages to Kafka.
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
    """Main function to run the transaction log tailing."""
    logger.info("Starting transaction log tailing.")
    replication_slot_name = os.getenv("REPLICATION_SLOT_NAME", "outbox")
    db = psycopg2.connect(
        dsn=os.getenv("DATABASE_DSN", "postgres://postgres:password@localhost:5432"),
        connection_factory=LogicalReplicationConnection,
    )
    producer = create_kafka_producer()

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
