#!/bin/bash
docker exec remnawave-minishop-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT user_id, panel_user_uuid, hwid_device_limit, extra_hwid_devices, status_from_panel, provider, is_active FROM subscriptions LIMIT 15;"'
