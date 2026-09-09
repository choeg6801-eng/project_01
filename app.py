import os
import platform
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ------------------------------------------------
# 1. 기본 설정 및 폰트 설정
# ------------------------------------------------
st.set_page_config(
    page_title='무역 분석 대시보드', page_icon='📊', layout='wide'
)

# 운영체제별 한글 폰트 설정 (글씨 깨짐 방지)
env_os = platform.system()
if env_os == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif env_os == 'Darwin':  # Mac
    plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (Streamlit Cloud 등)
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

# ------------------------------------------------
# 2. 데이터 로드 및 전처리
# ------------------------------------------------
@st.cache_data
def load_data():
    # 파일 로드 (제공된 파일명에 정확히 맞춤)
    if not os.path.exists('baci_85_sample.csv'):
        st.error("'baci_85_sample.csv' 파일이 없습니다.")
        st.stop()
    if not os.path.exists('country_codes_sample (1).csv'):
        st.error("'country_codes_sample (1).csv' 파일이 없습니다.")
        st.stop()

    baci_df = pd.read_csv('baci_85_sample.csv')
    country_df = pd.read_csv('country_codes_sample (1).csv')

    # 'j' 컬럼(상대 국가 코드) 기준으로 국가 이름 병합
    df = pd.merge(baci_df, country_df, on='j', how='left')
    df['country_name'] = df['country_name'].fillna('Unknown')

    # 무역액(v) 기준 등급 생성 (대, 중, 소)
    if 'v' in df.columns:
        # 3분위수로 나누어 등급 할당
        df['trade_grade'] = pd.qcut(df['v'], q=3, labels=['소', '중', '대'], duplicates='drop')
    
    return df

df = load_data()
# baci_85_sample.csv 원본 결측치 계산 (병합 전 원본 기준)
original_null_data = pd.read_csv('baci_85_sample.csv').isnull().sum().reset_index()
original_null_data.columns = ['컬럼명', '결측치 수']

# ------------------------------------------------
# 3. 사이드바 필터 구성
# ------------------------------------------------
st.sidebar.header('🔍 필터 옵션')

# 국가 선택
countries = df['country_name'].unique().tolist()
selected_countries = st.sidebar.multiselect(
    '국가 선택 (비워두면 전체)',
    options=countries,
    default=countries
)

# 무역액 등급 선택
grades = ['대', '중', '소']
selected_grades = st.sidebar.multiselect(
    '무역액 등급 선택',
    options=grades,
    default=grades
)

# 필터링 적용
filtered_df = df.copy()
if selected_countries:
    filtered_df = filtered_df[filtered_df['country_name'].isin(selected_countries)]
if selected_grades:
    filtered_df = filtered_df[filtered_df['trade_grade'].isin(selected_grades)]

# ------------------------------------------------
# 4. 오른쪽 메인 화면 구성
# ------------------------------------------------
st.title('📈 무역 분석 대시보드')
st.markdown('---')

# [요구사항 2] baci_85_sample.csv 파일의 결측치
st.subheader('1. 데이터 결측치 현황 (baci_85_sample.csv 원본)')
st.dataframe(original_null_data.T, use_container_width=True)

st.markdown('---')

# [요구사항 3] 총 거래건수 및 총 수출액(달러)
st.subheader('2. 전체 무역 요약 지표')
col1, col2 = st.columns(2)
with col1:
    st.metric(label='총 거래 건수', value=f'{len(filtered_df):,} 건')
with col2:
    total_export = filtered_df['v'].sum() if 'v' in filtered_df.columns else 0
    st.metric(label='총 수출액 (달러)', value=f'${total_export:,.2f}')

st.markdown('---')

# [요구사항 4] 국가*연도 수출액 히트맵 & 무역액 등급분포 (두 열로 분리)
st.subheader('3. 국가별 연도별 수출액 히트맵 및 무역액 등급 분포')
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('**상위 8개국 국가*연도 수출액 히트맵**')
    if not filtered_df.empty:
        # 수출액(v) 기준 상위 8개 국가 선정
        top_8_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(8).index
        heatmap_data = filtered_df[filtered_df['country_name'].isin(top_8_countries)].pivot_table(
            index='country_name', columns='t', values='v', aggfunc='sum', fill_value=0
        )
        
        if not heatmap_data.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(heatmap_data, cmap='Blues', annot=True, fmt=',.0f', ax=ax)
            ax.set_ylabel('국가')
            ax.set_xlabel('연도(t)')
            st.pyplot(fig)
        else:
            st.info('조건에 맞는 데이터가 부족합니다.')

with col_b:
    st.markdown('**무역액 등급 분포**')
    if not filtered_df.empty:
        grade_counts = filtered_df['trade_grade'].value_counts().reindex(['대', '중', '소'])
        fig, ax = plt.subplots(figsize=(8, 5))
        grade_counts.plot(kind='bar', color=['#ff9999', '#66b3ff', '#99ff99'], ax=ax)
        ax.set_xlabel('무역액 등급')
        ax.set_ylabel('건수')
        plt.xticks(rotation=0)
        st.pyplot(fig)

st.markdown('---')

# [요구사항 5] 상위 5개국 * 무역액 등급 교차표 (원본건수 / 정규화비율)
st.subheader('4. 상위 5개국 및 무역액 등급 교차표')
if not filtered_df.empty:
    top_5_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(5).index
    cross_df = filtered_df[filtered_df['country_name'].isin(top_5_countries)]
    
    if not cross_df.empty:
        # 원본 건수 교차표
        cross_count = pd.crosstab(cross_df['country_name'], cross_df['trade_grade'])
        # 정규화 비율 교차표
        cross_norm = pd.crosstab(cross_df['country_name'], cross_df['trade_grade'], normalize='index')
        
        st.markdown('##### 📌 원본 건수 교차표')
        st.dataframe(cross_count, use_container_width=True)
        
        st.markdown('##### 📌 정규화 비율 교차표 (행 기준)')
        st.dataframe(cross_norm.style.format('{:.2%}'), use_container_width=True)