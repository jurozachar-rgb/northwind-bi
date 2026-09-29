"""
Mini BI dashboard nad databázou Northwind (PostgreSQL / Supabase).
Spustenie:  streamlit run app.py
Pripojenie: premenná DATABASE_URL alebo .streamlit/secrets.toml
"""
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import bindparam, create_engine, text

st.set_page_config(page_title="Northwind BI", page_icon="📊", layout="wide")


# ---------- Pripojenie ----------
@st.cache_resource
def get_engine():
    url = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL")
    if not url:
        st.error("Chýba DATABASE_URL (env premenná alebo .streamlit/secrets.toml).")
        st.stop()
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=600)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


# ---------- Filtre ----------
years = query(
    "SELECT DISTINCT EXTRACT(YEAR FROM order_date)::int AS y FROM orders ORDER BY y"
)["y"].tolist()

st.sidebar.header("Filtre")
year_from, year_to = st.sidebar.select_slider(
    "Roky", options=years, value=(years[0], years[-1])
)
countries = query("SELECT DISTINCT ship_country FROM orders ORDER BY 1")["ship_country"].tolist()
sel_countries = st.sidebar.multiselect("Krajiny", countries, default=countries)

if not sel_countries:
    st.warning("Vyber aspoň jednu krajinu.")
    st.stop()

params = {"y1": year_from, "y2": year_to, "countries": tuple(sel_countries)}

# Spoločná časť dopytu – riadky objednávok s vypočítanou tržbou
BASE = """
    FROM orders o
    JOIN order_details d ON d.order_id = o.order_id
    JOIN products p      ON p.product_id = d.product_id
    JOIN categories c    ON c.category_id = p.category_id
    WHERE EXTRACT(YEAR FROM o.order_date) BETWEEN :y1 AND :y2
      AND o.ship_country IN :countries
"""
REVENUE = "d.unit_price * d.quantity * (1 - d.discount)"

def q(sql: str) -> pd.DataFrame:
    # expanding=True rozbalí zoznam krajín pre SQL podmienku IN
    stmt = text(sql).bindparams(bindparam("countries", expanding=True))
    with get_engine().connect() as conn:
        return pd.read_sql(stmt, conn, params={**params, "countries": list(params["countries"])})


# ---------- KPI ----------
st.title("📊 Northwind – predajný dashboard")

kpi = q(f"""
    SELECT SUM({REVENUE})              AS revenue,
           COUNT(DISTINCT o.order_id)  AS orders,
           COUNT(DISTINCT o.customer_id) AS customers
    {BASE}
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tržby", f"{kpi.revenue:,.0f} $".replace(",", " "))
c2.metric("Objednávky", int(kpi.orders))
c3.metric("Zákazníci", int(kpi.customers))
c4.metric("Priem. objednávka", f"{kpi.revenue / max(kpi.orders, 1):,.0f} $".replace(",", " "))

# ---------- Grafy ----------
monthly = q(f"""
    SELECT DATE_TRUNC('month', o.order_date)::date AS month, SUM({REVENUE}) AS revenue
    {BASE}
    GROUP BY 1 ORDER BY 1
""")
st.plotly_chart(
    px.line(monthly, x="month", y="revenue", markers=True, title="Tržby po mesiacoch"),
    use_container_width=True,
)

left, right = st.columns(2)

top_products = q(f"""
    SELECT p.product_name, SUM({REVENUE}) AS revenue
    {BASE}
    GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""")
left.plotly_chart(
    px.bar(top_products, x="revenue", y="product_name", orientation="h",
           title="Top 10 produktov").update_yaxes(autorange="reversed"),
    use_container_width=True,
)

by_category = q(f"""
    SELECT c.category_name, SUM({REVENUE}) AS revenue
    {BASE}
    GROUP BY 1 ORDER BY 2 DESC
""")
right.plotly_chart(
    px.pie(by_category, names="category_name", values="revenue", hole=0.4,
           title="Tržby podľa kategórie"),
    use_container_width=True,
)

by_country = q(f"""
    SELECT o.ship_country AS country, SUM({REVENUE}) AS revenue
    {BASE}
    GROUP BY 1 ORDER BY 2 DESC
""")
st.plotly_chart(
    px.choropleth(by_country, locations="country", locationmode="country names",
                  color="revenue", title="Tržby podľa krajiny"),
    use_container_width=True,
)

# ---------- Tabuľka ----------
with st.expander("Detail: top zákazníci"):
    top_customers = q(f"""
        SELECT cu.company_name, o.ship_country AS country,
               COUNT(DISTINCT o.order_id) AS orders, ROUND(SUM({REVENUE})::numeric, 2) AS revenue
        {BASE.replace("WHERE", "JOIN customers cu ON cu.customer_id = o.customer_id WHERE")}
        GROUP BY 1, 2 ORDER BY 4 DESC LIMIT 20
    """)
    st.dataframe(top_customers, use_container_width=True, hide_index=True)
    st.download_button("Stiahnuť CSV", top_customers.to_csv(index=False), "top_zakaznici.csv")
