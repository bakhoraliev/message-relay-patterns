INSERT INTO general.outbox (topic, key, value)
VALUES (
    'tests', NULL, 'Message with ID+1: ' || (SELECT COUNT(*) FROM general.outbox)::text
);