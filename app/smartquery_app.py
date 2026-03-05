import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
import tempfile
import os
import time

# ─────────────────────────────────────────
#  CONFIG — loaded from .streamlit/secrets.toml
#  locally, or from Streamlit Cloud secrets
# ─────────────────────────────────────────
DB_CONFIG = {
    "host":     st.secrets["DB_HOST"],
    "port":     5432,
    "dbname":   st.secrets["DB_NAME"],
    "user":     st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
}
OPENAI_API_KEY = st.secrets["OPENAI_KEY"]

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="SmartQuery — NL→SQL",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ══ RESET & BASE ══ */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ══ ANIMATED GRADIENT BACKGROUND ══ */
.stApp {
    background: linear-gradient(135deg, #e0e7ff 0%, #f0f4ff 25%, #faf5ff 50%, #e0f2fe 75%, #ede9fe 100%);
    background-size: 400% 400%;
    animation: gradientShift 12s ease infinite;
    color: #1e1b4b;
    min-height: 100vh;
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ══ HIDE STREAMLIT CHROME ══ */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

/* ══ SIDEBAR — GLASSMORPHISM ══ */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.55) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255,255,255,0.7) !important;
    box-shadow: 4px 0 24px rgba(99,102,241,0.08) !important;
}
[data-testid="stSidebar"] * { color: #312e81 !important; }

/* ══ GLASS CARD ══ */
.glass-card {
    background: rgba(255,255,255,0.60);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.80);
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(99,102,241,0.10), 0 1px 0 rgba(255,255,255,0.9) inset;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 40px rgba(99,102,241,0.15), 0 1px 0 rgba(255,255,255,0.9) inset;
}

/* ══ HEADER ══ */
.sq-header {
    background: rgba(255,255,255,0.70);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.90);
    border-radius: 24px;
    padding: 32px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(99,102,241,0.12), 0 1px 0 rgba(255,255,255,1) inset;
}
.sq-header::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 65%);
    pointer-events: none;
}
.sq-header::after {
    content: '';
    position: absolute;
    bottom: -60px; left: -40px;
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(99,102,241,0.10) 0%, transparent 65%);
    pointer-events: none;
}
.sq-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4338ca 0%, #6d28d9 50%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 8px 0;
    letter-spacing: -1px;
    line-height: 1.1;
}
.sq-subtitle {
    color: #6366f1;
    font-size: 1rem;
    font-weight: 400;
    margin: 0;
    opacity: 0.8;
}
.sq-badges {
    display: flex;
    gap: 8px;
    margin-top: 14px;
    flex-wrap: wrap;
}
.sq-badge {
    background: rgba(99,102,241,0.10);
    border: 1px solid rgba(99,102,241,0.20);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #4338ca;
}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 5px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.80);
    box-shadow: 0 4px 16px rgba(99,102,241,0.08);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 12px;
    color: #818cf8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 600;
    font-size: 0.92rem;
    padding: 12px 28px;
    border: none !important;
    transition: all 0.25s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(99,102,241,0.08) !important;
    color: #4338ca !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(79,70,229,0.35) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px !important;
}

/* ══ CARD LABEL ══ */
.card-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #a5b4fc;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ══ LANGUAGE BADGE ══ */
.lang-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.10);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 24px;
    padding: 5px 16px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #4338ca;
    margin-bottom: 14px;
    backdrop-filter: blur(8px);
}

/* ══ ANSWER BUBBLE ══ */
.answer-bubble {
    background: rgba(238,242,255,0.80);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(165,180,252,0.50);
    border-left: 4px solid #6366f1;
    border-radius: 16px;
    padding: 20px 24px;
    margin: 16px 0;
    font-size: 1.05rem;
    line-height: 1.75;
    color: #1e1b4b;
    box-shadow: 0 4px 16px rgba(99,102,241,0.10);
}

/* ══ SQL BLOCK ══ */
.sq-sql {
    background: rgba(15,15,35,0.88);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 14px;
    padding: 18px 22px;
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    color: #93c5fd;
    overflow-x: auto;
    line-height: 1.7;
    box-shadow: 0 4px 20px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.05);
}

