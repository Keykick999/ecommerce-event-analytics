import os
import time
import json
import random
import psycopg2
from faker import Faker
from datetime import datetime
from uuid import uuid4

# Configuration (Matching docker-compose.yml)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "database": "analytics_db",
    "user": "user",
    "password": "password",
    "port": 5432
}

fake = Faker()

class EventGenerator:
    def __init__(self):
        self.conn = self.connect_db()
        self.products = self.get_products()
        self.categories = list(set([p[2] for p in self.products]))
        print(f"Initialized with {len(self.products)} products across {len(self.categories)} categories.")

    def connect_db(self):
        while True:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                return conn
            except Exception as e:
                print(f"Waiting for DB... ({e})")
                time.sleep(2)

    def get_products(self):
        cur = self.conn.cursor()
        cur.execute("SELECT product_id, name, category, price FROM products;")
        return cur.fetchall()

    def generate_event(self):
        user_id = f"user_{random.randint(1, 1000)}"
        session_id = str(uuid4())
        
        # 1. Pick a random category first to decide user intent
        category = random.choice(self.categories)
        target_products = [p for p in self.products if p[2] == category]
        
        # 2. Simulate User Journey
        # Search -> View -> Add to Cart -> Purchase
        
        # A. Search Event
        if random.random() > 0.3:
            search_query = fake.word() if category == 'Food' else f"latest {category} model"
            self.insert_event(user_id, session_id, 'search', None, {
                "query_string": search_query,
                "selected_type": category,
                "result_count": random.randint(0, 50)
            })

        # B. View & Conversion Logic
        for product in random.sample(target_products, k=random.randint(1, 3)):
            p_id, p_name, p_cat, p_price = product
            
            # Record VIEW
            self.insert_event(user_id, session_id, 'page_view', p_id, {
                "url": f"/products/{p_id}",
                "referrer": "google.com"
            })
            
            # Decide if ADD TO CART
            # Higher chance for Food, lower for Electronics
            cart_chance = 0.6 if p_cat == 'Food' else 0.2
            if random.random() < cart_chance:
                self.insert_event(user_id, session_id, 'add_to_cart', p_id, {
                    "quantity": random.randint(1, 3),
                    "price_at_event": float(p_price)
                })
                
                # Decide if PURCHASE
                # High conversion from cart for Food
                purchase_chance = 0.8 if p_cat == 'Food' else 0.3
                if random.random() < purchase_chance:
                    order_id = str(uuid4())
                    self.insert_event(user_id, session_id, 'purchase', p_id, {
                        "order_id": order_id,
                        "total_amount": float(p_price),
                        "payment_method": random.choice(['credit_card', 'apple_pay', 'mobile_billing'])
                    })

    def insert_event(self, user_id, session_id, event_type, product_id, metadata):
        cur = self.conn.cursor()
        query = """
            INSERT INTO events (user_id, session_id, event_type, product_id, metadata, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            user_id, 
            session_id, 
            event_type, 
            product_id, 
            json.dumps(metadata), 
            fake.user_agent()
        ))
        self.conn.commit()
        print(f"Logged: {event_type} for User {user_id} (Category: {metadata.get('selected_type', 'N/A')})")

    def run(self, count=100):
        for _ in range(count):
            self.generate_event()
            time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    gen = EventGenerator()
    print("Starting data generation...")
    gen.run(500) # Generate 500 session flows
    print("Finished generation.")
