COMPOSE := docker compose
PG_EXEC := $(COMPOSE) exec -T postgres
KAFKA_EXEC := $(COMPOSE) exec -T kafka

.PHONY: help ps up.polling up.tailing stop down reset seed.one seed.multiple consume

help:
	@echo ""
	@echo "Targets:"
	@echo "  ps               Show compose services status"
	@echo "  up.polling       Start PostgreSQL + Kafka + Polling Publisher Message Relay"
	@echo "  up.tailing       Start PostgreSQL + Kafka + Transaction Log Tailing Relay"
	@echo "  stop             Stop containers (keep volumes)"
	@echo "  down             Stop and remove containers (keep volumes)"
	@echo "  reset            Remove containers and volumes (fresh DB)"
	@echo "  seed.one         Run db/seeds/single.sql against Postgres"
	@echo "  seed.multiple    Run db/seeds/multiple.sql against Postgres"
	@echo "  consume          Kafka console consumer (from beginning)"
	@echo ""

ps:
	$(COMPOSE) ps

# Start Polling Publisher Message Relay
up.polling:
	$(COMPOSE) up -d --build polling-publisher-relay

# Start Transaction Log Tailing Message Relay
up.tailing:
	$(COMPOSE) up -d --build transaction-log-tailing-relay

# Stop containers but keep volumes
stop:
	$(COMPOSE) stop

# Stop & remove containers (keep volumes)
down:
	$(COMPOSE) down

# Nuke everything (containers + volumes). Use when you change migrations.
reset:
	$(COMPOSE) down -v

# Seed database with one row
seed.one:
	$(PG_EXEC) psql -U postgres -v ON_ERROR_STOP=1 -f /seeds/single.sql

# Seed database with multiple rows
seed.multiple:
	$(PG_EXEC) psql -U postgres -v ON_ERROR_STOP=1 -f /seeds/multiple.sql

# Kafka console consumer (inside the kafka container).
# Using 'kafka:9092' matches the advertised listener in compose.
consume:
	$(KAFKA_EXEC) /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
		--bootstrap-server kafka:9092 \
		--topic $(KAFKA_TOPIC) \
		--from-beginning
