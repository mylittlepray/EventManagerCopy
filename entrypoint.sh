#!/bin/sh

set -e

if echo "$@" | grep -q "runserver"; then
    echo "Check/Apply database migrations (Web container)..."
    python manage.py migrate --noinput
fi

exec "$@"
