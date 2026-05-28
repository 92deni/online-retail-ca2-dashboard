
import os
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(
    page_title="Online Retail Senior-Friendly Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# Path handling
# -----------------------------
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DATA_PATHS = [
    PROJECT_ROOT / "data" / "Online Retail.xlsx",
    PROJECT_ROOT / "Online Retail.xlsx",
    Path.cwd() / "data" / "Online Retail.xlsx",
    Path.cwd() / "Online Retail.xlsx",
]


# -----------------------------
# Senior-friendly design options
# -----------------------------
st.sidebar.title("⚙️ Dashboard Settings")
high_contrast = st.sidebar.toggle("High contrast mode", value=True)
large_text = st.sidebar.toggle("Large text mode", value=True)

base_font = "22px" if large_text else "18px"
title_font = "42px" if large_text else "34px"
card_font = "34px" if large_text else "28px"

if high_contrast:
    bg = "#0B1220"
    card = "#111827"
    text = "#F9FAFB"
    accent = "#FBBF24"
    soft = "#1F2937"
else:
    bg = "#F8FAFC"
    card = "#FFFFFF"
    text = "#111827"
    accent = "#2563EB"
    soft = "#E5E7EB"

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {bg};
            color: {text};
            font-size: {base_font};
        }}
        h1, h2, h3, h4, h5, h6, p, label, div {{
            color: {text};
        }}
        .main-title {{
            font-size: {title_font};
            font-weight: 800;
            margin-bottom: 0.2rem;
        }}
        .subtitle {{
            font-size: {base_font};
            color: {text};
            opacity: 0.95;
            margin-bottom: 1.2rem;
        }}
        .kpi-card {{
            background: {card};
            border: 2px solid {soft};
            border-radius: 24px;
            padding: 24px;
            min-height: 150px;
            box-shadow: 0px 8px 20px rgba(0,0,0,0.18);
        }}
        .kpi-label {{
            font-size: {base_font};
            opacity: 0.92;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: {card_font};
            font-weight: 800;
            color: {accent};
        }}
        .explain-box {{
            background: {card};
            border-left: 8px solid {accent};
            border-radius: 18px;
            padding: 22px;
            font-size: {base_font};
            margin: 14px 0px 22px 0px;
        }}
        .small-note {{
            font-size: {base_font};
            opacity: 0.9;
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Data loading
# -----------------------------
@st.cache_data(show_spinner=True)
def load_csv_or_empty(filename):
    path = OUTPUT_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=True)
def build_outputs_from_excel():
    data_path = None
    for p in DATA_PATHS:
        if p.exists():
            data_path = p
            break

    if data_path is None:
        return None

    df_raw = pd.read_excel(data_path)
    df = df_raw.copy()
    df.columns = [c.strip() for c in df.columns]
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["Description"] = df["Description"].astype(str).str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    df = df[~df["InvoiceNo"].str.startswith("C")]
    df = df.dropna(subset=["CustomerID"])
    df = df[df["Description"].notna()]
    df = df[~df["Description"].str.lower().isin(["nan", ""])]
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    df["CustomerID"] = df["CustomerID"].astype(int).astype(str)
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    qty_cap = df["Quantity"].quantile(0.999)
    price_cap = df["UnitPrice"].quantile(0.999)
    df_model = df[(df["Quantity"] <= qty_cap) & (df["UnitPrice"] <= price_cap)].copy()

    monthly_sales = df_model.groupby("InvoiceMonth", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    )

    top_products = df_model.groupby(["StockCode", "Description"], as_index=False).agg(
        Quantity=("Quantity", "sum"),
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
    ).sort_values("Revenue", ascending=False).head(30)

    top_countries = df_model.groupby("Country", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    ).sort_values("Revenue", ascending=False).head(30)

    basket_summary = df_model.groupby("InvoiceNo").agg(
        BasketItems=("StockCode", "nunique"),
        BasketQuantity=("Quantity", "sum"),
        BasketRevenue=("Revenue", "sum"),
        CustomerID=("CustomerID", "first"),
        Country=("Country", "first"),
        InvoiceDate=("InvoiceDate", "min"),
    ).reset_index()

    sales_by_country_month = df_model.groupby(["Country", "InvoiceMonth"], as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    )

    customer_segments = df_model.groupby("CustomerID", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Products=("StockCode", "nunique"),
        LastPurchase=("InvoiceDate", "max"),
    )

    customer_segments["Segment"] = pd.qcut(
        customer_segments["Revenue"],
        q=4,
        labels=["Low Value", "Medium Value", "High Value", "VIP"],
        duplicates="drop",
    )

    return {
        "clean": df_model,
        "monthly_sales": monthly_sales,
        "top_products": top_products,
        "top_countries": top_countries,
        "basket_summary": basket_summary,
        "sales_by_country_month": sales_by_country_month,
        "customer_segments": customer_segments,
    }


monthly_sales = load_csv_or_empty("monthly_sales.csv")
top_products = load_csv_or_empty("top_products.csv")
top_countries = load_csv_or_empty("top_countries.csv")
basket_summary = load_csv_or_empty("basket_summary.csv")
customer_segments = load_csv_or_empty("customer_segments.csv")
sales_by_country_month = load_csv_or_empty("sales_by_country_month.csv")
apriori_rules = load_csv_or_empty("apriori_rules.csv")
fpgrowth_rules = load_csv_or_empty("fpgrowth_rules.csv")
eval_df = load_csv_or_empty("recommender_evaluation.csv")

# If the notebook outputs do not exist yet, build key dashboard data directly from the Excel file.
if monthly_sales.empty or top_products.empty or top_countries.empty or basket_summary.empty:
    built = build_outputs_from_excel()
    if built is not None:
        monthly_sales = built["monthly_sales"]
        top_products = built["top_products"]
        top_countries = built["top_countries"]
        basket_summary = built["basket_summary"]
        sales_by_country_month = built["sales_by_country_month"]
        customer_segments = built["customer_segments"]


# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">🛒 Online Retail Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">A senior-friendly interactive dashboard for understanding sales, customers, products and machine learning opportunities.</div>',
    unsafe_allow_html=True,
)

