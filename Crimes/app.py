# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# Page Config
# ==============================
st.set_page_config(page_title="Chicago Crime Dashboard", layout="wide")

# ==============================
# Theme: Light Blue + White (High Contrast)
# ==============================
st.markdown(
    """
<style>
.stApp { background: #f4f9ff; color: #0f172a; }
html, body, [class*="css"] { color: #0f172a !important; }
h1, h2, h3, h4 { color: #0b3d91 !important; }
p, span, label, small, div { color: #0f172a !important; }

section[data-testid="stSidebar"] { background: #e6f2ff !important; }
section[data-testid="stSidebar"] * { color: #0f172a !important; }

div[data-testid="stMetric"]{
  background: #ffffff !important;
  border: 1px solid rgba(15, 23, 42, 0.12) !important;
  padding: 14px 16px !important;
  border-radius: 14px !important;
  box-shadow: 0 2px 8px rgba(2, 6, 23, 0.08) !important;
}
div[data-testid="stMetric"] * { color: #0f172a !important; }
div[data-testid="stMetricLabel"] { color: #0b3d91 !important; font-weight: 700 !important; }

div[data-testid="stDataFrame"] * { color: #0f172a !important; }
div[data-baseweb="select"] * , div[data-baseweb="input"] * { color: #0f172a !important; }

a, a * { color: #0b3d91 !important; font-weight: 600 !important; }
hr { border-color: rgba(15, 23, 42, 0.18) !important; }

/* Insight Card */
.insight-card{
  background:#ffffff;
  border:1px solid rgba(15, 23, 42, 0.12);
  border-left:6px solid #0b3d91;
  padding:14px 16px;
  border-radius:14px;
  box-shadow:0 2px 8px rgba(2, 6, 23, 0.06);
  margin-top:10px;
  margin-bottom:4px;
}
.insight-title{
  font-weight:800;
  color:#0b3d91;
  margin-bottom:6px;
}
.insight-b{
  font-weight:700;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================
# UI Helper: Insight Card
# ==============================
def insight_card(title_th_en: str, what: str, so_what: str, now_what: str):
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">🔍 {title_th_en}</div>
          <div><span class="insight-b">What (พบอะไร):</span> {what}</div>
          <div><span class="insight-b">So What (สำคัญอย่างไร):</span> {so_what}</div>
          <div><span class="insight-b">Now What (ทำอะไรต่อ):</span> {now_what}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================
# Load Data
# ==============================
@st.cache_data(show_spinner=False)
def load_data():
    before_url = "https://drive.google.com/uc?id=1zl7Cg2oQi8q61gyX42IjLKXmK7rmzp9v"
    after_url = "https://drive.google.com/uc?id=1Mu5kXGBcC8KEINNfZPiumBPxNGQ-nN5G"
    df_before = pd.read_csv(before_url, low_memory=False)
    df_after = pd.read_csv(after_url, low_memory=False)
    return df_before, df_after

@st.cache_data(show_spinner=False)
def prep_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df

with st.spinner("กำลังโหลดข้อมูล..."):
    df_before, df_after = load_data()
    df_before = prep_dates(df_before)
    df_after = prep_dates(df_after)

# ==============================
# Title
# ==============================
st.title("Chicago Crimes Dashboard")
st.caption("เปรียบเทียบข้อมูลก่อนทำความสะอาด (Before) และหลังทำความสะอาด (After)")

# ==============================
# Sidebar Filters (Competition-ready)
# ==============================
st.sidebar.header("ตัวกรอง (Filters)")

# --- Reset filters button (helps usability / scoring)
if "reset_filters" not in st.session_state:
    st.session_state.reset_filters = False

if st.sidebar.button("รีเซ็ตตัวกรอง (Reset Filters)"):
    st.session_state.reset_filters = True

# --- Year range (robust)
if (
    "Year" in df_after.columns
    and df_after["Year"].notna().any()
    and "Year" in df_before.columns
    and df_before["Year"].notna().any()
):
    year_min = int(min(df_after["Year"].dropna().min(), df_before["Year"].dropna().min()))
    year_max = int(max(df_after["Year"].dropna().max(), df_before["Year"].dropna().max()))
else:
    year_min, year_max = 2001, 2025

default_year = (year_min, year_max)

year_range = st.sidebar.slider(
    "ช่วงปี (Year Range)",
    year_min,
    year_max,
    default_year if not st.session_state.reset_filters else (year_min, year_max),
)

# --- Helper to build options safely (works even if some columns are missing after cleaning)
def safe_unique_values(df: pd.DataFrame, col: str, max_items: int = 200):
    if col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).unique().tolist()
    vals = sorted(vals)
    return vals[:max_items]

# --- Build filter options from AFTER first (because it is the analysis dataset)
crime_types = safe_unique_values(df_after, "Primary Type")
districts = safe_unique_values(df_after, "District")
loc_desc = safe_unique_values(df_after, "Location Description")

# --- Multi-filters
sel_crime = st.sidebar.multiselect(
    "ประเภทคดี (Primary Type)",
    options=crime_types,
    default=[] if not st.session_state.reset_filters else [],
)

sel_district = st.sidebar.multiselect(
    "เขตตำรวจ (District)",
    options=districts,
    default=[] if not st.session_state.reset_filters else [],
)

sel_loc = st.sidebar.multiselect(
    "สถานที่เกิดเหตุ (Location Description)",
    options=loc_desc,
    default=[] if not st.session_state.reset_filters else [],
)

sel_arrest = st.sidebar.multiselect(
    "การจับกุม (Arrest)",
    options=["True", "False"],
    default=[] if not st.session_state.reset_filters else [],
)

sel_domestic = st.sidebar.multiselect(
    "คดีในครอบครัว (Domestic)",
    options=["True", "False"],
    default=[] if not st.session_state.reset_filters else [],
)

st.sidebar.divider()
metric_mode = st.sidebar.radio(
    "รูปแบบแสดงผล (Metric Mode)",
    options=["Count (จำนวน)", "Share % (สัดส่วน %)"],
    index=0,
)

top_k = st.sidebar.slider("Top K ที่แสดง (Top K)", 5, 20, 10)

# --- Apply same filters to both datasets (Before/After)
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    dff = df.copy()

    if "Year" in dff.columns:
        dff = dff[(dff["Year"] >= year_range[0]) & (dff["Year"] <= year_range[1])]

    if sel_crime and "Primary Type" in dff.columns:
        dff = dff[dff["Primary Type"].astype(str).isin(sel_crime)]

    if sel_district and "District" in dff.columns:
        dff = dff[dff["District"].astype(str).isin(sel_district)]

    if sel_loc and "Location Description" in dff.columns:
        dff = dff[dff["Location Description"].astype(str).isin(sel_loc)]

    if sel_arrest and "Arrest" in dff.columns:
        dff = dff[dff["Arrest"].astype(str).isin(sel_arrest)]

    if sel_domestic and "Domestic" in dff.columns:
        dff = dff[dff["Domestic"].astype(str).isin(sel_domestic)]

    return dff

b = apply_filters(df_before)
a = apply_filters(df_after)

# --- Clear reset flag after applying
if st.session_state.reset_filters:
    st.session_state.reset_filters = False

# --- Empty state (important for scoring)
if a.empty or b.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก กรุณาปรับตัวกรอง (Filter) ใหม่ หรือกด Reset Filters")
    st.stop()

# ==============================
# Tabs
# ==============================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "ภาพรวม (Overview)",
        "คุณภาพข้อมูล (Data Quality)",
        "สำรวจข้อมูล (Exploration)",
        "ขั้นตอนการจัดการข้อมูล (Cleaning Process)",
        "พจนานุกรมข้อมูล (Data Dictionary)",
        "Missing ก่อน–หลัง (Missing Compare)",
    ]
)

# ==============================
# Data Dictionary + Missing Handling
# ==============================
FEATURE_INFO = [
    ("Case Number", "รหัสคดีเฉพาะ (Case identifier)", "หมวดหมู่ (Categorical/String)", "Event"),
    ("ID", "หมายเลขประจำเหตุการณ์ (Record ID)", "ตัวเลข (Numeric/Integer)", "Event"),
    ("Date", "วันเวลาเกิดเหตุ (Incident datetime)", "วันเวลา (Datetime)", "Event"),
    ("Updated On", "วันเวลาอัปเดตข้อมูล (Updated datetime)", "วันเวลา (Datetime)", "Event"),
    ("Year", "ปีที่เกิดเหตุ (Year)", "ตัวเลข (Numeric/Integer)", "Event"),
    ("IUCR", "รหัสประเภทคดีมาตรฐาน (IUCR code)", "หมวดหมู่ (Categorical)", "Crime"),
    ("Primary Type", "ประเภทคดีหลัก (Primary type)", "หมวดหมู่ (Categorical)", "Crime"),
    ("Description", "รายละเอียดคดี (Description)", "หมวดหมู่ (Categorical)", "Crime"),
    ("FBI Code", "รหัสจัดกลุ่มตาม FBI (FBI code)", "หมวดหมู่ (Categorical)", "Crime"),
    ("Arrest", "มีการจับกุมหรือไม่ (Arrested)", "ตรรกะ (Boolean)", "Status"),
    ("Domestic", "คดีในครอบครัวหรือไม่ (Domestic)", "ตรรกะ (Boolean)", "Status"),
    ("Block", "บล็อกที่เกิดเหตุ (Block)", "หมวดหมู่ (Categorical)", "Location"),
    ("Beat", "รหัสเขตย่อยตำรวจ (Beat)", "ตัวเลข (Numeric/Integer)", "Location"),
    ("District", "เขตตำรวจ (District)", "ตัวเลข (Numeric/Integer)", "Location"),
    ("Ward", "เขตการเลือกตั้ง (Ward)", "ตัวเลข (Numeric)", "Location"),
    ("Community Area", "เขตชุมชน (Community area)", "ตัวเลข (Numeric)", "Location"),
    ("Location Description", "ประเภทสถานที่ (Location description)", "หมวดหมู่ (Categorical)", "Location"),
    ("X Coordinate", "พิกัดแกน X (X coordinate)", "ตัวเลข (Numeric)", "Geo"),
    ("Y Coordinate", "พิกัดแกน Y (Y coordinate)", "ตัวเลข (Numeric)", "Geo"),
    ("Latitude", "ละติจูด (Latitude)", "ตัวเลขทศนิยม (Numeric/Float)", "Geo"),
    ("Longitude", "ลองจิจูด (Longitude)", "ตัวเลขทศนิยม (Numeric/Float)", "Geo"),
    ("Location", "พิกัดคู่ (Lat, Long) (Location tuple text)", "ข้อความ/ออบเจกต์ (Object/String)", "Geo"),
]

MISSING_HANDLING = {
    "Case Number": "ลบแถว (Drop rows) – ฟีเจอร์หลักของเหตุการณ์",
    "Date": "ลบแถว (Drop rows) – ใช้วิเคราะห์เวลา/แนวโน้ม",
    "Block": "ลบแถว (Drop rows) – ระบุตำแหน่งเหตุ",
    "IUCR": "ลบแถว (Drop rows) – รหัสมาตรฐานประเภทคดี",
    "Primary Type": "ลบแถว (Drop rows) – ใช้วิเคราะห์ประเภทคดี",
    "Description": "ลบแถว (Drop rows) – รายละเอียดสำคัญ",
    "Arrest": "ลบแถว (Drop rows) – ใช้คำนวณสัดส่วนจับกุม",
    "Domestic": "ลบแถว (Drop rows) – ใช้แยก domestic/non-domestic",
    "Beat": "ลบแถว (Drop rows) – รหัสพื้นที่",
    "District": "ลบแถว (Drop rows) – รหัสพื้นที่",
    "FBI Code": "ลบแถว (Drop rows) – รหัสจัดกลุ่ม",
    "Year": "ลบแถว (Drop rows) – เงื่อนไขตามช่วงปี",
    "Updated On": "ลบแถว (Drop rows) – ความสมบูรณ์ของข้อมูล",
    "Location Description": "เติมค่า (Fill) = UNKNOWN – missing ต่ำ (~0.41%)",
    "Ward": "ตัดคอลัมน์ (Drop column) – missing สูงมาก (~69%)",
    "Community Area": "ตัดคอลัมน์ (Drop column) – missing สูงมาก (~68%)",
    "Latitude": "กรองเฉพาะตอนทำแผนที่ (Map-only filter) – ไม่ลบจากชุดหลัก",
    "Longitude": "กรองเฉพาะตอนทำแผนที่ (Map-only filter) – ไม่ลบจากชุดหลัก",
    "X Coordinate": "กรองเฉพาะตอนทำแผนที่ (Map-only filter) – ไม่ลบจากชุดหลัก",
    "Y Coordinate": "กรองเฉพาะตอนทำแผนที่ (Map-only filter) – ไม่ลบจากชุดหลัก",
    "Location": "กรองเฉพาะตอนทำแผนที่ (Map-only filter) – ไม่ลบจากชุดหลัก",
}

def dtype_str(s: pd.Series) -> str:
    try:
        return str(s.dtype)
    except Exception:
        return "unknown"

def missing_count_pct(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return None, None
    cnt = int(df[col].isna().sum())
    pct = float(df[col].isna().mean() * 100)
    return cnt, pct

def build_data_dictionary(df_b: pd.DataFrame, df_a: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, meaning, expected_type, group in FEATURE_INFO:
        b_dtype = dtype_str(df_b[col]) if col in df_b.columns else "-"
        a_dtype = dtype_str(df_a[col]) if col in df_a.columns else "-"
        handling = MISSING_HANDLING.get(col, "ไม่ระบุ (Not specified)")
        rows.append(
            {
                "ฟีเจอร์ (Feature)": col,
                "กลุ่ม (Group)": group,
                "ความหมาย (Meaning)": meaning,
                "ชนิดข้อมูลที่ควรเป็น (Expected type)": expected_type,
                "ชนิดข้อมูลก่อน (Before dtype)": b_dtype,
                "ชนิดข้อมูลหลัง (After dtype)": a_dtype,
                "แนวทางจัดการ Missing (Handling)": handling,
            }
        )
    return pd.DataFrame(rows)

def build_missing_compare(df_b: pd.DataFrame, df_a: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_cols = sorted(set(df_b.columns).union(set(df_a.columns)))
    for col in all_cols:
        b_cnt, b_pct = missing_count_pct(df_b, col)
        a_cnt, a_pct = missing_count_pct(df_a, col)
        rows.append(
            {
                "ฟีเจอร์ (Feature)": col,
                "Missing ก่อน (Count)": "-" if b_cnt is None else f"{b_cnt:,}",
                "Missing ก่อน (%)": "-" if b_pct is None else f"{b_pct:.4f}",
                "Missing หลัง (Count)": "-" if a_cnt is None else f"{a_cnt:,}",
                "Missing หลัง (%)": "-" if a_pct is None else f"{a_pct:.4f}",
                "วิธีจัดการ (Method)": MISSING_HANDLING.get(col, "-"),
            }
        )
    df_out = pd.DataFrame(rows)

    def sort_key(x):
        try:
            return float(x)
        except Exception:
            return -1.0

    df_out["_sort"] = df_out["Missing หลัง (%)"].apply(sort_key)
    df_out = df_out.sort_values("_sort", ascending=False).drop(columns=["_sort"])
    return df_out

# ==============================
# Helpers: charts
# ==============================
def top_bar_before_after(df_b: pd.DataFrame, df_a: pd.DataFrame, col: str, k: int, mode: str):
    tb = df_b[col].value_counts().head(k).reset_index()
    tb.columns = [col, "Count"]
    ta = df_a[col].value_counts().head(k).reset_index()
    ta.columns = [col, "Count"]

    if mode.startswith("Share"):
        tb["Value"] = (tb["Count"] / max(tb["Count"].sum(), 1)) * 100
        ta["Value"] = (ta["Count"] / max(ta["Count"].sum(), 1)) * 100
        x_title = "Share (%)"
        text_fmt = ".2f"
    else:
        tb["Value"] = tb["Count"]
        ta["Value"] = ta["Count"]
        x_title = "Count"
        text_fmt = ","

    max_x = float(max(tb["Value"].max(), ta["Value"].max())) if (len(tb) and len(ta)) else None

    fig_b = px.bar(
        tb,
        x="Value",
        y=col,
        orientation="h",
        title="ก่อนทำความสะอาด (Before)",
        text="Value",
    )
    fig_b.update_traces(texttemplate=f"%{{text:{text_fmt}}}", textposition="outside")
    fig_b.update_layout(xaxis_title=x_title, yaxis_title=col, margin=dict(l=10, r=10, t=50, b=10))
    if max_x is not None:
        fig_b.update_xaxes(range=[0, max_x * 1.10])

    fig_a = px.bar(
        ta,
        x="Value",
        y=col,
        orientation="h",
        title="หลังทำความสะอาด (After)",
        text="Value",
    )
    fig_a.update_traces(texttemplate=f"%{{text:{text_fmt}}}", textposition="outside")
    fig_a.update_layout(xaxis_title=x_title, yaxis_title=col, margin=dict(l=10, r=10, t=50, b=10))
    if max_x is not None:
        fig_a.update_xaxes(range=[0, max_x * 1.10])

    return fig_b, fig_a

def safe_rate(series: pd.Series):
    if series.empty:
        return 0.0
    s = series.astype(str)
    return float((s == "True").mean() * 100)

# ------------------------------
# TAB 1: Overview (Executive Summary)
# ------------------------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📌 จำนวนแถว (Rows) - ก่อน", f"{b.shape[0]:,}")
    c2.metric("✅ จำนวนแถว (Rows) - หลัง", f"{a.shape[0]:,}")

    miss_b = int(b.isna().sum().sum())
    miss_a = int(a.isna().sum().sum())
    c3.metric("⚠️ Missing - ก่อน", f"{miss_b:,}")
    c4.metric("🧼 Missing - หลัง", f"{miss_a:,}")

    st.divider()

    colK1, colK2, colK3, colK4 = st.columns(4)
    arrest_rate = safe_rate(a["Arrest"]) if "Arrest" in a.columns else 0.0
    domestic_rate = safe_rate(a["Domestic"]) if "Domestic" in a.columns else 0.0
    has_geo = int(a.dropna(subset=["Latitude", "Longitude"]).shape[0]) if ("Latitude" in a.columns and "Longitude" in a.columns) else 0

    colK1.metric("👮 Arrest Rate (After)", f"{arrest_rate:.2f}%")
    colK2.metric("🏠 Domestic Share (After)", f"{domestic_rate:.2f}%")
    colK3.metric("🗺️ แถวที่มีพิกัด (After)", f"{has_geo:,}")
    colK4.metric("📅 ช่วงปีที่เลือก", f"{year_range[0]}–{year_range[1]}")

    st.caption("หมายเหตุ: KPI จะเปลี่ยนตามตัวกรอง (Filters) เพื่อให้ตอบคำถามกรรมการได้ทันที")

    st.divider()

    # Top Crime Types (Scale locked + labels)
    st.subheader("ประเภทคดีสูงสุด (Top Crime Types)")
    if "Primary Type" in b.columns and "Primary Type" in a.columns:
        fig_b, fig_a = top_bar_before_after(b, a, "Primary Type", top_k, metric_mode)
        colL, colR = st.columns(2)
        with colL:
            st.plotly_chart(fig_b, use_container_width=True)
        with colR:
            st.plotly_chart(fig_a, use_container_width=True)

        insight_card(
            "Insight 1: คดีลักทรัพย์ (Theft) พบบ่อยที่สุด",
            "Theft มีจำนวนสูงสุดเมื่อเทียบกับ Battery และ Criminal Damage",
            "สะท้อนความเสี่ยงหลักเป็นคดีในพื้นที่สาธารณะและเกิดซ้ำบ่อย",
            "โฟกัสจุดเสี่ยง (Hotspot) เช่น เพิ่ม CCTV/ไฟส่องสว่าง/ลาดตระเวน",
        )
    else:
        st.warning("ไม่พบคอลัมน์ Primary Type ในไฟล์")

    st.divider()

    # Arrest Rate (Pie)
    st.subheader("สัดส่วนการจับกุม (Arrest Rate)")
    if "Arrest" in b.columns and "Arrest" in a.columns:
        colL2, colR2 = st.columns(2)

        arrest_b = (b["Arrest"].value_counts(normalize=True) * 100).reset_index()
        arrest_b.columns = ["Arrest", "Percent"]

        arrest_a = (a["Arrest"].value_counts(normalize=True) * 100).reset_index()
        arrest_a.columns = ["Arrest", "Percent"]

        with colL2:
            fig3 = px.pie(arrest_b, values="Percent", names="Arrest", title="Before")
            st.plotly_chart(fig3, use_container_width=True)

        with colR2:
            fig4 = px.pie(arrest_a, values="Percent", names="Arrest", title="After")
            st.plotly_chart(fig4, use_container_width=True)

        insight_card(
            "Insight 2: อัตราการจับกุมต่ำ (Low Arrest Rate)",
            "สัดส่วนคดีที่จับกุมได้มีน้อยเมื่อเทียบกับคดีทั้งหมด",
            "สะท้อนช่องว่างด้านการเฝ้าระวัง/หลักฐาน โดยเฉพาะคดีพื้นที่สาธารณะ",
            "เพิ่ม Surveillance (กล้อง/ไฟ/จุดตรวจ) และใช้การวิเคราะห์ข้อมูลช่วยจัดลำดับพื้นที่เสี่ยง",
        )
    else:
        st.warning("ไม่พบคอลัมน์ Arrest ในไฟล์")

    st.divider()

    # Trend by Year (line)
    st.subheader("แนวโน้มจำนวนคดีตามปี (Trend by Year)")
    if "Year" in b.columns and "Year" in a.columns:
        yb = b["Year"].value_counts().sort_index().reset_index()
        yb.columns = ["Year", "Count"]
        yb["Dataset"] = "Before"

        ya = a["Year"].value_counts().sort_index().reset_index()
        ya.columns = ["Year", "Count"]
        ya["Dataset"] = "After"

        yy = pd.concat([yb, ya], ignore_index=True)
        fig5 = px.line(yy, x="Year", y="Count", color="Dataset", markers=True)
        fig5.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig5, use_container_width=True)

        insight_card(
            "Insight 5: จำนวนคดีผันผวนตามปี (Yearly Fluctuation)",
            "จำนวนคดีขึ้นลงตามปี และบางปีอาจสูงผิดปกติเมื่อเทียบกับปีข้างเคียง",
            "สะท้อนอิทธิพลปัจจัยภายนอก เช่น เศรษฐกิจ/นโยบาย/สังคม",
            "ใช้ Trend เพื่อวางแผนทรัพยากร (Resource Planning) และมาตรการเชิงป้องกันล่วงหน้า",
        )
    else:
        st.info("ทำกราฟแนวโน้มไม่ได้ เพราะไม่พบ Year/Date")

# ------------------------------
# TAB 2: Data Quality
# ------------------------------
with tab2:
    st.subheader("Missing ต่อคอลัมน์ (Missing by Column)")
    st.caption("แสดง Top 15 เพื่อชี้คอลัมน์ที่ควรจัดการก่อน (Prioritize fields)")

    colQ1, colQ2 = st.columns(2)

    with colQ1:
        miss_col_b = (b.isna().mean() * 100).sort_values(ascending=False).head(15).reset_index()
        miss_col_b.columns = ["Column", "MissingPercent"]
        fig6 = px.bar(miss_col_b, x="MissingPercent", y="Column", orientation="h", title="Before (Top 15)")
        st.plotly_chart(fig6, use_container_width=True)

    with colQ2:
        miss_col_a = (a.isna().mean() * 100).sort_values(ascending=False).head(15).reset_index()
        miss_col_a.columns = ["Column", "MissingPercent"]
        fig7 = px.bar(miss_col_a, x="MissingPercent", y="Column", orientation="h", title="After (Top 15)")
        st.plotly_chart(fig7, use_container_width=True)

    st.divider()

    st.subheader("ค่าผิดปกติพิกัด (Outlier: Latitude/Longitude)")
    st.caption("ใช้ Box plot (กล่องสถิติ) เพื่อชี้ค่าที่หลุดช่วง และช่วยตัดสินใจกรองก่อนทำแผนที่ (Map)")

    cols = st.columns(2)
    if "Latitude" in b.columns and "Latitude" in a.columns:
        with cols[0]:
            fig8 = px.box(b, y="Latitude", title="Latitude - Before")
            st.plotly_chart(fig8, use_container_width=True)
        with cols[1]:
            fig9 = px.box(a, y="Latitude", title="Latitude - After")
            st.plotly_chart(fig9, use_container_width=True)

    cols2 = st.columns(2)
    if "Longitude" in b.columns and "Longitude" in a.columns:
        with cols2[0]:
            fig10 = px.box(b, y="Longitude", title="Longitude - Before")
            st.plotly_chart(fig10, use_container_width=True)
        with cols2[1]:
            fig11 = px.box(a, y="Longitude", title="Longitude - After")
            st.plotly_chart(fig11, use_container_width=True)

    st.divider()

    st.subheader("ชุดข้อมูลสำหรับทำแผนที่ (Map-ready subset)")
    if "Latitude" in a.columns and "Longitude" in a.columns:
        map_df = a.dropna(subset=["Latitude", "Longitude"]).copy()
        st.write(f"จำนวนแถวที่มีพิกัดพร้อมใช้: **{map_df.shape[0]:,}** จาก **{a.shape[0]:,}**")
        st.caption("แนวทาง: ไม่ลบจากชุดหลัก แต่กรองเฉพาะตอนทำแผนที่ (Map-only filtering)")
        cols_show = [c for c in ["Date", "Primary Type", "Location Description", "Latitude", "Longitude"] if c in map_df.columns]
        st.dataframe(map_df[cols_show].head(20), use_container_width=True)
    else:
        st.info("ไม่มีคอลัมน์ Latitude/Longitude ในไฟล์ clean")

# ------------------------------
# TAB 3: Exploration (Add Hotspot Map)
# ------------------------------
with tab3:
    st.subheader("คดีตามพื้นที่ (District / Community Area / Ward)")

    available_dims = [c for c in ["District", "Community Area", "Ward"] if (c in b.columns and c in a.columns)]
    if not available_dims:
        st.warning("ไม่พบคอลัมน์ District/Community Area/Ward ที่ตรงกันทั้ง Before และ After")
    else:
        pick = st.selectbox("เลือกมิติพื้นที่ (Location Dimension)", available_dims)
        colE1, colE2 = st.columns(2)

        top_loc_b = b[pick].value_counts().head(15).reset_index()
        top_loc_b.columns = [pick, "Count"]
        top_loc_a = a[pick].value_counts().head(15).reset_index()
        top_loc_a.columns = [pick, "Count"]

        fig12 = px.bar(top_loc_b, x="Count", y=pick, orientation="h", title=f"{pick} - Before (Top 15)", text="Count")
        fig12.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig13 = px.bar(top_loc_a, x="Count", y=pick, orientation="h", title=f"{pick} - After (Top 15)", text="Count")
        fig13.update_traces(texttemplate="%{text:,}", textposition="outside")

        max_x = float(max(top_loc_b["Count"].max(), top_loc_a["Count"].max())) if (len(top_loc_b) and len(top_loc_a)) else None
        if max_x is not None:
            fig12.update_xaxes(range=[0, max_x * 1.10])
            fig13.update_xaxes(range=[0, max_x * 1.10])

        with colE1:
            st.plotly_chart(fig12, use_container_width=True)
        with colE2:
            st.plotly_chart(fig13, use_container_width=True)

    st.divider()

    st.subheader("จุดเกิดเหตุ (Location Description) Top 15")
    if "Location Description" in b.columns and "Location Description" in a.columns:
        colLD1, colLD2 = st.columns(2)

        ld_b = b["Location Description"].fillna("UNKNOWN").value_counts().head(15).reset_index()
        ld_b.columns = ["Location Description", "Count"]

        ld_a = a["Location Description"].fillna("UNKNOWN").value_counts().head(15).reset_index()
        ld_a.columns = ["Location Description", "Count"]

        fig_ld1 = px.bar(ld_b, x="Count", y="Location Description", orientation="h", title="Before (Top 15)", text="Count")
        fig_ld1.update_traces(texttemplate="%{text:,}", textposition="outside")

        fig_ld2 = px.bar(ld_a, x="Count", y="Location Description", orientation="h", title="After (Top 15)", text="Count")
        fig_ld2.update_traces(texttemplate="%{text:,}", textposition="outside")

        max_x2 = float(max(ld_b["Count"].max(), ld_a["Count"].max())) if (len(ld_b) and len(ld_a)) else None
        if max_x2 is not None:
            fig_ld1.update_xaxes(range=[0, max_x2 * 1.10])
            fig_ld2.update_xaxes(range=[0, max_x2 * 1.10])

        with colLD1:
            st.plotly_chart(fig_ld1, use_container_width=True)
        with colLD2:
            st.plotly_chart(fig_ld2, use_container_width=True)

        insight_card(
            "Insight 4: จุดเกิดเหตุสูงสุดคือถนน (STREET)",
            "Location Description ที่พบบ่อยที่สุดคือ STREET รองลงมาคือ Residence/Apartment",
            "พื้นที่สาธารณะเสี่ยงสูงและควบคุมยากกว่าพื้นที่ปิด",
            "โฟกัสความปลอดภัยบนถนน เช่น เพิ่มไฟส่องสว่าง/กล้อง/ลาดตระเวนในโซนเสี่ยง",
        )
    else:
        st.info("ไม่พบคอลัมน์ Location Description")

    st.divider()

    st.subheader("คดีในครอบครัว vs นอกครอบครัว (Domestic vs Non-Domestic)")
    if "Domestic" in b.columns and "Domestic" in a.columns:
        colD1, colD2 = st.columns(2)

        dom_b = (b["Domestic"].value_counts(normalize=True) * 100).reset_index()
        dom_b.columns = ["Domestic", "Percent"]

        dom_a = (a["Domestic"].value_counts(normalize=True) * 100).reset_index()
        dom_a.columns = ["Domestic", "Percent"]

        with colD1:
            fig_dom1 = px.pie(dom_b, values="Percent", names="Domestic", title="Before")
            st.plotly_chart(fig_dom1, use_container_width=True)
        with colD2:
            fig_dom2 = px.pie(dom_a, values="Percent", names="Domestic", title="After")
            st.plotly_chart(fig_dom2, use_container_width=True)

        insight_card(
            "Insight 3: คดีส่วนใหญ่เป็นนอกครอบครัว (Non-Domestic)",
            "สัดส่วนคดี Non-Domestic สูงกว่า Domestic อย่างชัดเจน",
            "ความเสี่ยงหลักอยู่ในพื้นที่สาธารณะมากกว่าคดีในบ้าน/ครอบครัว",
            "เน้นมาตรการความปลอดภัยพื้นที่สาธารณะควบคู่ระบบช่วยเหลือกรณี Domestic",
        )
    else:
        st.info("ไม่พบคอลัมน์ Domestic")

    st.divider()

    st.subheader("แผนที่จุดเสี่ยง (Hotspot Map)")
    st.caption("แสดงเฉพาะแถวที่มี Latitude/Longitude (OpenStreetMap ไม่ต้องใช้ token)")

    if "Latitude" in a.columns and "Longitude" in a.columns:
        map_df = a.dropna(subset=["Latitude", "Longitude"]).copy()
        map_df = map_df[(map_df["Latitude"].between(-90, 90)) & (map_df["Longitude"].between(-180, 180))]

        # จำกัดจำนวนจุดเพื่อให้แผนที่ลื่น (competition usability)
        max_points = 3000
        if map_df.shape[0] > max_points:
            map_df = map_df.sample(max_points, random_state=42)

        hover_cols = [c for c in ["Primary Type", "Location Description", "Date", "District"] if c in map_df.columns]
        fig_map = px.scatter_mapbox(
            map_df,
            lat="Latitude",
            lon="Longitude",
            hover_data=hover_cols,
            zoom=9,
            height=520,
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("ไม่มีคอลัมน์ Latitude/Longitude ในไฟล์ clean")

    st.divider()

    st.subheader("ตารางตัวอย่าง (Sample Table) - After")
    st.dataframe(a.head(50), use_container_width=True)

# ------------------------------
# TAB 4: Cleaning Process (คงของเดิม + ปรับให้ยืดหยุ่น)
# ------------------------------
with tab4:
    st.header("ขั้นตอนการจัดการข้อมูล (Data Cleaning Process)")

    st.markdown("### 1) สรุปภาพรวมก่อน–หลัง (Before vs After)")
    colP1, colP2, colP3, colP4 = st.columns(4)
    colP1.metric("ก่อน: จำนวนแถว (Rows)", f"{df_before.shape[0]:,}")
    colP2.metric("ก่อน: จำนวนฟีเจอร์ (Features)", f"{df_before.shape[1]:,}")
    colP3.metric("หลัง: จำนวนแถว (Rows)", f"{df_after.shape[0]:,}")
    colP4.metric("หลัง: จำนวนฟีเจอร์ (Features)", f"{df_after.shape[1]:,}")
    st.caption("หมายเหตุ: หลังทำความสะอาดมีการตัดฟีเจอร์ที่ missing สูงมากออก (Ward, Community Area)")

    st.divider()

    st.markdown("### 2) ตรวจสอบคุณภาพข้อมูล (Data Quality Check)")
    st.markdown(
        """
- ตรวจสอบข้อมูลขาดหาย (Missing values) พบว่าบางฟีเจอร์มี missing สูงมาก เช่น **Ward (~69%)** และ **Community Area (~68%)**
- ตรวจสอบข้อมูลซ้ำ (Duplicates) (แนะนำ: ตรวจ Case Number + Date + IUCR เพื่อความมั่นใจ)
- สรุป: จำเป็นต้องทำความสะอาดข้อมูลก่อนวิเคราะห์ เพื่อให้ผลลัพธ์น่าเชื่อถือและตรวจสอบย้อนกลับได้
"""
    )

    st.divider()

    st.markdown("### 3) การจัดการข้อมูลขาดหาย (Missing Value Handling)")
    st.markdown(
        """
**A) ลบแถว (Drop rows)**  
ลบแถวที่มีค่าว่างในฟีเจอร์สำคัญ เช่น Case Number, Date, IUCR, Primary Type, Description, Arrest, Domestic, Beat, District, FBI Code ฯลฯ  
เหตุผล: เป็นข้อมูลแกนหลักสำหรับระบุเหตุการณ์/เวลา/ประเภทคดี และใช้คำนวณสถิติหลัก

