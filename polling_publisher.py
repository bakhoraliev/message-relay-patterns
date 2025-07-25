import os
import time

import kafka
import psycopg


def create_connection(dsn: str) -> psycopg.Connection:
    """Create a connection to the PostgreSQL database using psycopg."""
    conn = psycopg.connect(dsn)
    return conn


def create_producer(bootstrap_servers: str) -> kafka.KafkaProducer:
    """Create a Kafka producer."""
    producer = kafka.KafkaProducer(bootstrap_servers=bootstrap_servers)
    return producer


def poll_messages(connection: psycopg.Connection):
    """Poll messages from outbox table."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM outbox WHERE processed = FALSE ORDER BY created_at DESC"
    )
    messages = cursor.fetchall()
    return messages


def push_messages(producer: kafka.KafkaProducer, messages):
    """Push messages to Kafka topic."""
    for message in messages:
        producer.send("outbox_topic", value=message)


def mark_processed_messages(connection: psycopg.Connection, messages):
    """Mark messages as processed in the outbox table."""
    cursor = connection.cursor()
    if messages:
        message_ids = tuple(message[0] for message in messages)
        cursor.execute(
            "UPDATE outbox SET processed = TRUE WHERE id IN ANY(%s)", (message_ids,)
        )


def main():
    """Main function to run the message relay."""
    dsn = os.getenv(
        "DATABASE_URL",
        "dbname=your_db user=your_user password=your_password host=localhost port=5432",
    )
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    poll_timeout = int(os.getenv("POLL_TIMEOUT", 5))

    conn = create_connection(dsn)
    producer_instance = create_producer(bootstrap_servers)

    while True:
        messages = poll_messages(conn)
        if messages:
            push_messages(producer_instance, messages)
            mark_processed_messages(conn, messages)

        time.sleep(poll_timeout)


if __name__ == "__main__":
    main()
