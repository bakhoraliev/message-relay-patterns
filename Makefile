COMPOSE := docker compose
PG_EXEC := $(COMPOSE) exec -T postgres
KAFKA_EXEC := $(COMPOSE) exec -T kafka

.PHONY: help ps up.polling up.tailing stop down reset seed.one seed.multiple consume

help:
	@echo ""
	@echo "Message Relay Patterns - Make Commands:"
	@echo ""
	@echo "  Basic Operations:"
	@echo "    ps               Show running services"
	@echo "    stop             Stop all services (keep data)"
	@echo "    down             Stop and remove containers (keep data)"
	@echo "    reset            Remove everything including data"
	@echo ""
	@echo "  Start Patterns:"
	@echo "    up.polling       Start Polling Publisher pattern"
	@echo "    up.tailing       Start Transaction Log Tailing pattern"
	@echo ""
	@echo "  Testing:"
	@echo "    seed.one         Insert one test message"
	@echo "    seed.multiple    Insert 100 test messages"
	@echo "    consume          Watch Kafka messages (KAFKA_TOPIC=tests)"
	@echo ""

ps:
	$(COMPOSE) ps

# Start patterns
up.polling:
	$(COMPOSE) up -d --build polling-publisher-relay

up.tailing:
	$(COMPOSE) up -d --build transaction-log-tailing-relay

# Container management
stop:
	$(COMPOSE) stop

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

# Database seeding
seed.one:
	$(PG_EXEC) psql -U postgres -v ON_ERROR_STOP=1 -f /seeds/single.sql

seed.multiple:
	$(PG_EXEC) psql -U postgres -v ON_ERROR_STOP=1 -f /seeds/multiple.sql

# Kafka consumer
consume:
	$(KAFKA_EXEC) /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
		--bootstrap-server kafka:9092 \
		--topic $(or $(KAFKA_TOPIC),tests) \
		--from-beginning
