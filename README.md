<img src="./diagrams/images/logo.svg" alt="Transactional Outbox simple diagram" width="250">

# Message Relay Patterns

This repository contains simple educational examples of the [Polling Publisher](https://microservices.io/patterns/data/polling-publisher.html) and [Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html) patterns.

## Motivation

After reading an article about Transactional Outbox pattern on microservices.io, I discorvered that there are no good educational examples of the Transaction Log Tailing and Polling Publisher patterns on either the website or GitHub.
So this repository tries to fill that gap by providing simple examples of these patterns in Python using PostgreSQL as the database and Kafka as the message broker.

## Requirements

- Read articles on microservices.io about [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html), [Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html) and [Polling Publisher](https://microservices.io/patterns/data/polling-publisher.html).
- Minimal knowledge of Python to understand the examples.
- Docker and Docker Compose installed on your machine to run the examples.

## Installing

If you want to run the examples, clone the repository and open it in your terminal:

```bash
git clone https://github.com/bakhoraliev/message-relay-patterns
cd message-relay-patterns
```

## Polling Publisher

<img src="./diagrams/images/polling_publisher.svg" alt="Polling Publisher" width="800">

**Polling Publisher** is one of the simplest implementations of the Message Relay pattern based on periodic polling of the database:

1. The application (e.g., Order Service) writes messages to a special Outbox Table in the database within the same transaction as the business operation.
2. Message Relay component periodically polls this Outbox Table using SQL queries.
3. New messages found are published to the Message Broker (e.g., Kafka).
4. After successful publishing, messages are either deleted from the Outbox Table or marked as processed.

### Advantages

- Simple to implement.
- Works with any SQL database.
- Does not require complex database setup.

### Disadvantages

- Periodic polling causes additional load on the database.
- Message publishing may have delays depending on the polling interval.
- When scaling out, care must be taken to avoid multiple Message Relay instances processing the same messages (using `SELECT _ FOR UPDATE` or similar mechanisms).
- Message delivery ordering can be disrupted when processing in parallel.

### Example

Code for the Polling Publisher example is located in the [polling_publisher](./polling_publisher) directory. To run the example, use Make:

```bash
make up.polling
```

## Transaction Log Tailing

<img src="./diagrams/images/transaction_log_tailing.svg" alt="Transaction Log Tailing" width="800">

**Transaction Log Tailing** is an advanced pattern that leverages reading the database transaction log:

1. The application (e.g., Order Service) writes messages to the Outbox table inside the transaction.
2. Message Relay component reads change records directly from the database transaction log (for example, logical replication with `wal2json` plugin in PostgreSQL) or uses a database-specific feature to stream changes.
3. When new entries appear, Message Relay immediately publishes messages to the Message Broker (e.g., Kafka).

### Advantages

- Reduces load on the database compared to Polling Publisher.
- Lower latency delivery due to near-instant reaction to changes.
- Guarantees message order as per transaction commit order in the database.

### Disadvantages

- Requires specific database configuration (enabling logical replication, installing plugins).
- Increases complexity of deployment and maintenance.
- Scaling is complicated because multiple readers might see the same log entries without a simple way to skip already processed ones.
- Depends on database system capabilities.

### Example

Code for the Transaction Log Tailing example is located in the [transaction_log_tailing](./transaction_log_tailing) directory. To run the example, use Make:

```bash
make up.tailing
```

## Testing the examples

For testing the examples, we need two terminals: one for the watching messages in Kafka and another for inserting test messages into the PostgreSQL Outbox Table. After running the examples, you can follow these steps:

### Watching messages in Kafka

1. Open a terminal and enter Kafka container and start consuming messages:

```bash
make consume KAFKA_TOPIC=tests
```

### Inserting test messages into PostgreSQL Outbox Table

1. Open another terminal and seed the database with one message:

```bash
make seed.one
```

2. or multiple messages:

```bash
make seed.multiple
```

## Links
- Original articles on microservices.io:
  - https://microservices.io/patterns/data/transactional-outbox.html
  - https://microservices.io/patterns/data/transaction-log-tailing.html
  - https://microservices.io/patterns/data/polling-publisher.html
- PostgreSQL documentation on Logical Replication: https://www.postgresql.org/docs/current/logical-replication.html
- wal2json plugin: https://github.com/eulerto/wal2json

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

! Remember that this repository is primarily for educational purposes, and aim to keep the examples simple and easy to understand.

## License

The code in this project is licensed under [The Unlicense](https://unlicense.org/) license.
