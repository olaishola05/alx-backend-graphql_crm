from celery import shared_task
import logging
from datetime import datetime, timezone
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
import asyncio
import requests

logger = logging.getLogger(__name__)

@shared_task
async def generate_crm_report():
    REPORT_LOG_FILE = "/tmp/crm_report_log.txt"

    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql/")
    query = gql(
        """
        query GetCrmReport {
          allCustomers {
            totalCount
          }
          allOrders {
            totalCount
            edges {
              node {
                totalAmount
              }
            }
          }
        }
        """
    )
    
    try:
      async with Client(transport=transport, fetch_schema_from_transport=True) as session:
          result = await session.execute(query)
      customer_count = result.get('allCustomers', {}).get('totalCount', 0)
      order_data = result.get('allOrders', {})
      order_count = order_data.get('totalCount', 0)
      orders = order_data.get('edges', [])

      total_revenue = sum(order['node']['totalAmount'] for order in orders)
      
      log_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
      report_message= (
            f"{log_timestamp} - Report: {customer_count} customers, "
            f"{order_count} orders, ${total_revenue:.2f} revenue.\n"
        )
      
      with open(REPORT_LOG_FILE, 'a') as f:
          f.write(report_message)

      logger.info("Order report generated successfully.")
      logger.info(f"Report Details logged to: {REPORT_LOG_FILE}")

    except Exception as e:
        logger.error(f"Error generating report: {e}")

if __name__ == "__main__":
    asyncio.run(generate_crm_report())
