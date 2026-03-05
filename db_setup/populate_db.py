"""
populate_db.py
──────────────────────────────────────────────────────────────────
Generates realistic Indian sample data for BOTH schemas and
inserts it into your AWS RDS PostgreSQL database.

Install dependencies first:
    pip install psycopg2-binary faker

Usage:
    python populate_db.py
"""

import random
import psycopg2
from faker import Faker
from datetime import date, timedelta

fake = Faker("en_IN")   # Indian locale for names, addresses, phone numbers
random.seed(42)

# ──────────────────────────────────────────────
#  🔧 EDIT THESE with your RDS credentials
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     "smartquery-db.cwzwiq2awtps.us-east-1.rds.amazonaws.com",    # e.g. mydb.xxxxxx.us-east-1.rds.amazonaws.com
    "port":     5432,
    "dbname":   "smartquery",
    "user":     "postgres",
    "password": "jesmen2211",
}
# ──────────────────────────────────────────────

conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

print("✅ Connected to RDS")


# ════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

GRADE_MAP = {
    "O":  10.0, "A+": 9.0, "A": 8.0,
    "B+": 7.0,  "B":  6.0, "C": 5.0, "F": 0.0
}

def rand_grade():
    weights = [5, 15, 25, 25, 15, 10, 5]   # O … F
    return random.choices(list(GRADE_MAP.keys()), weights=weights, k=1)[0]

def marks_from_grade(grade: str) -> float:
    base = {"O": 90, "A+": 80, "A": 70, "B+": 60, "B": 55, "C": 50, "F": 30}
    return round(base[grade] + random.uniform(0, 9.9), 2)


# ════════════════════════════════════════════════════════
#  COLLEGE DATA
# ════════════════════════════════════════════════════════
print("\n📚 Inserting College data...")

# ── Departments ──
departments = [
    ("Computer Science & Engineering", "Dr. Ramesh Kumar",    "Block A"),
    ("Electronics & Communication",    "Dr. Priya Nair",      "Block B"),
    ("Mechanical Engineering",         "Dr. Suresh Reddy",    "Block C"),
    ("Civil Engineering",              "Dr. Anitha Sharma",   "Block D"),
    ("Information Technology",         "Dr. Vikram Menon",    "Block A"),
    ("Artificial Intelligence & ML",   "Dr. Kavitha Pillai",  "Block E"),
]

dept_ids = []
for dept_name, hod, building in departments:
    cur.execute(
        "INSERT INTO departments (dept_name, hod_name, building) VALUES (%s,%s,%s) RETURNING dept_id",
        (dept_name, hod, building)
    )
    dept_ids.append(cur.fetchone()[0])
print(f"  → {len(dept_ids)} departments")

# ── Faculty ──
designations = ["Professor", "Asst. Professor", "Assoc. Professor", "Lecturer"]
faculty_ids  = []
for _ in range(40):
    dept_id = random.choice(dept_ids)
    cur.execute("""
        INSERT INTO faculty (name, email, phone, dept_id, designation, joined_date)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING faculty_id
    """, (
        fake.name(),
        fake.unique.email(),
        fake.phone_number()[:15],
        dept_id,
        random.choice(designations),
        rand_date(date(2005, 1, 1), date(2022, 12, 31))
    ))
    faculty_ids.append(cur.fetchone()[0])
print(f"  → {len(faculty_ids)} faculty members")

# ── Students ──
student_ids = []
roll_counter = {d: 1 for d in dept_ids}
dept_code    = {dept_ids[i]: ["CSE","ECE","MECH","CIVIL","IT","AIML"][i] for i in range(len(dept_ids))}

for _ in range(500):
    dept_id = random.choice(dept_ids)
    year    = random.randint(1, 4)
    adm_yr  = 2024 - year + 1
    roll_no = f"{dept_code[dept_id]}{adm_yr}{roll_counter[dept_id]:03d}"
    roll_counter[dept_id] += 1

    cur.execute("""
        INSERT INTO students
        (roll_no, name, email, phone, dept_id, year, section, dob, gender, address, city, admission_year)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING student_id
    """, (
        roll_no,
        fake.name(),
        fake.unique.email(),
        fake.phone_number()[:15],
        dept_id,
        year,
        random.choice(["A", "B", "C"]),
        rand_date(date(2000, 1, 1), date(2006, 12, 31)),
        random.choice(["Male", "Female", "Other"]),
        fake.address().replace("\n", ", ")[:255],
        random.choice(["Chennai", "Bangalore", "Hyderabad", "Coimbatore", "Madurai", "Kochi", "Mysore"]),
        adm_yr
    ))
    student_ids.append(cur.fetchone()[0])
print(f"  → {len(student_ids)} students")

