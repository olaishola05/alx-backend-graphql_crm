import asyncio
from datetime import datetime, timedelta, timezone
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

async def send_order_reminders():
    REMINDER_LOG_FILE = "/tmp/order_reminders_log.txt"
    transport = AIOHTTPTransport(url="http://localhost:8000/graphql/")
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        seven_days_ago_iso = seven_days_ago.isoformat()
        
        query = gql(
            """
            query GetRecentOrders($startDate: DateTime!) {
              allOrders(orderDate_DateGte: $startDate) {
                edges {
                  node {
                    id
                    totalAmount
                    orderDate
                    customer {
                      name
                      email
                    }
                    products {
                      edges {
                        node {
                          name
                          price
                        }
                      }
                    }
                  }
                }
              }
            }
            """
        )
        
        print(f"Querying orders with order_date greater than or equal to: {seven_days_ago_iso}")
        result = await session.execute(query, variable_values={"startDate": seven_days_ago_iso})
        
        if result and result.get('allOrders') and result['allOrders']['edges']:
            print("\n--- Recent Orders ---")
            with open(REMINDER_LOG_FILE, 'a') as f:
                for edge in result['allOrders']['edges']:
                    order = edge['node']
                    customer_email = order['customer']['email'] if order['customer'] else 'N/A'
                    log_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    log_message = f"{log_timestamp} - Order ID: {order['id']}, Customer Email: {customer_email}\n"

                    print(f"Order ID: {order['id']}")
                    print(f"  Customer: {order['customer']['name']} ({customer_email})")
                    print(f"  Order Date: {order['orderDate']}")
                    print(f"  Total Amount: {order['totalAmount']}")
                    print("  Products:")
                    for product_edge in order['products']['edges']:
                        product = product_edge['node']
                        print(f"    - {product['name']} (Price: {product['price']})")
                    print("-" * 30)

                    f.write(log_message)
            print(f"Order IDs and customer emails logged to {REMINDER_LOG_FILE}")
        else:
            print("No orders found in the last 7 days.")
        
        print("Order reminders processed!")
        
if __name__ == "__main__":
    asyncio.run(send_order_reminders())