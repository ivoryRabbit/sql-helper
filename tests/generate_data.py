"""
Fake data generator for text-to-SQL testing.
Produces CSV files under tests/data/ that simulate Trino-exposed tables.

Assumed Trino catalog/schema:  ecommerce.public.<table>

Tables:
  ecommerce.public.categories   — product hierarchy (2 levels)
  ecommerce.public.products     — product catalog with price & stock
  ecommerce.public.customers    — registered buyers
  ecommerce.public.orders       — order headers with status & total
  ecommerce.public.order_items  — line items linking orders ↔ products
  ecommerce.public.reviews      — customer product reviews with ratings

Run:
    python tests/generate_data.py
"""

import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def write_csv(filename: str, rows: list[dict], fieldnames: list[str]) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>5} rows → {path}")


# ── categories ────────────────────────────────────────────────────────────────
# Two-level hierarchy: parent_id is NULL for root categories.

CATEGORY_TREE = {
    "Electronics":    ["Smartphones", "Laptops", "Tablets", "Accessories"],
    "Clothing":       ["Men", "Women", "Kids", "Sports"],
    "Home & Kitchen": ["Furniture", "Appliances", "Cookware", "Bedding"],
    "Books":          ["Fiction", "Non-Fiction", "Science", "Technology"],
    "Sports":         ["Outdoor", "Fitness", "Team Sports", "Water Sports"],
}

def gen_categories() -> list[dict]:
    rows = []
    cid = 1
    id_map: dict[str, int] = {}

    for parent, children in CATEGORY_TREE.items():
        rows.append({"id": cid, "name": parent, "parent_id": None})
        id_map[parent] = cid
        cid += 1
        for child in children:
            rows.append({"id": cid, "name": child, "parent_id": id_map[parent]})
            id_map[child] = cid
            cid += 1

    return rows, id_map


# ── products ──────────────────────────────────────────────────────────────────

PRODUCT_TEMPLATES = {
    "Smartphones":   [("iPhone 15", 999), ("Galaxy S24", 899), ("Pixel 8", 699),
                      ("OnePlus 12", 649), ("Xiaomi 14", 599)],
    "Laptops":       [("MacBook Pro 14", 1999), ("Dell XPS 15", 1599), ("ThinkPad X1", 1499),
                      ("Surface Laptop 5", 1299), ("ASUS ZenBook", 1099)],
    "Tablets":       [("iPad Pro 12.9", 1099), ("Galaxy Tab S9", 849), ("Surface Pro 9", 999),
                      ("Kindle Fire HD", 149), ("Lenovo Tab P12", 349)],
    "Accessories":   [("AirPods Pro", 249), ("USB-C Hub", 49), ("Wireless Charger", 39),
                      ("Phone Case", 19), ("Screen Protector", 12)],
    "Men":           [("Slim Fit Jeans", 59), ("Oxford Shirt", 45), ("Chino Pants", 55),
                      ("Puffer Jacket", 129), ("Polo Shirt", 39)],
    "Women":         [("Floral Dress", 69), ("Skinny Jeans", 65), ("Blouse", 49),
                      ("Winter Coat", 149), ("Yoga Pants", 55)],
    "Kids":          [("Denim Shorts", 29), ("T-Shirt Pack 3", 35), ("Sneakers", 45),
                      ("Rain Jacket", 59), ("School Backpack", 39)],
    "Sports":        [("Running Shoes", 89), ("Sport Socks 5-Pack", 19), ("Compression Tights", 49),
                      ("Cap", 25), ("Gym Bag", 45)],
    "Furniture":     [("Office Desk", 299), ("Ergonomic Chair", 399), ("Bookshelf", 149),
                      ("Sofa 3-Seater", 799), ("Coffee Table", 199)],
    "Appliances":    [("Air Fryer", 99), ("Robot Vacuum", 299), ("Espresso Machine", 249),
                      ("Stand Mixer", 349), ("Microwave", 149)],
    "Cookware":      [("Cast Iron Pan", 59), ("Non-stick Set 5pc", 89), ("Dutch Oven", 119),
                      ("Cutting Board Set", 39), ("Knife Block Set", 129)],
    "Bedding":       [("Queen Duvet Set", 89), ("Memory Foam Pillow", 49), ("Mattress Topper", 129),
                      ("Blackout Curtains", 69), ("Bed Sheet Set", 55)],
    "Fiction":       [("The Last Kingdom", 14), ("Project Hail Mary", 16), ("Dune", 18),
                      ("The Midnight Library", 13), ("Normal People", 12)],
    "Non-Fiction":   [("Atomic Habits", 17), ("Sapiens", 19), ("The Body", 22),
                      ("Thinking Fast and Slow", 18), ("Educated", 15)],
    "Science":       [("A Brief History of Time", 16), ("The Selfish Gene", 15), ("Cosmos", 20),
                      ("The Gene", 22), ("Astrophysics for People", 14)],
    "Technology":    [("Clean Code", 35), ("The Pragmatic Programmer", 40), ("DDIA", 55),
                      ("Python Crash Course", 38), ("Designing Data-Intensive", 50)],
    "Outdoor":       [("Hiking Backpack 40L", 119), ("Tent 2-Person", 179), ("Sleeping Bag", 89),
                      ("Trekking Poles", 59), ("Headlamp", 39)],
    "Fitness":       [("Yoga Mat", 39), ("Resistance Band Set", 29), ("Dumbbell 10kg", 49),
                      ("Pull-up Bar", 35), ("Jump Rope", 19)],
    "Team Sports":   [("Football", 29), ("Basketball", 35), ("Volleyball", 25),
                      ("Tennis Racket", 89), ("Badminton Set", 49)],
    "Water Sports":  [("Swim Goggles", 25), ("Swim Cap", 12), ("Snorkel Set", 55),
                      ("Surfboard Leash", 29), ("Waterproof Bag", 35)],
}