**B) เติมค่า UNKNOWN (Fill 'UNKNOWN')**  
Location Description missing ต่ำ (~0.41%) จึงเติมค่า **UNKNOWN**  
เหตุผล: รักษาจำนวนเรคอร์ด และไม่ทำให้สถิติหลักเพี้ยนมาก

**C) ตัดคอลัมน์ (Drop columns)**  
Ward และ Community Area missing สูงมาก (>65%) จึงตัดออก  
เหตุผล: ลดการเดาค่า (Imputation) ที่เสี่ยงผิด และลด bias

**D) พิกัดสำหรับแผนที่ (Map-only filtering)**  
Latitude/Longitude/Location หาก missing ให้กรองเฉพาะตอนทำแผนที่  
เหตุผล: ไม่ทำให้การวิเคราะห์ประเภทคดี/แนวโน้มเสีย แต่ทำ Map ได้ถูกต้อง
"""
    )

    st.divider()

    st.markdown("### 4) การจัดรูปแบบ/ความสอดคล้อง (Format & Consistency)")
    st.markdown(
        """
- Date, Updated On → แปลงเป็น datetime
- Arrest / Domestic → Boolean (True/False)
- Beat / District → Integer (รหัสพื้นที่)
- Year → คำนวณจาก Date และใช้กรองช่วงปี
- Latitude/Longitude → ตรวจช่วงค่า (Latitude: -90..90, Longitude: -180..180) เพื่อกันค่าหลุดช่วง
"""
    )

    st.divider()

    st.markdown("### 5) การตรวจค่าผิดปกติ (Outlier Handling)")
    st.markdown(
        """
