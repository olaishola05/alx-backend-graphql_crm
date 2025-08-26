from datetime import datetime, timedelta, timezone
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio
from gql.transport.requests import RequestsHTTPTransport

async def log_crm_heartbeat():
  HEART_BEAT_LOG = "/tmp/crm_heartbeat_log.txt"
  transport = AIOHTTPTransport(url="http://localhost:8000/graphql/")
  
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


if __name__ == "__main__":
    asyncio.run(log_crm_heartbeat())