def gen_products(category_id_map: dict[str, int]) -> list[dict]:
    rows = []
    pid = 1
    start = datetime(2022, 1, 1)
    end = datetime(2024, 12, 31)

    for cat_name, items in PRODUCT_TEMPLATES.items():
        cat_id = category_id_map[cat_name]
        for name, base_price in items:
            price = round(base_price * random.uniform(0.9, 1.1), 2)
            rows.append({
                "id":             pid,
                "name":           name,
                "category_id":    cat_id,
                "price":          price,
                "stock_quantity": random.randint(0, 200),
                "is_active":      random.random() > 0.05,
                "created_at":     fmt(rand_date(start, end)),
            })
            pid += 1

    return rows


# ── customers ─────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James", "Olivia", "Liam", "Emma", "Noah", "Ava", "William", "Sophia",
    "Benjamin", "Isabella", "Lucas", "Mia", "Henry", "Charlotte", "Alexander",
    "Amelia", "Mason", "Harper", "Ethan", "Evelyn", "Daniel", "Abigail",
    "Logan", "Emily", "Sebastian", "Ella", "Jackson", "Elizabeth", "Aiden",
    "Camila", "Mateo", "Luna", "Jack", "Sofia", "Owen", "Avery", "Theodore",
    "Mila", "Elijah", "Aria", "Jayden", "Scarlett", "Julian", "Penelope",
    "Muhammad", "Layla", "David", "Riley", "Ryan", "Zoey",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]
CITIES = [
    ("New York", "US"), ("Los Angeles", "US"), ("Chicago", "US"),
    ("Houston", "US"), ("Phoenix", "US"), ("Philadelphia", "US"),
    ("San Antonio", "US"), ("San Diego", "US"), ("Dallas", "US"),
    ("San Jose", "US"), ("London", "GB"), ("Manchester", "GB"),
    ("Birmingham", "GB"), ("Toronto", "CA"), ("Vancouver", "CA"),
    ("Montreal", "CA"), ("Sydney", "AU"), ("Melbourne", "AU"),
    ("Berlin", "DE"), ("Hamburg", "DE"), ("Munich", "DE"),
    ("Paris", "FR"), ("Lyon", "FR"), ("Tokyo", "JP"), ("Osaka", "JP"),
    ("Seoul", "KR"), ("Singapore", "SG"), ("Dubai", "AE"),
]

def gen_customers(n: int = 500) -> list[dict]:
    rows = []
    start = datetime(2020, 1, 1)
    end = datetime(2024, 12, 31)
    emails: set[str] = set()

    for cid in range(1, n + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@example.com"
        suffix = 1
        while email in emails:
            email = f"{base_email}{suffix}@example.com"
            suffix += 1
        emails.add(email)

        city, country = random.choice(CITIES)
        rows.append({
            "id":            cid,
            "first_name":    first,
            "last_name":     last,
            "email":         email,
            "city":          city,
            "country":       country,
            "registered_at": fmt(rand_date(start, end)),
        })

    return rows


# ── orders & order_items ──────────────────────────────────────────────────────

ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled", "refunded"]
STATUS_WEIGHTS  = [5, 10, 15, 55, 10, 5]

def gen_orders_and_items(
    customers: list[dict],
    products: list[dict],
    n_orders: int = 2000,
) -> tuple[list[dict], list[dict]]:
    orders = []
    items = []
    item_id = 1

    start = datetime(2023, 1, 1)
    end = datetime(2025, 4, 30)

    active_products = [p for p in products if p["is_active"]]

    for oid in range(1, n_orders + 1):
        customer = random.choice(customers)
        status = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        created_at = rand_date(start, end)

        n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5], k=1)[0]
        chosen = random.sample(active_products, min(n_items, len(active_products)))

        order_total = 0.0
        for product in chosen:
            qty = random.randint(1, 4)
            unit_price = product["price"]
            items.append({
                "id":         item_id,
                "order_id":   oid,
                "product_id": product["id"],
                "quantity":   qty,
                "unit_price": unit_price,
            })
            order_total += qty * unit_price
            item_id += 1

        orders.append({
            "id":          oid,
            "customer_id": customer["id"],
            "status":      status,
            "total_amount": round(order_total, 2),
            "created_at":  fmt(created_at),
        })

    return orders, items