/* ══ METRICS ══ */
.metric-row {
    display: flex;
    gap: 14px;
    margin-bottom: 22px;
}
.metric-card {
    flex: 1;
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.85);
    border-radius: 16px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(99,102,241,0.08);
    transition: transform 0.2s ease;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4338ca, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.68rem;
    color: #a5b4fc;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
    margin-top: 4px;
}

/* ══ BUTTONS ══ */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 12px 22px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.30) !important;
    letter-spacing: 0.2px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(79,70,229,0.45) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ══ INPUTS ══ */
.stTextArea textarea, .stTextInput input {
    background: rgba(255,255,255,0.75) !important;
    backdrop-filter: blur(8px) !important;
    border: 1.5px solid rgba(165,180,252,0.50) !important;
    border-radius: 14px !important;
    color: #1e1b4b !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6366f1 !important;
    background: rgba(255,255,255,0.90) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ══ DATAFRAME ══ */
.stDataFrame {
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.08) !important;
    border: 1px solid rgba(165,180,252,0.30) !important;
}
[data-testid="stDataFrame"] > div {
    background: rgba(255,255,255,0.75) !important;
    backdrop-filter: blur(8px) !important;
}

/* ══ EXAMPLE BUTTONS ══ */
.stButton > button[kind="secondary"],
div[data-testid*="ex_"] > div > button {
    background: rgba(255,255,255,0.65) !important;
    color: #4338ca !important;
    border: 1px solid rgba(165,180,252,0.50) !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.08) !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(238,242,255,0.90) !important;
    border-color: #818cf8 !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.18) !important;
    transform: translateX(3px) !important;
}

/* ══ HISTORY ITEMS ══ */
.history-item {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(165,180,252,0.35);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.82rem;
    color: #4338ca;
    transition: all 0.15s ease;
    backdrop-filter: blur(8px);
}
.history-item:hover {
    background: rgba(238,242,255,0.80);
    border-color: #818cf8;
    transform: translateX(2px);
}
.history-tag {
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border-radius: 6px;
    padding: 1px 8px;
    font-size: 0.68rem;
    color: #6366f1;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* ══ RADIO ══ */
.stRadio > div {
    background: rgba(255,255,255,0.55) !important;
    border-radius: 12px !important;
    padding: 8px 12px !important;
    border: 1px solid rgba(165,180,252,0.35) !important;
}

/* ══ ALERTS ══ */
.stSuccess > div {
    background: rgba(236,253,245,0.85) !important;
    border: 1px solid rgba(110,231,183,0.60) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}
.stError > div {
    background: rgba(254,242,242,0.85) !important;
    border: 1px solid rgba(252,165,165,0.60) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}
.stInfo > div {
    background: rgba(239,246,255,0.85) !important;
    border: 1px solid rgba(147,197,253,0.60) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}
.stWarning > div {
    background: rgba(255,251,235,0.85) !important;
    border: 1px solid rgba(253,211,77,0.60) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}

/* ══ SPINNER ══ */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ══ DIVIDER ══ */
hr { border-color: rgba(165,180,252,0.30) !important; }

/* ══ SCROLLBAR ══ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.25); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.50); }


/* ══ STYLE NATIVE STREAMLIT CONTAINERS AS GLASS CARDS ══ */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    background: rgba(255,255,255,0.60);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.80);
    border-radius: 20px;
    padding: 24px !important;
    box-shadow: 0 8px 32px rgba(99,102,241,0.10), 0 1px 0 rgba(255,255,255,0.9) inset;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 4px;
}

/* ══ SELECTBOX ══ */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.75) !important;
    border: 1.5px solid rgba(165,180,252,0.50) !important;
    border-radius: 12px !important;
}

