import psycopg2
import uuid
import random
from datetime import datetime, timedelta

# Database connection parameters
PGHOST = "viaduct.proxy.rlwy.net"
PGPORT = "30155"
PGUSER = "postgres"
PGPASSWORD = "oZWIMrGbUFgwtuHhHKKrGwxjsoXaLDcS"
PGDATABASE = "railway"

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=PGHOST,
    port=PGPORT,
    user=PGUSER,
    password=PGPASSWORD,
    database=PGDATABASE
)
cursor = conn.cursor()

# Constants
USER_ID = '79eb44a9-8745-4a15-af1d-12c6bd3d4aeb'
BOT_ID = '1e0bd9f2-6449-445f-ab59-7c29d8a6e83f'
COUNTRIES = ['USA', 'CAN', 'MEX', 'GBR', 'NGA', 'DEU']  # Add more as needed
PLATFORMS = ['Paystack', 'Stripe', 'CoinPayments', 'Nowpayment']
DURATIONS = [14, 30, 99999]
FIRST_NAMES = [
    'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Hank', 'Ivy', 'Jack',
    'Karen', 'Leo', 'Chimaje', 'Abba', 'Timi', 'Evangeline', 'Kaobi', 'Georgia',
    'Adebayo', 'Zainab', 'Kwame', 'Fatima', 'Chinedu', 'Ngozi', 'Kofi', 'Amara',
    'Binta', 'Jelani'
]

# Helper functions
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_transaction_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=9))

def create_customer(cursor, first_names):
    customer_id = uuid.uuid4()
    first_name = random.choice(first_names)
    first_names.remove(first_name)  # Remove the selected first name to ensure uniqueness
    created_at = datetime.now()
    updated_at = created_at
    telegram_id = random.randint(100000, 999999)  # Random telegram ID
    
    cursor.execute("""
        INSERT INTO public.customer(
            id, "firstName", "telegramId", "createdAt", "updatedAt", "userId", "botId")
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, (str(customer_id), first_name, telegram_id, created_at, updated_at, USER_ID, BOT_ID))
    
    return customer_id

def create_transaction(cursor, customer_id):
    transaction_id = str(uuid.uuid4())
    trans_id = random_transaction_id()
    status = 'SUCCESS'
    platform = random.choice(PLATFORMS)
    if platform == 'Paystack':
        currency = 'NGN'
        amount = random.randint(32000, 100000)
    else:
        currency = 'USD'
        amount = random.randint(100, 300)
    
    created_at = random_date(datetime(2024, 1, 1), datetime(2024, 7, 31))
    updated_at = created_at
    country = random.choice(COUNTRIES)
    duration = random.choice(DURATIONS)
    
    cursor.execute("""
        INSERT INTO public.transaction(
            id, "transactionId", status, currency, platform, "createdAt", "updatedAt", "customerId", country, amount, duration)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (transaction_id, trans_id, status, currency, platform, created_at, updated_at, str(customer_id), country, amount, duration))

# Main function to create customers and transactions
def main(num_customers, transactions_per_customer):
    first_names_copy = FIRST_NAMES.copy()  # Create a copy of the first names list to avoid modifying the original
    if num_customers > len(first_names_copy):
        raise ValueError("Number of customers exceeds the number of unique first names available.")
    
    for _ in range(num_customers):
        customer_id = create_customer(cursor, first_names_copy)
        for _ in range(transactions_per_customer):
            create_transaction(cursor, customer_id)
    
    # Commit the transactions
    conn.commit()
    print(f"Inserted {num_customers} customers with {transactions_per_customer} transactions each.")

if __name__ == "__main__":
    main(13, 50)  # Adjust the numbers as needed
    cursor.close()
    conn.close()
