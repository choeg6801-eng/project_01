import os
import base64
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# ------------------------------------------------
# 1. 기본 설정 및 배포 환경을 고려한 폰트 강제 적용
# ------------------------------------------------
st.set_page_config(
    page_title='무역 분석 대시보드', page_icon='📊', layout='wide'
)

current_dir = os.path.dirname(os.path.abspath(__file__))

# --- 배경 이미지 설정 함수 ---
def set_background(image_file):
    image_path = os.path.join(current_dir, image_file)
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        
        # linear-gradient를 사용해 이미지 위에 50% 투명도(rgba의 0.5)의 흰색 레이어를 덮어씌움
        # 이렇게 해야 글자나 차트가 투명해지는 것을 막고 배경만 흐릿해집니다.
        css = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)), url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ 배경 이미지 파일을 찾을 수 없습니다: {image_file}")

# 배경 이미지 적용 (파일명을 container.jpg로 맞췄다고 가정)
set_background('container.jpg')

# --- 폰트 설정 ---
FONT_PATH = os.path.join(current_dir, 'Griun_Fromsol-Rg.ttf')

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    font_prop = fm.FontProperties(fname=FONT_PATH)
    font_name = font_prop.get_name()
    
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False
    
    sns.set_theme(style="whitegrid", rc={"font.family": font_name, "axes.unicode_minus": False})
    plt.rc('font', family=font_name) 
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

    df = pd.merge(baci_df, country_df, on='j', how='left')
    df['country_name'] = df['country_name'].fillna('Unknown')

    if 'v' in df.columns:
        df['trade_grade'] = pd.qcut(df['v'], q=3, labels=['소', '중', '대'], duplicates='drop')
    
    return df

df = load_data()

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

filtered_df = df.copy()
if selected_countries:
    filtered_df = filtered_df[filtered_df['country_name'].isin(selected_countries)]
if selected_grades:
    filtered_df = filtered_df[filtered_df['trade_grade'].isin(selected_grades)]

# ------------------------------------------------
# 4. 오른쪽 메인 화면 구성
# ------------------------------------------------
pochacco_path = os.path.join(current_dir, 'pochacco.png') # 확장자가 jpg라면 'pochacco.jpg'로 변경

if os.path.exists(pochacco_path):
    with open(pochacco_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    # 1. 텍스트를 먼저 배치하고, 이미지를 뒤로 보냄
    # 2. width를 100으로 키움 (원하는 크기로 조절 가능)
    # 3. margin-left를 주어 텍스트와 이미지 사이 간격 확보
    title_html = f"""
    <h1 style="display: flex; align-items: center; margin-bottom: 0;">
        무역 분석 대시보드
        <img src="data:image/png;base64,{img_base64}" width="100" style="margin-left: 20px; border-radius: 10px;">
    </h1>
    """
    st.markdown(title_html, unsafe_allow_html=True)
else:
    st.title('무역 분석 대시보드 🐶')


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
        
        plt.xticks(rotation=0)
        
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