# ── Courses ──
course_templates = [
    ("Data Structures",         "CS301", 4, 3),
    ("Database Management",     "CS302", 4, 3),
    ("Operating Systems",       "CS401", 4, 4),
    ("Machine Learning",        "CS501", 4, 5),
    ("Computer Networks",       "CS402", 3, 4),
    ("Python Programming",      "CS201", 3, 2),
    ("Discrete Mathematics",    "MA301", 3, 3),
    ("Digital Circuits",        "EC301", 4, 3),
    ("Signals & Systems",       "EC401", 4, 4),
    ("Thermodynamics",          "ME301", 4, 3),
    ("Fluid Mechanics",         "ME401", 4, 4),
    ("Structural Analysis",     "CE301", 4, 3),
    ("Web Technologies",        "IT301", 3, 3),
    ("Deep Learning",           "AI401", 4, 4),
    ("NLP",                     "AI501", 4, 5),
    ("Software Engineering",    "CS601", 3, 6),
    ("Cloud Computing",         "IT401", 3, 4),
    ("Embedded Systems",        "EC501", 4, 5),
]

course_ids = []
for cname, ccode, credits, sem in course_templates:
    dept_id    = random.choice(dept_ids)
    faculty_id = random.choice(faculty_ids)
    cur.execute("""
        INSERT INTO courses (course_code, course_name, credits, dept_id, semester, faculty_id)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING course_id
    """, (ccode, cname, credits, dept_id, sem, faculty_id))
    course_ids.append(cur.fetchone()[0])
print(f"  → {len(course_ids)} courses")