if monthly_sales.empty:
    st.error(
        "No dashboard data found. Run the notebook first, or place 'Online Retail.xlsx' inside the data folder."
    )
    st.stop()


# -----------------------------
# Filters
# -----------------------------
available_countries = sorted(top_countries["Country"].dropna().unique().tolist()) if not top_countries.empty else []
selected_countries = st.sidebar.multiselect(
    "Choose countries",
    options=available_countries,
    default=available_countries[:5] if len(available_countries) >= 5 else available_countries,
)

if selected_countries and not basket_summary.empty:
    basket_filtered = basket_summary[basket_summary["Country"].isin(selected_countries)].copy()
else:
    basket_filtered = basket_summary.copy()

if selected_countries and not sales_by_country_month.empty:
    country_month_filtered = sales_by_country_month[sales_by_country_month["Country"].isin(selected_countries)].copy()
else:
    country_month_filtered = sales_by_country_month.copy()


# -----------------------------
# KPIs
# -----------------------------
total_revenue = monthly_sales["Revenue"].sum()
total_orders = monthly_sales["Orders"].sum()
total_customers = monthly_sales["Customers"].sum()
avg_order = basket_filtered["BasketRevenue"].mean() if not basket_filtered.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Revenue</div><div class="kpi-value">£{total_revenue:,.0f}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Orders</div><div class="kpi-value">{total_orders:,.0f}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Customer Activity</div><div class="kpi-value">{total_customers:,.0f}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Average Basket</div><div class="kpi-value">£{avg_order:,.0f}</div></div>', unsafe_allow_html=True)


st.markdown(
    """
    <div class="explain-box">
    <b>How to read this dashboard:</b> The large cards show the main business results. 
    The charts below show which months, countries and products matter most. 
    These patterns help explain why the dataset is useful for recommendation systems and Market Basket Analysis.
    </div>
    """,
    unsafe_allow_html=True,
)


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Sales Story",
    "🌍 Countries",
    "🎁 Products",
    "🤖 Machine Learning",
    "♿ 65+ Design"
])


