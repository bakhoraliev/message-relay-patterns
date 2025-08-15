BEGIN;
INSERT INTO general.outbox (topic, value)
SELECT
    'test',
    'value_' || i
FROM generate_series(0, 100) AS i;
COMMIT;