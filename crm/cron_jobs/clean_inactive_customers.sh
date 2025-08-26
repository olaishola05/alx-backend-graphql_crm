#!/bin/bash


PROJECT_ROOT="alx_backend_graphql_crm"
LOG_FILE="/tmp/customer_cleanup_log.txt"

cd "$PROJECT_ROOT" || { echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Could not navigate to project root." >> "$LOG_FILE"; exit 1; }

DELETED_COUNT=$(python manage.py shell << EOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from datetime import datetime, timedelta, timezone
from crm.models import Customer, Order

one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

active_customer_ids = Order.objects.filter(
    order_date__gte=one_year_ago
  ).values_list('customer', flat=True).distinct()
inactive_customers_query = Customer.objects.exclude(id__in=active_customer_ids)

deleted_count, _ = inactive_customers_query.delete()

print(deleted_count)
EOF
)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "$TIMESTAMP - Deleted $DELETED_COUNT inactive customers." >> "$LOG_FILE"

echo "Customer cleanup script finished. Check $LOG_FILE for details."