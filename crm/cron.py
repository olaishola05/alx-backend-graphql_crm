from datetime import datetime, timedelta, timezone
from gql import Client, gql
import asyncio
from gql.transport.requests import RequestsHTTPTransport

async def log_crm_heartbeat():
  HEART_BEAT_LOG = "/tmp/crm_heartbeat_log.txt"
  transport = RequestsHTTPTransport(url="http://localhost:8000/graphql/")
  
  async with Client(transport=transport, fetch_schema_from_transport=True) as session:
      query = gql(
          """
          query {
            hello
          }
          """
      )
      
      result = await session.execute(query)
      if result and result.get('hello') == 'Hello, world!':
          with open(HEART_BEAT_LOG, 'a') as f:
              log_timestamp = datetime.now(timezone.utc).strftime('%d/%m/%Y-%H:%M:%S')
              f.write(f"{log_timestamp} - CRM is alive\n")
          print(f"CRM is alive at {log_timestamp}")
      else:
          with open(HEART_BEAT_LOG, 'a') as f:
              log_timestamp = datetime.now(timezone.utc).strftime('%d/%m/%Y-%H:%M:%S')
              f.write(f"{log_timestamp} - CRM is not responding\n")
          print(f"CRM is not responding at {log_timestamp}")


async def update_low_stock():
    transport = AIOHTTPTransport(url="http://localhost:8000/graphql/")
    LOW_STOCK_LOGS = "/tmp/low_stock_updates_log.txt"
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        mutation = gql(
            """
            mutation UpdateLowStockProducts($threshold: Int!) {
              updateLowStockProducts(threshold: $threshold) {
                updated_count
                message
                low_stock_products {
                  id
                  name
                  stock
                }
                errors {
                  field
                  message
                }
              }
            }
            """
        )
        variables = {"threshold": 5}
        result = await session.execute(mutation, variable_values=variables)

        with open(LOW_STOCK_LOGS, 'a') as f:
            log_timestamp = datetime.now(timezone.utc).strftime('%d/%m/%Y-%H:%M:%S')
            if result and result.get('updateLowStockProducts'):
                updated_products = result['updateLowStockProducts'].get('low_stock_products', [])
                for product in updated_products:
                    f.write(f"{log_timestamp} - Updated {product['name']} to {product['stock']} units\n")
            else:
                f.write(f"{log_timestamp} - No products updated\n")


if __name__ == "__main__":
    asyncio.run(log_crm_heartbeat())
    asyncio.run(update_low_stock())