# ── reviews ───────────────────────────────────────────────────────────────────

REVIEW_BODIES = [
    "Great product, exactly as described.",
    "Good value for the price.",
    "Works perfectly for my needs.",
    "Delivery was fast and packaging was secure.",
    "Quality is decent but could be better.",
    "Would definitely buy again.",
    "A bit overpriced but the quality is there.",
    "Five stars, no complaints.",
    "Had some issues at first but it works now.",
    "Excellent build quality, highly recommend.",
    "Not what I expected, but still okay.",
    "Customer support was very helpful.",
    "Looks exactly like the photos.",
    "Very satisfied with this purchase.",
    "Disappointed with the quality for this price.",
    "Shipping took longer than expected but product is great.",
    "Perfect gift, recipient loved it.",
    "Easy to set up and use.",
    "Sturdy and well-made.",
    "Exceeded my expectations.",
]

def gen_reviews(
    customers: list[dict],
    products: list[dict],
    orders: list[dict],
    n: int = 1500,
) -> list[dict]:
    rows = []
    start = datetime(2023, 3, 1)
    end = datetime(2025, 4, 30)
    delivered_orders = [o for o in orders if o["status"] == "delivered"]

    for rid in range(1, n + 1):
        customer = random.choice(customers)
        product = random.choice(products)
        rating = random.choices([1, 2, 3, 4, 5], weights=[3, 5, 12, 35, 45], k=1)[0]
        rows.append({
            "id":           rid,
            "customer_id":  customer["id"],
            "product_id":   product["id"],
            "rating":       rating,
            "body":         random.choice(REVIEW_BODIES),
            "helpful_votes": random.randint(0, 80),
            "created_at":   fmt(rand_date(start, end)),
        })

    return rows


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Generating test data …")

    categories, cat_id_map = gen_categories()
    write_csv("categories.csv", categories,
              ["id", "name", "parent_id"])

    products = gen_products(cat_id_map)
    write_csv("products.csv", products,
              ["id", "name", "category_id", "price", "stock_quantity", "is_active", "created_at"])

    customers = gen_customers(500)
    write_csv("customers.csv", customers,
              ["id", "first_name", "last_name", "email", "city", "country", "registered_at"])

    orders, order_items = gen_orders_and_items(customers, products, 2000)
    write_csv("orders.csv", orders,
              ["id", "customer_id", "status", "total_amount", "created_at"])
    write_csv("order_items.csv", order_items,
              ["id", "order_id", "product_id", "quantity", "unit_price"])

    reviews = gen_reviews(customers, products, orders, 1500)
    write_csv("reviews.csv", reviews,
              ["id", "customer_id", "product_id", "rating", "body", "helpful_votes", "created_at"])

    print("\nDone. Trino table reference (ecommerce.public.<table>):")
    print("  categories   — id, name, parent_id")
    print("  products     — id, name, category_id, price, stock_quantity, is_active, created_at")
    print("  customers    — id, first_name, last_name, email, city, country, registered_at")
    print("  orders       — id, customer_id, status, total_amount, created_at")
    print("  order_items  — id, order_id, product_id, quantity, unit_price")
    print("  reviews      — id, customer_id, product_id, rating, body, helpful_votes, created_at")
    print()
    print("Sample text-to-SQL questions to test:")
    sample_questions = [
        "Show me the top 10 customers by total spending",
        "What are the 5 best-selling products by quantity sold?",
        "How many orders were placed each month in 2024?",
        "Which product categories generate the most revenue?",
        "Find customers who have never placed an order",
        "What is the average order value per country?",
        "List active products with stock below 10",
        "Show the monthly revenue trend for the Electronics category",
        "Which customers placed more than 5 orders?",
        "What percentage of orders were delivered vs cancelled?",
        "What is the average rating per product category?",
        "Find products with more than 50 reviews and an average rating above 4",
        "Which country has the highest average order value?",
        "Show the top 5 products by revenue in the last 3 months",
    ]
    for q in sample_questions:
        print(f"  - {q}")


if __name__ == "__main__":
    main()
