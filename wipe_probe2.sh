#!/usr/bin/env bash
set -u
echo "=== tables t-z ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -c \
"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename >= 'user_payment_methods' ORDER BY 1;"

echo "=== live counts (nonzero only) ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -t -A -F'|' <<'SQL'
DO $$
DECLARE r record; cnt bigint;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename LOOP
    EXECUTE format('SELECT count(*) FROM %I', r.tablename) INTO cnt;
    IF cnt > 0 THEN RAISE NOTICE '%|%', r.tablename, cnt; END IF;
  END LOOP;
END $$;
SQL

echo "=== admin-related env keys in backend ==="
docker exec remnawave-minishop-backend printenv | grep -E '^(ADMIN|ROOT|OWNER)' | sed -E 's/=(.*)/=<set>/'

echo "=== account_roles content ==="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -c \
"SELECT user_id, role FROM account_roles LIMIT 20;" 2>/dev/null || \
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop -c \
"SELECT * FROM account_roles LIMIT 10;"
