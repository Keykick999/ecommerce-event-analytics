import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# DB Connection

def get_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="analytics_db",
            user="user",
            password="password",
            port=5433
        )
    except Exception as e:
        st.error(f"데이터베이스 연결에 실패했습니다. Docker가 실행 중인지 확인해 주세요. ({e})")
        st.stop()

st.set_page_config(page_title="E-commerce Analytics Dashboard", layout="wide")

st.title("📊 E-commerce Discovery vs. Purchase Analytics")
st.markdown("이 대시보드는 상품에 대한 관심(조회)과 결과(결제)의 차이를 분석하여 비즈니스 인사이트를 제공합니다.")

# Sidebar Filters
st.sidebar.header("Filters")
conn = get_connection()
categories_df = pd.read_sql("SELECT DISTINCT category FROM products", conn)
selected_category = st.sidebar.selectbox("Select Category", ["All"] + list(categories_df['category']))

# Main Metrics
st.subheader(f"Current Performance: {selected_category}")

category_filter = "" if selected_category == "All" else f"AND p.category = '{selected_category}'"

# Query for Metrics
metrics_query = f"""
    SELECT 
        COUNT(*) FILTER (WHERE event_type = 'page_view') as total_views,
        COUNT(*) FILTER (WHERE event_type = 'purchase') as total_purchases,
        COUNT(DISTINCT user_id) as unique_users
    FROM events e
    JOIN products p ON e.product_id = p.product_id
    WHERE 1=1 {category_filter}
"""
metrics_df = pd.read_sql(metrics_query, conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Views", metrics_df['total_views'][0])
col2.metric("Total Purchases", metrics_df['total_purchases'][0])
col3.metric("Unique Users", metrics_df['unique_users'][0])

cvr = (metrics_df['total_purchases'][0] / metrics_df['total_views'][0] * 100) if metrics_df['total_views'][0] > 0 else 0
col4.metric("Conversion Rate (CVR)", f"{cvr:.2f}%")

# Analysis Charts
col_left, col_right = st.columns(2)

with col_left:
    st.write("### 🔥 Top 10 Most Viewed Products")
    view_query = f"""
        SELECT p.name, COUNT(*) as views
        FROM events e
        JOIN products p ON e.product_id = p.product_id
        WHERE e.event_type = 'page_view' {category_filter}
        GROUP BY p.name
        ORDER BY views DESC
        LIMIT 10
    """
    view_df = pd.read_sql(view_query, conn)
    if not view_df.empty:
        fig_view = px.bar(view_df, x='views', y='name', orientation='h', color='views', color_continuous_scale='Blues')
        st.plotly_chart(fig_view, use_container_width=True)
    else:
        st.info("No view data available.")

with col_right:
    st.write("### 💰 Top 10 Most Sold Products")
    sold_query = f"""
        SELECT p.name, COUNT(*) as sales
        FROM events e
        JOIN products p ON e.product_id = p.product_id
        WHERE e.event_type = 'purchase' {category_filter}
        GROUP BY p.name
        ORDER BY sales DESC
        LIMIT 10
    """
    sold_df = pd.read_sql(sold_query, conn)
    if not sold_df.empty:
        fig_sold = px.bar(sold_df, x='sales', y='name', orientation='h', color='sales', color_continuous_scale='Reds')
        st.plotly_chart(fig_sold, use_container_width=True)
    else:
        st.info("No purchase data available.")

st.divider()

# New Search Insights Section
st.subheader("🔍 Search & Intent Analysis")
col_s1, col_s2 = st.columns(2)

with col_s1:
    st.write("### 🔝 Top Search Keywords")
    search_query = f"""
        SELECT metadata->>'query_string' as keyword, COUNT(*) as count
        FROM events e
        WHERE event_type = 'search' 
        {"" if selected_category == "All" else f"AND metadata->>'selected_type' = '{selected_category}'"}
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 10
    """
    search_df = pd.read_sql(search_query, conn)
    if not search_df.empty:
        fig_search = px.pie(search_df, values='count', names='keyword', hole=.3, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_search, use_container_width=True)
    else:
        st.info("No search data available.")

with col_s2:
    st.write("### ⚠️ Zero-Result Searches (Bottlenecks)")
    zero_query = f"""
        SELECT metadata->>'query_string' as keyword, metadata->>'selected_type' as category, COUNT(*) as count
        FROM events e
        WHERE event_type = 'search' AND (metadata->>'result_count')::int = 0
        GROUP BY keyword, category
        ORDER BY count DESC
        LIMIT 5
    """
    zero_df = pd.read_sql(zero_query, conn)
    if not zero_df.empty:
        st.warning("사용자가 검색했지만 결과를 찾지 못한 키워드들입니다.")
        st.table(zero_df)
    else:
        st.success("모든 검색어가 하나 이상의 결과를 찾았습니다! (데이터가 더 쌓이면 나타납니다)")

st.divider()

# Error Log & System Health Section
st.subheader("🚨 System Health & Error Monitoring")
col_e1, col_e2 = st.columns([1, 2])

with col_e1:
    st.write("### Error Distribution")
    error_query = """
        SELECT metadata->>'error_code' as code, COUNT(*) as count
        FROM events WHERE event_type = 'error'
        GROUP BY code
    """
    error_dist_df = pd.read_sql(error_query, conn)
    if not error_dist_df.empty:
        fig_err = px.bar(error_dist_df, x='code', y='count', color='code', color_discrete_sequence=['#FF4B4B', '#FF9F9F'])
        st.plotly_chart(fig_err, use_container_width=True)
    else:
        st.info("No system errors detected yet.")

with col_e2:
    st.write("### Recent System Error Logs")
    detailed_error_query = """
        SELECT timestamp, metadata->>'error_code' as code, metadata->>'message' as message, metadata->>'page' as page
        FROM events WHERE event_type = 'error'
        ORDER BY timestamp DESC LIMIT 5
    """
    det_error_df = pd.read_sql(detailed_error_query, conn)
    if not det_error_df.empty:
        st.dataframe(det_error_df, use_container_width=True)
    else:
        st.success("System is running healthy.")

# Data Table
st.divider()
if st.checkbox("Show Raw Event Log (Last 50 Insights)"):
    log_query = """
        SELECT timestamp, event_type, user_id, 
               CASE 
                 WHEN product_id IS NOT NULL THEN (SELECT name FROM products WHERE product_id = events.product_id)
                 ELSE 'N/A'
               END as product_name,
               metadata 
        FROM events 
        ORDER BY timestamp DESC 
        LIMIT 50
    """
    st.dataframe(pd.read_sql(log_query, conn), use_container_width=True)

conn.close()

if st.button("Refresh Data"):
    st.rerun()
