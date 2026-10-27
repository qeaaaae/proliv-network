#!/usr/bin/env bash
set -u
echo "=== minishop tables + row counts ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -c "
SELECT t.tablename,
       (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE c.relname=t.tablename AND n.nspname='public' AND c.relkind='r') AS exists_tbl,
       pg_total_relation_size('public.'||t.tablename) AS bytes
FROM pg_tables t WHERE t.schemaname='public' ORDER BY t.tablename;"

echo
echo "=== live row counts ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minisphere -d remnawave_minishop 2>/dev/null <<'SQL' || \
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop <<'SQL'
DO $$
DECLARE r record; cnt bigint;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename LOOP
    EXECUTE format('SELECT count(*) FROM %I', r.tablename) INTO cnt;
    RAISE NOTICE '% = %', r.tablename, cnt;
  END LOOP;
END $$;
SQL
