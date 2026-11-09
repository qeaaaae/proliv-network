#!/bin/bash
curl -s http://127.0.0.1:9091/v1/users | tr ',' '\n' | grep -E 'connections|octets|unique_ips'
