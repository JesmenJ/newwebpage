-- ============================================================
--  SmartQuery DB Schema
--  Two schemas: college + ecommerce
--  PostgreSQL 17 compatible
-- ============================================================

-- ─────────────────────────────────────────
--  COLLEGE SCHEMA
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS departments (
    dept_id     SERIAL PRIMARY KEY,
    dept_name   VARCHAR(100) NOT NULL UNIQUE,
    hod_name    VARCHAR(100),
    building    VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS faculty (
    faculty_id  SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    phone       VARCHAR(15),
    dept_id     INT REFERENCES departments(dept_id),
    designation VARCHAR(50),        -- e.g. 'Professor', 'Asst. Professor'
    joined_date DATE
);

CREATE TABLE IF NOT EXISTS students (
    student_id  SERIAL PRIMARY KEY,
    roll_no     VARCHAR(20) UNIQUE NOT NULL,   -- e.g. 'CSE2021001'
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    phone       VARCHAR(15),
    dept_id     INT REFERENCES departments(dept_id),
    year        INT CHECK (year BETWEEN 1 AND 4),
    section     CHAR(1),            -- 'A', 'B', 'C'
    dob         DATE,
    gender      VARCHAR(10),
    address     VARCHAR(255),
    city        VARCHAR(50),
    admission_year INT
);

CREATE TABLE IF NOT EXISTS courses (
    course_id   SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,   -- e.g. 'CS301'
    course_name VARCHAR(150) NOT NULL,
    credits     INT DEFAULT 3,
    dept_id     INT REFERENCES departments(dept_id),
    semester    INT CHECK (semester BETWEEN 1 AND 8),
    faculty_id  INT REFERENCES faculty(faculty_id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INT REFERENCES students(student_id),
    course_id       INT REFERENCES courses(course_id),
    semester        INT,
    academic_year   VARCHAR(10),        -- e.g. '2023-24'
    grade           VARCHAR(2),         -- 'O', 'A+', 'A', 'B+', 'B', 'C', 'F'
    grade_points    NUMERIC(3,1),       -- 10, 9, 8, 7, 6, 5, 0
    marks           NUMERIC(5,2),
    UNIQUE(student_id, course_id, academic_year)
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id   SERIAL PRIMARY KEY,
    student_id      INT REFERENCES students(student_id),
    course_id       INT REFERENCES courses(course_id),
    date            DATE NOT NULL,
    status          VARCHAR(10) CHECK (status IN ('Present', 'Absent', 'OD', 'Leave'))
);


-- ─────────────────────────────────────────
--  E-COMMERCE SCHEMA
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ec_customers (
    customer_id     SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    phone           VARCHAR(15),
    city            VARCHAR(50),
    state           VARCHAR(50),
    pincode         VARCHAR(10),
    registered_on   DATE,
    is_prime        BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS ec_categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL UNIQUE,
    parent_category VARCHAR(100)    -- e.g. 'Electronics > Mobiles'
);

CREATE TABLE IF NOT EXISTS ec_products (
    product_id      SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    category_id     INT REFERENCES ec_categories(category_id),
    brand           VARCHAR(100),
    price           NUMERIC(10,2),
    discount_pct    NUMERIC(4,1) DEFAULT 0,
    stock           INT DEFAULT 0,
    rating          NUMERIC(2,1),   -- 1.0 to 5.0
    description     TEXT
);

CREATE TABLE IF NOT EXISTS ec_orders (
    order_id        SERIAL PRIMARY KEY,
    customer_id     INT REFERENCES ec_customers(customer_id),
    order_date      DATE NOT NULL,
    total_amount    NUMERIC(10,2),
    status          VARCHAR(20) CHECK (status IN ('Processing','Shipped','Delivered','Cancelled','Returned')),
    payment_method  VARCHAR(20) CHECK (payment_method IN ('UPI','Credit Card','Debit Card','NetBanking','COD')),
    shipping_city   VARCHAR(50),
    delivery_date   DATE
);

CREATE TABLE IF NOT EXISTS ec_order_items (
    item_id         SERIAL PRIMARY KEY,
    order_id        INT REFERENCES ec_orders(order_id),
    product_id      INT REFERENCES ec_products(product_id),
    quantity        INT DEFAULT 1,
    unit_price      NUMERIC(10,2),
    discount_pct    NUMERIC(4,1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ec_reviews (
    review_id       SERIAL PRIMARY KEY,
    customer_id     INT REFERENCES ec_customers(customer_id),
    product_id      INT REFERENCES ec_products(product_id),
    rating          INT CHECK (rating BETWEEN 1 AND 5),
    review_text     TEXT,
    review_date     DATE,
    helpful_votes   INT DEFAULT 0
);
