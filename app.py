import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ------------------------------------------------
# 1. 기본 설정 및 폰트 객체 준비 (배포 환경 100% 호환)
# ------------------------------------------------
st.set_page_config(
    page_title='무역 분석 대시보드', page_icon='📊', layout='wide'
)

# 현재 스크립트(app.py) 경로 기준으로 폰트 파일 찾기
current_dir = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(current_dir, 'Griun_Fromsol-Rg.ttf')

# 전역 설정 및 폰트 프로퍼티 객체(font_prop) 생성
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    font_prop = fm.FontProperties(fname=FONT_PATH) # 이 객체를 차트 그릴 때 강제 주입합니다.
    font_name = font_prop.get_name()
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.error(f"❌ 폰트 파일을 찾을 수 없습니다.\n경로: {FONT_PATH}")
    st.stop()


# ------------------------------------------------
# 2. 데이터 로드 및 전처리
# ------------------------------------------------
@st.cache_data
def load_data():
    if not os.path.exists('baci_85_sample.csv'):
        st.error("'baci_85_sample.csv' 파일이 없습니다.")
        st.stop()
    if not os.path.exists('country_codes_sample (1).csv'):
        st.error("'country_codes_sample (1).csv' 파일이 없습니다.")
        st.stop()

    baci_df = pd.read_csv('baci_85_sample.csv')
    country_df = pd.read_csv('country_codes_sample (1).csv')

    # 'j' 컬럼(국가 코드) 기준으로 국가 이름 병합
    df = pd.merge(baci_df, country_df, on='j', how='left')
    df['country_name'] = df['country_name'].fillna('Unknown')

    # 무역액(v) 기준 등급 생성 (대, 중, 소)
    if 'v' in df.columns:
        df['trade_grade'] = pd.qcut(df['v'], q=3, labels=['소', '중', '대'], duplicates='drop')
    
    return df

df = load_data()

# baci_85_sample.csv 원본 결측치 계산
original_null_data = pd.read_csv('baci_85_sample.csv').isnull().sum().reset_index()
original_null_data.columns = ['컬럼명', '결측치 수']

# ------------------------------------------------
# 3. 사이드바 필터 구성
# ------------------------------------------------
st.sidebar.header('🔍 필터 옵션')

countries = df['country_name'].unique().tolist()
selected_countries = st.sidebar.multiselect(
    '국가 선택 (비워두면 전체)',
    options=countries,
    default=countries
)

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

st.subheader('1. 데이터 결측치 현황')
st.dataframe(original_null_data.T, use_container_width=True)

st.markdown('---')

st.subheader('2. 전체 무역 요약 지표')
col1, col2 = st.columns(2)
with col1:
    st.metric(label='총 거래 건수', value=f'{len(filtered_df):,} 건')
with col2:
    total_export = filtered_df['v'].sum() if 'v' in filtered_df.columns else 0
    st.metric(label='총 수출액 (달러)', value=f'${total_export:,.2f}')

st.markdown('---')

st.subheader('3. 국가별 연도별 수출액 히트맵 및 무역액 등급 분포')
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('**상위 8개국 국가*연도 수출액 히트맵**')
    if not filtered_df.empty:
        top_8_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(8).index
        heatmap_data = filtered_df[filtered_df['country_name'].isin(top_8_countries)].pivot_table(
            index='country_name', columns='t', values='v', aggfunc='sum', fill_value=0
        )
        
        if not heatmap_data.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(heatmap_data, cmap='Blues', annot=True, fmt=',.0f', ax=ax)
            
            # [핵심] 차트의 모든 글씨에 폰트 객체(font_prop)를 직접 강제 적용
            ax.set_title('상위 8개국 연도별 수출액', fontproperties=font_prop, pad=15)
            ax.set_ylabel('국가명', fontproperties=font_prop)
            ax.set_xlabel('연도(t)', fontproperties=font_prop)
            
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(font_prop)
                
            st.pyplot(fig)
        else:
            st.info('조건에 맞는 데이터가 부족합니다.')

with col_b:
    st.markdown('**무역액 등급 분포**')
    if not filtered_df.empty:
        grade_counts = filtered_df['trade_grade'].value_counts().reindex(['대', '중', '소'])
        fig, ax = plt.subplots(figsize=(8, 5))
        grade_counts.plot(kind='bar', color=['#ff9999', '#66b3ff', '#99ff99'], ax=ax)
        
        # 글씨 회전을 먼저 적용
        plt.xticks(rotation=0)
        
        # [핵심] 차트의 모든 글씨에 폰트 객체(font_prop)를 직접 강제 적용
        ax.set_title('무역액 등급별 분포', fontproperties=font_prop, pad=15)
        ax.set_xlabel('무역액 등급', fontproperties=font_prop)
        ax.set_ylabel('건수', fontproperties=font_prop)
        
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
            
        st.pyplot(fig)

st.markdown('---')

st.subheader('4. 상위 5개국 및 무역액 등급 교차표')
if not filtered_df.empty:
    top_5_countries = filtered_df.groupby('country_name')['v'].sum().nlargest(5).index
    cross_df = filtered_df[filtered_df['country_name'].isin(top_5_countries)]
    
    if not cross_df.empty:
        cross_count = pd.crosstab(cross_df['country_name'], cross_df['trade_grade'])
        cross_norm = pd.crosstab(cross_df['country_name'], cross_df['trade_grade'], normalize='index')
        
        st.markdown('##### 📌 원본 건수 교차표')
        st.dataframe(cross_count, use_container_width=True)
        
        st.markdown('##### 📌 정규화 비율 교차표 (행 기준)')
        st.dataframe(cross_norm.style.format('{:.2%}'), use_container_width=True)