with tab1:
    st.header("Sales over time")
    fig = px.line(
        monthly_sales,
        x="InvoiceMonth",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Trend",
    )
    fig.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26)
    st.plotly_chart(fig, use_container_width=True)

    if not basket_filtered.empty:
        fig2 = px.histogram(
            basket_filtered,
            x="BasketRevenue",
            nbins=40,
            title="Order Value Distribution",
        )
        fig2.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Country performance")
    show_countries = top_countries[top_countries["Country"].isin(selected_countries)] if selected_countries else top_countries
    fig = px.bar(
        show_countries.sort_values("Revenue", ascending=True),
        x="Revenue",
        y="Country",
        orientation="h",
        title="Revenue by Country",
    )
    fig.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26)
    st.plotly_chart(fig, use_container_width=True)

    if not country_month_filtered.empty:
        fig2 = px.area(
            country_month_filtered,
            x="InvoiceMonth",
            y="Revenue",
            color="Country",
            title="Country Revenue by Month",
        )
        fig2.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26)
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.header("Best products")
    top_n = st.slider("Number of products to show", min_value=5, max_value=30, value=15, step=5)
    product_chart = top_products.head(top_n).sort_values("Revenue", ascending=True)
    fig = px.bar(
        product_chart,
        x="Revenue",
        y="Description",
        orientation="h",
        title=f"Top {top_n} Products by Revenue",
        hover_data=["Quantity", "Orders"],
    )
    fig.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26, height=650)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Why this dataset is suitable for Machine Learning")
    st.markdown(
        """
        <div class="explain-box">
        This dataset is suitable because it contains <b>customers</b>, <b>products</b>, 
        <b>invoices</b>, <b>dates</b>, <b>quantities</b> and <b>prices</b>. 
        These fields allow three important retail models:
        <br><br>
        1. <b>User-user collaborative filtering</b>: recommend products using similar customers.<br>
        2. <b>Item-item collaborative filtering</b>: recommend products using similar products.<br>
        3. <b>Market Basket Analysis</b>: identify products frequently bought together.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not eval_df.empty:
        st.subheader("Recommendation model evaluation")
        st.dataframe(eval_df, use_container_width=True)

    rule_choice = st.radio("Choose association rules to view", ["Apriori", "FP-Growth"], horizontal=True)
    rules = apriori_rules if rule_choice == "Apriori" else fpgrowth_rules

    if not rules.empty and {"antecedents_text", "consequents_text", "lift", "confidence"}.issubset(rules.columns):
        st.subheader(f"Top {rule_choice} Market Basket Rules")
        display_rules = rules[["antecedents_text", "consequents_text", "support", "confidence", "lift"]].head(10)
        st.dataframe(display_rules, use_container_width=True)
    else:
        st.info("Apriori and FP-Growth were implemented in the Jupyter Notebook. The main association rule results are summarised in the written report, including support, confidence and lift.")

with tab5:
    st.header("Dashboard design for adults aged 65+")
    st.markdown(
        """
        <div class="explain-box">
        This dashboard was designed for adults aged 65+ by using:
        <br><br>
        ✅ Large text and large KPI cards<br>
        ✅ High contrast mode for easier reading<br>
        ✅ Simple tabs instead of crowded pages<br>
        ✅ Clear labels and plain English explanations<br>
        ✅ Limited number of charts per page<br>
        ✅ Interactive filters that are easy to understand<br>
        ✅ Business-focused insights instead of technical jargon
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not customer_segments.empty and "Segment" in customer_segments.columns:
        st.subheader("Customer value segments")
        segment_summary = customer_segments.groupby("Segment", as_index=False).agg(
            Customers=("CustomerID", "nunique"),
            Revenue=("Revenue", "sum"),
            AverageOrders=("Orders", "mean"),
        )
        fig = px.pie(
            segment_summary,
            names="Segment",
            values="Customers",
            title="Customer Segments by Count",
        )
        fig.update_layout(font=dict(size=18 if large_text else 14), title_font_size=26)
        st.plotly_chart(fig, use_container_width=True)


st.caption(
    "Dataset: UCI Online Retail Dataset. Dashboard prepared for CA2 Machine Learning for Business and Data Visualisation Techniques."
)
