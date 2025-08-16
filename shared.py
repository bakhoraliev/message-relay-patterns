"""
Shared utilities for message relay patterns.

This module contains common code used by both Polling Publisher 
and Transaction Log Tailing implementations.
"""
import logging
import os
from typing import TypedDict

import kafka


# Configure logging for all relay components
logging.basicConfig(
    level=logging.INFO,  # Simplified from DEBUG for better readability
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class OutboxMessage(TypedDict):
    """Represents a message from the outbox table."""
    id: int
    topic: str
    key: str | None
    value: str | None
    headers: list[tuple[str, str]] | None
    partition: int | None


def create_kafka_producer() -> kafka.KafkaProducer:
    """Create a configured Kafka producer."""
    return kafka.KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
        key_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
    )


def publish_message(producer: kafka.KafkaProducer, message: OutboxMessage):
    """Publish a message to Kafka."""
    logger = logging.getLogger(__name__)
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