- ตรวจ Outlier ที่ Latitude/Longitude ด้วย Box plot
- ใช้แนวทาง “Map-only filtering” คือกรองก่อนทำแผนที่ แต่ไม่ทำให้ชุดวิเคราะห์หลักเสีย
"""
    )

    st.divider()

    st.markdown("### 6) Insight สรุปจากข้อมูล (Evidence-based Insights)")
    st.caption("สรุปแบบ What → So What → Now What เพื่อใช้ในสไลด์/ตอบกรรมการ")

    insight_card(
        "Insight: คดีลักทรัพย์ (Theft) มากที่สุด",
        "Theft เป็นประเภทคดีที่พบมากที่สุดเมื่อเทียบกับประเภทอื่น",
        "ชี้ว่าความเสี่ยงหลักคือคดีในพื้นที่สาธารณะและเกิดซ้ำ",
        "ใช้ผลนี้เพื่อกำหนดโซนเสี่ยงและวางมาตรการป้องกันเชิงรุก",
    )
    insight_card(
        "Insight: อัตราการจับกุมต่ำ (Low Arrest Rate)",
        "สัดส่วนการจับกุมมีน้อยเมื่อเทียบกับคดีทั้งหมด",
        "สะท้อนช่องว่างด้านความปลอดภัยและการบังคับใช้กฎหมาย",
        "เพิ่มการเฝ้าระวัง/กล้อง/การวิเคราะห์ข้อมูลเพื่อสนับสนุนการสืบสวน",
    )
    insight_card(
        "Insight: คดีส่วนใหญ่เป็นนอกครอบครัว (Non-Domestic)",
        "สัดส่วน Non-Domestic มากกว่า Domestic อย่างชัดเจน",
        "ความเสี่ยงหลักอยู่ในพื้นที่สาธารณะมากกว่าคดีในบ้าน",
        "นโยบายควรเน้นพื้นที่สาธารณะควบคู่มาตรการช่วยเหลือคดีในครอบครัว",
    )
    insight_card(
        "Insight: จุดเกิดเหตุหลักคือถนน (STREET)",
        "Location Description ที่พบบ่อยสุดคือ STREET",
        "ถนนเป็นพื้นที่เปิด สัญจรสูง ควบคุมยาก",
        "เพิ่มไฟส่องสว่าง/กล้อง/ลาดตระเวนในโซนถนนสำคัญ",
    )
    insight_card(
        "Insight: จำนวนคดีผันผวนตามปี (Yearly Fluctuation)",
        "จำนวนคดีขึ้นลงตามปี และบางปีอาจสูงกว่าปกติ",
        "สะท้อนปัจจัยภายนอก เช่น เศรษฐกิจ/สังคม",
        "ใช้เทรนด์เพื่อวางแผนกำลังคนและมาตรการเชิงป้องกันล่วงหน้า",
    )

# ------------------------------
# TAB 5: Data Dictionary
# ------------------------------
with tab5:
    st.header("พจนานุกรมข้อมูล (Data Dictionary)")
    st.caption("อธิบายว่าฟีเจอร์เก็บข้อมูลอะไร และชนิดข้อมูล (Data type) ก่อน–หลัง")

    dd = build_data_dictionary(df_before, df_after)
    st.dataframe(dd, use_container_width=True, height=520)

    st.divider()

    st.subheader("สรุปขนาดข้อมูล (Dataset Size Summary)")
    colS1, colS2, colS3, colS4 = st.columns(4)
    colS1.metric("ก่อน: แถว (Rows)", f"{df_before.shape[0]:,}")
    colS2.metric("ก่อน: ฟีเจอร์ (Columns)", f"{df_before.shape[1]:,}")
    colS3.metric("หลัง: แถว (Rows)", f"{df_after.shape[0]:,}")
    colS4.metric("หลัง: ฟีเจอร์ (Columns)", f"{df_after.shape[1]:,}")

    st.info(
        f"หลังจัดการ Missing แล้ว จำนวนข้อมูลเปลี่ยนจาก **{df_before.shape[0]:,} แถว** → "
        f"**{df_after.shape[0]:,} แถว** (ลดลง **{df_before.shape[0] - df_after.shape[0]:,} แถว**) "
        f"และจำนวนฟีเจอร์จาก **{df_before.shape[1]}** → **{df_after.shape[1]}**"
    )

# ------------------------------
# TAB 6: Missing Compare
# ------------------------------
with tab6:
    st.header("เปรียบเทียบ Missing ก่อน–หลัง (Missing Comparison)")
    st.caption("แสดงจำนวน (Count) และร้อยละ (%) ของ Missing ก่อนจัดการ vs หลังจัดการ")

    miss_cmp = build_missing_compare(df_before, df_after)
    st.dataframe(miss_cmp, use_container_width=True, height=520)

    st.divider()

    st.subheader("สรุปวิธีจัดการ Missing (Methods Summary)")
    st.markdown(
        """
- **ลบแถว (Drop rows):** ใช้กับฟีเจอร์แกนหลัก เช่น Case Number, Date, IUCR, Primary Type, Arrest, District ฯลฯ  
  เหตุผล: ถ้าหายจะวิเคราะห์ประเภทคดี/เวลา/สัดส่วนจับกุมไม่ถูกต้อง

- **เติมค่า (Fill):** Location Description เติม **UNKNOWN**  
  เหตุผล: missing ต่ำ (~0.41%) และเป็นข้อมูลหมวดหมู่

- **ตัดคอลัมน์ (Drop column):** Ward และ Community Area  
  เหตุผล: missing สูงมาก (~69% และ ~68%) เสี่ยง bias

- **กรองเฉพาะตอนทำแผนที่ (Map-only filtering):** Latitude/Longitude/Location/X/Y  
  เหตุผล: ไม่กระทบการวิเคราะห์ภาพรวม แต่ทำให้แผนที่แม่นยำ
"""
    )
