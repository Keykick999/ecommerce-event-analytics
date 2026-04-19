import streamlit as st
import pandas as pd
import plotly.express as px
from data_service import DataService

# Initialize DataService
data_service = DataService()

# --- Page Config ---
st.set_page_config(page_title="이커머스 통합 관제 시스템", layout="wide", page_icon="🛡️")

# --- Header ---
st.title("🛡️ 통합 시스템 관제 및 비즈니스 분석")
st.markdown("실시간 고가용성 이커머스 이벤트 로그 파이프라인 및 이상 탐지 시스템")

# --- Sidebar ---
st.sidebar.header("🕹️ 컨트롤 센터")
categories_df = pd.read_sql("SELECT DISTINCT category FROM products", data_service.get_connection())
selected_cat = st.sidebar.selectbox("카테고리 필터", ["All"] + list(categories_df['category']))

# --- Tabs ---
tab_health, tab_biz, tab_log = st.tabs(["🚦 시스템 상태 (Health)", "📊 비즈니스 데이터 분석", "📜 엔드-투-엔드 로그"])

# [Tab 1] 시스템 상태 영역 (EARS core)
with tab_health:
    st.header("실시간 인프라 건강도")
    
    # 1. KPI Metrics
    health_metrics = data_service.get_system_health_metrics()
    col1, col2, col3 = st.columns(3)
    col1.metric("최근 1시간 에러 발생 (건)", int(health_metrics['total_errors']), delta=-2 if health_metrics['total_errors'] > 0 else 0)
    col2.metric("고유 에러 타입", int(health_metrics['unique_error_types']))
    col3.metric("Critical 발생", int(health_metrics['critical_errors']), delta_color="inverse")

    st.divider()

    # 2. Charts
    col_h1, col_h2 = st.columns([1, 2])
    with col_h1:
        st.write("### 🚨 에러 코드별 분포")
        err_dist = data_service.get_error_distribution_by_code()
        if not err_dist.empty:
            fig_err = px.pie(err_dist, values='count', names='error_code', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Reds_r)
            st.plotly_chart(fig_err, use_container_width=True)
            
    with col_h2:
        st.write("### 📉 상세 에러 패턴 분석 (Summary)")
        # 요약 테이블을 활용한 시계열 분석 등 추가 가능
        st.dataframe(err_dist, use_container_width=True)

# [Tab 2] 비즈니스 데이터 분석 영역 (KPI)
with tab_biz:
    st.header(f"비즈니스 인사이트 ({selected_cat})")
    
    # 1. Business Metrics
    biz_metrics = data_service.get_kpi_metrics(selected_cat)
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.metric("총 조회수", f"{int(biz_metrics['views']):,}")
    b_col2.metric("총 구매수", f"{int(biz_metrics['purchases']):,}")
    b_col3.metric("유니크 방문자", f"{int(biz_metrics['users']):,}")
    
    cvr = (biz_metrics['purchases'] / biz_metrics['views'] * 100) if biz_metrics['views'] > 0 else 0
    b_col4.metric("구매 전환율 (CVR)", f"{cvr:.2f}%")

    st.divider()
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.write("### 🏆 인기 상품 TOP 10")
        popular_df = data_service.get_popular_products(selected_cat)
        if not popular_df.empty:
            fig_pop = px.bar(popular_df, x='count', y='name', orientation='h',
                             labels={'count': '구매 횟수', 'name': '상품명'},
                             color='count', color_continuous_scale='Viridis')
            st.plotly_chart(fig_pop, use_container_width=True)
            
    with col_b2:
        st.write("### 🔍 인기 검색 키워드 TOP 10")
        keywords_df = data_service.get_popular_search_keywords(selected_cat)
        if not keywords_df.empty:
            st.table(keywords_df)

    st.divider()

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.write("### 🥧 카테고리별 성과 비교 (전체)")
        cat_perf_df = data_service.get_category_performance()
        if not cat_perf_df.empty:
            fig_cat = px.bar(cat_perf_df, x='category', y=['views', 'purchases'], 
                             barmode='group', title="카테고리별 조회 vs 구매")
            st.plotly_chart(fig_cat, use_container_width=True)
            
    with col_c2:
        st.write("### 📈 시간대별 사용자 활동량 (24시간)")
        hourly_df = data_service.get_hourly_activity()
        if not hourly_df.empty:
            fig_hour = px.line(hourly_df, x='hour', y='count', 
                               labels={'count': '활동량', 'hour': '시간'})
            st.plotly_chart(fig_hour, use_container_width=True)

# [Tab 3] 상세 로그 조회 영역 (Trace ID 포함)
with tab_log:
    st.header("📜 엔드-투-엔드 이벤트 로그")
    if st.checkbox("최근 50개 로그 보기"):
        logs = data_service.get_recent_event_logs(50)
        st.dataframe(logs, use_container_width=True)

if st.button("데이터 강제 새로고침"):
    st.rerun()
