DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_replication_slots WHERE slot_name = 'outbox'
    ) THEN
        PERFORM pg_create_logical_replication_slot('outbox', 'wal2json');
    END IF;
END
$$;