/* ══ PAGE TRANSITION ANIMATION ══ */
.main .block-container {
    animation: fadeUp 0.4s ease forwards;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  DB SCHEMA PROMPTS
# ─────────────────────────────────────────
COLLEGE_SCHEMA = """
You are a PostgreSQL expert. Generate SQL for this college database schema:

Tables:
- departments(dept_id, dept_name, hod_name, building)
- faculty(faculty_id, name, email, phone, dept_id, designation, joined_date)
- students(student_id, roll_no, name, email, phone, dept_id, year, section, dob, gender, address, city, admission_year)
- courses(course_id, course_code, course_name, credits, dept_id, semester, faculty_id)
- enrollments(enrollment_id, student_id, course_id, semester, academic_year, grade, grade_points, marks)
- attendance(attendance_id, student_id, course_id, date, status) -- status: 'Present','Absent','OD','Leave'

Grade system: O=10, A+=9, A=8, B+=7, B=6, C=5, F=0

Complex query examples:
- CGPA = AVG(grade_points) from enrollments
- Attendance % = COUNT(Present)/COUNT(*)*100
- Can JOIN multiple tables for combined queries
"""

ECOMMERCE_SCHEMA = """
You are a PostgreSQL expert. Generate SQL for this e-commerce database schema:

Tables:
- ec_customers(customer_id, name, email, phone, city, state, pincode, registered_on, is_prime)
- ec_categories(category_id, category_name, parent_category)
- ec_products(product_id, name, category_id, brand, price, discount_pct, stock, rating, description)
- ec_orders(order_id, customer_id, order_date, total_amount, status, payment_method, shipping_city, delivery_date)
  -- status: 'Processing','Shipped','Delivered','Cancelled','Returned'
  -- payment_method: 'UPI','Credit Card','Debit Card','NetBanking','COD'
- ec_order_items(item_id, order_id, product_id, quantity, unit_price, discount_pct)
- ec_reviews(review_id, customer_id, product_id, rating, review_text, review_date, helpful_votes)

Can JOIN tables for complex analysis like revenue by category, top customers, etc.
"""

LANGUAGE_NAMES = {
    "en": "English", "ta": "Tamil", "te": "Telugu",
    "kn": "Kannada", "hi": "Hindi"
}
LANGUAGE_FLAGS = {
    "en": "🇬🇧", "ta": "🇮🇳", "te": "🇮🇳", "kn": "🇮🇳", "hi": "🇮🇳"
}
LANGUAGE_DISPLAY = {
    "en": "English", "ta": "தமிழ்", "te": "తెలుగు",
    "kn": "ಕನ್ನಡ", "hi": "हिंदी"
}

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
for key, default in {
    "query_history": [],
    "last_audio":    None,
    "nl_question":   "",
    "detected_lang": "en",
    "total_queries": 0,
    "last_query_time": None,
    "college_auto_run": False,
    "ec_auto_run":      False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def run_sql(sql: str):
    """Run SQL directly on RDS via psycopg2."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)
        rows      = [dict(r) for r in cur.fetchall()]
        row_count = len(rows)
        cur.close()
        conn.close()
        return {"rows": rows, "row_count": row_count}
    except Exception as e:
        return {"error": str(e)}


def is_safe_sql(sql: str) -> bool:
    sql_lower = sql.strip().lower()
    if not sql_lower.startswith("select"):
        return False
    banned = ["insert","update","delete","drop","alter","truncate","create ","grant","revoke"]
    return not any(k in sql_lower for k in banned)


def detect_language(text: str) -> str:
    """Use GPT to detect which language the text is in."""
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Detect the language of this text and respond with ONLY the ISO 639-1 code (en/ta/te/kn/hi). Text: {text}"
            }],
            max_tokens=5,
        )
        code = resp.choices[0].message.content.strip().lower()[:2]
        return code if code in LANGUAGE_NAMES else "en"
    except:
        return "en"


def generate_sql(question: str, schema: str) -> str:
    prompt = f"""
{schema}

User question (may be in any language — translate to understand it):
\"\"\"{question}\"\"\"

Write a single PostgreSQL SQL query that answers the question.
Rules:
- Return ONLY the SQL query, no explanation, no markdown, no backticks.
- Use only the tables and columns defined above.
- No INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
- Use JOINs and aggregations for complex questions.
- Use CURRENT_DATE for today.
- If unanswerable: SELECT 'Question cannot be answered with available data' AS message;
"""
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def translate_answer(data_summary: str, target_lang: str, original_question: str) -> str:
    """Summarize query results in the target language."""
    if target_lang == "en":
        return None
    lang_name = LANGUAGE_NAMES.get(target_lang, "English")
    prompt = f"""
The user asked (in {lang_name}): "{original_question}"

The database returned this data:
{data_summary}

Write a clear, friendly 2-3 sentence answer in {lang_name} that directly answers the user's question based on the data.
Be conversational, not technical. Do not mention SQL or databases.
"""
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def transcribe_audio(audio_bytes: bytes) -> tuple[str, str]:
    """Returns (transcribed_text, detected_language_code)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            tmp_path = f.name
        with open(tmp_path, "rb") as af:
            # No language param = Whisper auto-detects Tamil/Telugu/Kannada/Hindi/English
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=af,
                response_format="verbose_json",   # returns language too
            )
        os.unlink(tmp_path)
        text      = transcript.text
        lang_code = getattr(transcript, "language", "en")
        # Map Whisper full names to codes
        lang_map  = {"tamil":"ta","telugu":"te","kannada":"kn","hindi":"hi","english":"en"}
        lang_code = lang_map.get(lang_code.lower(), lang_code[:2])
        return text, lang_code
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return "", "en"


def process_query(question: str, schema: str, schema_name: str, lang: str):
    """Full pipeline: NL → SQL → RDS → translate → display."""
    if not question.strip():
        st.error("Please enter a question.")
        return

    start_time = time.time()

    # 1. Generate SQL
    with st.spinner("🤖 Generating SQL..."):
        try:
            sql = generate_sql(question, schema)
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return

    # 2. Safety check
    if not is_safe_sql(sql):
        st.error("⚠️ Generated SQL failed safety check. Only SELECT queries allowed.")
        return

    # 3. Show SQL
    st.markdown('<div class="card-label">Generated SQL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sq-sql">{sql}</div>', unsafe_allow_html=True)

    # 4. Run query
    with st.spinner("⚡ Running query on RDS..."):
        body = run_sql(sql)

    elapsed = round(time.time() - start_time, 2)

    if "error" in body:
        st.error(f"Database error: {body['error']}")
        return

    row_count = body["row_count"]

    # 5. Metrics
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">{row_count}</div>
            <div class="metric-label">Rows Returned</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{elapsed}s</div>
            <div class="metric-label">Query Time</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{LANGUAGE_FLAGS.get(lang,'🌐')}</div>
            <div class="metric-label">{LANGUAGE_NAMES.get(lang,'Auto')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if row_count == 0:
        st.warning("Query returned zero rows.")
        return

    df = pd.DataFrame(body["rows"])

    # 6. Translate answer if non-English
    if lang != "en":
        data_preview = df.head(10).to_string(index=False)
        with st.spinner(f"🌐 Translating answer to {LANGUAGE_NAMES.get(lang)}..."):
            translated = translate_answer(data_preview, lang, question)
        if translated:
            st.markdown(f"""
            <div class="answer-bubble">
                <span class="answer-icon">💬</span>{translated}
            </div>
            """, unsafe_allow_html=True)

    # 7. Data table
    st.markdown('<div class="card-label">Query Results</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

    # 8. Update history
    st.session_state["total_queries"] += 1
    st.session_state["last_query_time"] = elapsed
    history_entry = {
        "question": question[:60] + ("..." if len(question) > 60 else ""),
        "schema":   schema_name,
        "rows":     row_count,
        "lang":     lang,
    }
    st.session_state["query_history"].insert(0, history_entry)
    st.session_state["query_history"] = st.session_state["query_history"][:8]


# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.5rem;">🧠</div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.2rem; font-weight:700;
                    background:linear-gradient(135deg,#4f46e5,#6366f1);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;">SmartQuery</div>
        <div style="font-size:0.72rem; color:#9ca3af; letter-spacing:2px; margin-top:2px;">
            NL → SQL ENGINE
        </div>
    </div>
    <hr style="border-color:#e8eaf6; margin: 10px 0 20px 0;">
    """, unsafe_allow_html=True)

    # Stats
    total_q  = st.session_state["total_queries"]
    last_t   = st.session_state["last_query_time"] or "—"
    st.markdown(f"""
    <div style="display:flex; gap:8px; margin-bottom:20px;">
        <div style="flex:1; background:rgba(255,255,255,0.65); border:1px solid rgba(165,180,252,0.45); border-radius:12px; backdrop-filter:blur(8px);
                    padding:10px; text-align:center;">
            <div style="font-size:1.3rem; font-weight:700; color:#4f46e5;">{total_q}</div>
            <div style="font-size:0.68rem; color:#9ca3af; text-transform:uppercase;
                        letter-spacing:1px;">Queries</div>
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.65); border:1px solid rgba(165,180,252,0.45); border-radius:12px; backdrop-filter:blur(8px);
                    padding:10px; text-align:center;">
            <div style="font-size:1.3rem; font-weight:700; color:#6366f1;">{last_t}{"s" if last_t != "—" else ""}</div>
            <div style="font-size:0.68rem; color:#9ca3af; text-transform:uppercase;
                        letter-spacing:1px;">Last Time</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Language support info
    st.markdown("""
    <div style="background:rgba(255,255,255,0.55); border:1px solid rgba(165,180,252,0.40); border-radius:14px; backdrop-filter:blur(8px);
                padding:14px 16px; margin-bottom:20px;">
        <div style="font-size:0.7rem; font-weight:700; letter-spacing:2px;
                    text-transform:uppercase; color:#a5b4fc; margin-bottom:10px;">
            🌐 Voice Languages
        </div>
    """, unsafe_allow_html=True)
    for code, display in LANGUAGE_DISPLAY.items():
        flag = LANGUAGE_FLAGS[code]
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; padding:4px 0;
                    font-size:0.85rem; color:#6b7280;">
            <span>{flag}</span><span>{display}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Query history
    if st.session_state["query_history"]:
        st.markdown("""
        <div style="font-size:0.7rem; font-weight:700; letter-spacing:2px;
                    text-transform:uppercase; color:#a5b4fc; margin-bottom:10px;">
            📜 Recent Queries
        </div>
        """, unsafe_allow_html=True)
        for item in st.session_state["query_history"]:
            lang_flag = LANGUAGE_FLAGS.get(item["lang"], "🌐")
            st.markdown(f"""
            <div class="history-item">
                <div class="history-tag">{item['schema']} · {item['rows']} rows · {lang_flag}</div>
                <div>{item['question']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="position:absolute; bottom:20px; left:0; right:0; text-align:center;
                font-size:0.68rem; color:#d1d5db;">
        Powered by GPT-4o-mini + Whisper<br>AWS RDS PostgreSQL
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  MAIN HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="sq-header">
    <div class="sq-title">🧠 SmartQuery</div>
    <p class="sq-subtitle">
        Ask in <strong>English, Tamil, Telugu, Kannada or Hindi</strong> — voice or text — get instant answers.
    </p>
    <div class="sq-badges">
        <span class="sq-badge">🎤 Voice Input</span>
        <span class="sq-badge">🌐 5 Languages</span>
        <span class="sq-badge">🎓 College DB</span>
        <span class="sq-badge">🛍️ E-Commerce DB</span>
        <span class="sq-badge">⚡ Live SQL</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🎓  College Database",
    "🛍️  E-Commerce Database",
    "⚙️  Raw SQL"
])

# ══════════════════════════════════════════
#  TAB 1 — COLLEGE
# ══════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown('<div class="card-label">🎤 Ask a Question</div>', unsafe_allow_html=True)

        lang = st.session_state.get("detected_lang_college", "en")
        st.markdown(f'''
        <div class="lang-badge">
            {LANGUAGE_FLAGS.get(lang,"🌐")} Detected: {LANGUAGE_DISPLAY.get(lang,"Auto")}
        </div>
        ''', unsafe_allow_html=True)

        vcol, tcol = st.columns([1, 8])
        with vcol:
            st.write("")
            st.write("")
            audio_bytes = audio_recorder(
                text="", recording_color="#7c3aed",
                neutral_color="#4f46e5",
                icon_name="microphone", icon_size="lg",
                key="audio_college"
            )
        with tcol:
            college_question = st.text_area(
                "Question",
                value=st.session_state.get("college_question", ""),
                height=110,
                key="college_input",
                placeholder="e.g. Show me all CSE students with CGPA above 8.5",
                label_visibility="collapsed"
            )

        if audio_bytes and audio_bytes != st.session_state.get("last_audio_college"):
            st.session_state["last_audio_college"] = audio_bytes
            with st.spinner("🎧 Transcribing your voice..."):
                text, detected_lang = transcribe_audio(audio_bytes)
            if text:
                st.session_state["college_question"] = text
                st.session_state["detected_lang_college"] = detected_lang
                st.session_state["college_auto_run"] = True

        b1, b2 = st.columns(2)
        with b1:
            search = st.button("🔍 Search", use_container_width=True, key="college_search")
        with b2:
            clear = st.button("🗑️ Clear", use_container_width=True, key="college_clear")

        if clear:
            st.session_state["college_question"] = ""
            st.session_state["college_auto_run"] = False
            st.rerun()

        should_run = search or st.session_state.get("college_auto_run", False)
        if should_run:
            st.session_state["college_auto_run"] = False
            q    = st.session_state.get("college_question", college_question).strip()
            lang = st.session_state.get("detected_lang_college", "en")
            if q:
                if not search:
                    st.info(f"🎤 Voice: *\"{q}\"* ({LANGUAGE_DISPLAY.get(lang, lang)})")
                process_query(q, COLLEGE_SCHEMA, "College", lang)

    with col_right:
        st.markdown('<div class="card-label">💡 Example Questions</div>', unsafe_allow_html=True)
        examples = [
            ("🎓", "Show all CSE students in year 3"),
            ("📊", "Which student has the highest CGPA?"),
            ("📅", "Students with attendance below 75% this semester"),
            ("🏆", "Top 5 students by marks in Database Management"),
            ("👥", "How many students are in each department?"),
            ("📋", "List all students who failed any course"),
            ("🗓️", "என் roll number CS2021001 இன் marks காட்டு"),
            ("🔍", "CSE విభాగంలో అన్ని faculty చూపించు"),
        ]
        for icon, ex in examples:
            if st.button(f"{icon}  {ex}", key=f"ex_col_{ex[:20]}", use_container_width=True):
                st.session_state["college_question"] = ex
                st.session_state["detected_lang_college"] = detect_language(ex)
                st.rerun()

# ══════════════════════════════════════════
#  TAB 2 — E-COMMERCE
# ══════════════════════════════════════════
with tab2:
    col_left2, col_right2 = st.columns([3, 2], gap="large")

    with col_left2:
        st.markdown('<div class="card-label">🎤 Ask a Question</div>', unsafe_allow_html=True)

        lang2 = st.session_state.get("detected_lang_ec", "en")
        st.markdown(f'''
        <div class="lang-badge">
            {LANGUAGE_FLAGS.get(lang2,"🌐")} Detected: {LANGUAGE_DISPLAY.get(lang2,"Auto")}
        </div>
        ''', unsafe_allow_html=True)

        vcol2, tcol2 = st.columns([1, 8])
        with vcol2:
            st.write("")
            st.write("")
            audio_bytes2 = audio_recorder(
                text="", recording_color="#7c3aed",
                neutral_color="#4f46e5",
                icon_name="microphone", icon_size="lg",
                key="audio_ec"
            )
        with tcol2:
            ec_question = st.text_area(
                "Question",
                value=st.session_state.get("ec_question", ""),
                height=110,
                key="ec_input",
                placeholder="e.g. What are the top 5 selling products this month?",
                label_visibility="collapsed"
            )

        if audio_bytes2 and audio_bytes2 != st.session_state.get("last_audio_ec"):
            st.session_state["last_audio_ec"] = audio_bytes2
            with st.spinner("🎧 Transcribing your voice..."):
                text2, detected_lang2 = transcribe_audio(audio_bytes2)
            if text2:
                st.session_state["ec_question"] = text2
                st.session_state["detected_lang_ec"] = detected_lang2
                st.session_state["ec_auto_run"] = True

        b3, b4 = st.columns(2)
        with b3:
            search2 = st.button("🔍 Search", use_container_width=True, key="ec_search")
        with b4:
            clear2  = st.button("🗑️ Clear", use_container_width=True, key="ec_clear")

        if clear2:
            st.session_state["ec_question"] = ""
            st.session_state["ec_auto_run"] = False
            st.rerun()

        should_run2 = search2 or st.session_state.get("ec_auto_run", False)
        if should_run2:
            st.session_state["ec_auto_run"] = False
            q2    = st.session_state.get("ec_question", ec_question).strip()
            lang2 = st.session_state.get("detected_lang_ec", "en")
            if q2:
                if not search2:
                    st.info(f"🎤 Voice: *\"{q2}\"* ({LANGUAGE_DISPLAY.get(lang2, lang2)})")
                process_query(q2, ECOMMERCE_SCHEMA, "E-Commerce", lang2)

    with col_right2:
        st.markdown('<div class="card-label">💡 Example Questions</div>', unsafe_allow_html=True)
        examples2 = [
            ("💰", "Top 10 customers by total spending"),
            ("📦", "How many orders were delivered this month?"),
            ("⭐", "Products with rating above 4.5"),
            ("🏙️", "Which city has the most orders?"),
            ("💳", "Most popular payment method"),
            ("📉", "Products with stock below 10"),
            ("🛒", "இந்த மாதம் எத்தனை orders cancel ஆனது?"),
            ("📊", "ఈ నెలలో అత్యధిక అమ్మకాలు చేసిన products"),
        ]
        for icon, ex in examples2:
            if st.button(f"{icon}  {ex}", key=f"ex_ec_{ex[:20]}", use_container_width=True):
                st.session_state["ec_question"] = ex
                st.session_state["detected_lang_ec"] = detect_language(ex)
                st.rerun()

# ══════════════════════════════════════════
#  TAB 3 — RAW SQL
# ══════════════════════════════════════════
with tab3:
    st.markdown('<div class="card-label">⚙️ Raw SQL Query</div>', unsafe_allow_html=True)

    db_choice = st.radio(
        "Target database:",
        ["College", "E-Commerce"],
        horizontal=True,
        key="raw_db_choice"
    )

    default_sql = {
        "College":    "SELECT s.name, s.roll_no, d.dept_name, ROUND(AVG(e.grade_points)::numeric,2) as cgpa\nFROM students s\nJOIN departments d ON s.dept_id = d.dept_id\nJOIN enrollments e ON s.student_id = e.student_id\nGROUP BY s.name, s.roll_no, d.dept_name\nORDER BY cgpa DESC\nLIMIT 10;",
        "E-Commerce": "SELECT c.name, COUNT(o.order_id) as total_orders, ROUND(SUM(o.total_amount)::numeric,2) as total_spent\nFROM ec_customers c\nJOIN ec_orders o ON c.customer_id = o.customer_id\nGROUP BY c.name\nORDER BY total_spent DESC\nLIMIT 10;",
    }

    raw_sql = st.text_area(
        "Enter your SQL query (SELECT only):",
        value=default_sql[db_choice],
        height=180,
        key="raw_sql_input"
    )

    if st.button("▶  Run Query", key="run_raw"):
        if not raw_sql.strip():
            st.error("SQL cannot be empty.")
        elif not is_safe_sql(raw_sql):
            st.error("⚠️ Only SELECT queries are allowed.")
        else:
            start = time.time()
            with st.spinner("⚡ Running query..."):
                body = run_sql(raw_sql)
            elapsed = round(time.time() - start, 2)
            if "error" in body:
                st.error(f"Error: {body['error']}")
            else:
                rc = body["row_count"]
                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-card">
                        <div class="metric-value">{rc}</div>
                        <div class="metric-label">Rows</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{elapsed}s</div>
                        <div class="metric-label">Time</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if rc > 0:
                    df = pd.DataFrame(body["rows"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No rows returned.")