# ── Enrollments ──
enrollment_count = 0
for student_id in student_ids:
    for course_id in random.sample(course_ids, k=random.randint(4, 7)):
        grade = rand_grade()
        try:
            cur.execute("""
                INSERT INTO enrollments
                (student_id, course_id, semester, academic_year, grade, grade_points, marks)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                student_id, course_id,
                random.randint(1, 8), "2023-24",
                grade, GRADE_MAP[grade], marks_from_grade(grade)
            ))
            enrollment_count += 1
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
print(f"  → {enrollment_count} enrollments")

# ── Attendance (last 90 days) ──
today = date.today()
attendance_count = 0
sample_students = random.sample(student_ids, min(100, len(student_ids)))
for student_id in sample_students:
    for course_id in random.sample(course_ids, k=3):
        for day_offset in range(90):
            d = today - timedelta(days=day_offset)
            if d.weekday() < 5:   # Mon–Fri only
                status = random.choices(
                    ["Present", "Absent", "OD", "Leave"],
                    weights=[75, 15, 5, 5], k=1
                )[0]
                cur.execute("""
                    INSERT INTO attendance (student_id, course_id, date, status)
                    VALUES (%s,%s,%s,%s)
                """, (student_id, course_id, d, status))
                attendance_count += 1
print(f"  → {attendance_count} attendance records")


# ════════════════════════════════════════════════════════
#  E-COMMERCE DATA
# ════════════════════════════════════════════════════════
print("\n🛍️  Inserting E-Commerce data...")

# ── Categories ──
categories = [
    ("Mobiles",        "Electronics"),
    ("Laptops",        "Electronics"),
    ("Headphones",     "Electronics"),
    ("Televisions",    "Electronics"),
    ("Refrigerators",  "Appliances"),
    ("Washing Machines","Appliances"),
    ("Men's Clothing", "Fashion"),
    ("Women's Clothing","Fashion"),
    ("Footwear",       "Fashion"),
    ("Books",          "Education"),
    ("Toys",           "Kids"),
    ("Kitchen",        "Home & Kitchen"),
    ("Furniture",      "Home"),
    ("Sports",         "Sports & Fitness"),
    ("Beauty",         "Health & Beauty"),
]

cat_ids = []
for cname, parent in categories:
    cur.execute(
        "INSERT INTO ec_categories (category_name, parent_category) VALUES (%s,%s) RETURNING category_id",
        (cname, parent)
    )
    cat_ids.append(cur.fetchone()[0])
print(f"  → {len(cat_ids)} categories")

# ── Customers ──
indian_cities = [
    "Mumbai","Delhi","Bangalore","Chennai","Hyderabad",
    "Pune","Kolkata","Ahmedabad","Jaipur","Kochi",
    "Coimbatore","Lucknow","Surat","Nagpur","Indore"
]
indian_states = {
    "Mumbai": "Maharashtra", "Delhi": "Delhi", "Bangalore": "Karnataka",
    "Chennai": "Tamil Nadu", "Hyderabad": "Telangana", "Pune": "Maharashtra",
    "Kolkata": "West Bengal", "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan",
    "Kochi": "Kerala", "Coimbatore": "Tamil Nadu", "Lucknow": "Uttar Pradesh",
    "Surat": "Gujarat", "Nagpur": "Maharashtra", "Indore": "Madhya Pradesh"
}

customer_ids = []
for _ in range(300):
    city = random.choice(indian_cities)
    cur.execute("""
        INSERT INTO ec_customers
        (name, email, phone, city, state, pincode, registered_on, is_prime)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING customer_id
    """, (
        fake.name(),
        fake.unique.email(),
        fake.phone_number()[:15],
        city,
        indian_states[city],
        str(fake.postcode())[:10],
        rand_date(date(2019, 1, 1), date(2024, 12, 31)),
        random.random() < 0.3    # 30% prime members
    ))
    customer_ids.append(cur.fetchone()[0])
print(f"  → {len(customer_ids)} customers")

# ── Products ──
product_templates = [
    ("Samsung Galaxy S24",         0, "Samsung",  79999, 10),
    ("iPhone 15 Pro",              0, "Apple",    134900, 5),
    ("OnePlus 12",                 0, "OnePlus",  64999, 15),
    ("Redmi Note 13",              0, "Xiaomi",   17999, 30),
    ("Dell Inspiron 15",           1, "Dell",     55990, 20),
    ("HP Pavilion 14",             1, "HP",       62990, 18),
    ("MacBook Air M2",             1, "Apple",    114900, 8),
    ("Sony WH-1000XM5",            2, "Sony",     29990, 25),
    ("boAt Airdopes 141",          2, "boAt",      1299, 100),
    ("LG 55\" OLED TV",            3, "LG",       129990, 7),
    ("Samsung 43\" Smart TV",      3, "Samsung",   34990, 15),
    ("LG 260L Refrigerator",       4, "LG",       28990, 10),
    ("Whirlpool Washing Machine",  5, "Whirlpool", 25990, 12),
    ("Levi's Men's Jeans",         6, "Levi's",    2499, 50),
    ("Nike Air Max",               8, "Nike",      8999, 40),
    ("Atomic Habits (Book)",       9, "Penguin",    350, 200),
    ("LEGO Technic Set",          10, "LEGO",      5999, 30),
    ("Prestige Cooker 5L",        11, "Prestige",  2199, 60),
    ("Yoga Mat",                  13, "Decathlon", 1299, 80),
    ("Himalaya Face Wash",        14, "Himalaya",   149, 150),
]

product_ids = []
for pname, cat_idx, brand, price, stock in product_templates:
    rating = round(random.uniform(3.5, 5.0), 1)
    cur.execute("""
        INSERT INTO ec_products
        (name, category_id, brand, price, discount_pct, stock, rating)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING product_id
    """, (
        pname, cat_ids[cat_idx], brand, price,
        round(random.uniform(0, 30), 1), stock, rating
    ))
    product_ids.append(cur.fetchone()[0])
print(f"  → {len(product_ids)} products")

# ── Orders + Order Items ──
order_ids     = []
order_count   = 0
item_count    = 0
statuses      = ["Processing","Shipped","Delivered","Cancelled","Returned"]
status_weights= [5, 15, 65, 10, 5]
payments      = ["UPI","Credit Card","Debit Card","NetBanking","COD"]

for customer_id in customer_ids:
    for _ in range(random.randint(1, 8)):
        order_date = rand_date(date(2023, 1, 1), date.today())
        status     = random.choices(statuses, weights=status_weights, k=1)[0]
        delivery   = (order_date + timedelta(days=random.randint(2, 10))
                      if status == "Delivered" else None)
        city = random.choice(indian_cities)

        cur.execute("""
            INSERT INTO ec_orders
            (customer_id, order_date, total_amount, status, payment_method, shipping_city, delivery_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING order_id
        """, (
            customer_id, order_date, 0,
            status, random.choice(payments), city, delivery
        ))
        order_id = cur.fetchone()[0]
        order_ids.append(order_id)
        order_count += 1

        # Order items
        total = 0
        for product_id in random.sample(product_ids, k=random.randint(1, 4)):
            qty      = random.randint(1, 3)
            cur.execute("SELECT price FROM ec_products WHERE product_id=%s", (product_id,))
            price    = float(cur.fetchone()[0])
            disc     = round(random.uniform(0, 25), 1)
            total   += qty * price * (1 - disc/100)
            cur.execute("""
                INSERT INTO ec_order_items (order_id, product_id, quantity, unit_price, discount_pct)
                VALUES (%s,%s,%s,%s,%s)
            """, (order_id, product_id, qty, price, disc))
            item_count += 1

        # Update total_amount
        cur.execute("UPDATE ec_orders SET total_amount=%s WHERE order_id=%s",
                    (round(total, 2), order_id))

print(f"  → {order_count} orders, {item_count} order items")

# ── Reviews ──
review_count = 0
for _ in range(600):
    try:
        cur.execute("""
            INSERT INTO ec_reviews
            (customer_id, product_id, rating, review_text, review_date, helpful_votes)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            random.choice(customer_ids),
            random.choice(product_ids),
            random.randint(1, 5),
            fake.sentence(nb_words=20),
            rand_date(date(2023, 1, 1), date.today()),
            random.randint(0, 50)
        ))
        review_count += 1
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
print(f"  → {review_count} reviews")


# ════════════════════════════════════════════════════════
#  COMMIT & CLOSE
# ════════════════════════════════════════════════════════
conn.commit()
cur.close()
conn.close()

print("\n🎉 All done! Database populated successfully.")
print("Summary:")
print(f"  College  : 6 depts | 40 faculty | 500 students | {len(course_ids)} courses")
print(f"  Ecommerce: 300 customers | {len(product_ids)} products | {order_count} orders")
