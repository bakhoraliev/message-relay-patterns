<img src="./diagrams/images/logo.svg" alt="Transactional Outbox simple diagram" width="250">

# Message Relay Patterns

This repository contains simple educational examples of the [Polling Publisher](https://microservices.io/patterns/data/polling-publisher.html) and [Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html) patterns.

## Motivation

After reading an article about [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html) pattern on microservices.io, I discorvered that there are no good educational examples of the [Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html) and [Polling Publisher](https://microservices.io/patterns/data/polling-publisher.html) patterns on either the website or GitHub.
So this repository tries to fill that gap by providing simple examples of these patterns in Python using PostgreSQL as the database and Kafka as the message broker.

## Requirements

- Read articles on microservices.io about [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html), [Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html) and [Polling Publisher](https://microservices.io/patterns/data/polling-publisher.html).
- Minimal knowledge of Python to understand the examples.
- Docker and Docker Compose installed on your machine to run the examples.

## Polling Publisher

<img src="./diagrams/images/polling_publisher.svg" alt="Polling Publisher" width="800">

## Transaction Log Tailing

<img src="./diagrams/images/transaction_log_tailing.svg" alt="Transaction Log Tailing" width="800">

## Links

- Original articles on microservices.io:
  - https://microservices.io/patterns/data/transactional-outbox.html
  - https://microservices.io/patterns/data/transaction-log-tailing.html
  - https://microservices.io/patterns/data/polling-publisher.html
- PostgreSQL documentation on Logical Replication: https://www.postgresql.org/docs/current/logical-replication.html
- wal2json plugin: https://github.com/eulerto/wal2json

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

The code in this project is licensed under [The Unlicense](https://unlicense.org/) license.
