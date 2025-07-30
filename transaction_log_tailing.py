import json
import logging
import os
from typing import Callable, TypedDict

import kafka
import psycopg2
from psycopg2.extras import LogicalReplicationConnection, ReplicationMessage

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


TransactionLogConsumer = Callable[[ReplicationMessage], None]


class OutboxMessage(TypedDict):
    id: int
    topic: str
    key: str | None
    value: str | None
    headers: list[tuple[str, str]] | None
    partition: int | None


def create_transaction_log_consumer(
    producer: kafka.KafkaProducer,
) -> TransactionLogConsumer:

    def consume(replication_message: ReplicationMessage):
        replication_message_payload = json.loads(
            replication_message.data.decode("utf-8")
        )
        outbox_message = OutboxMessage(
            id=replication_message_payload["id"],
            topic=replication_message_payload["topic"],
            key=replication_message_payload["key"],
            value=replication_message_payload["value"],
            headers=replication_message_payload["headers"],
            partition=replication_message_payload["partition"],
        )
        producer.send(
            topic=outbox_message["topic"],
            key=outbox_message["key"],
            value=outbox_message["value"],
            headers=outbox_message["headers"],
            partition=outbox_message["partition"],
        )
        producer.flush()
        replication_message.cursor.send_feedback(
            flush_lsn=replication_message.data_start
        )

    return consume


def main():
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
            cursor.start_replication(slot_name=..., decode=True)
            cursor.consume_stream(
                create_transaction_log_consumer(producer),
            )
    except KeyboardInterrupt:
        logger.info("Transaction log tailing interrupted by user. Shutting down.")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", str(e), exc_info=True)
    finally:
        db.close()
        producer.close()


if __name__ == "__main__":
    main()
