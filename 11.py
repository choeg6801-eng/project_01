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

# --- 배경, 짱구 GIF, 포차코 설정 CSS ---
def apply_custom_ui():
    # 지구본 이미지 URL (투명 배경 PNG)
    globe_url = "https://cdn.pixabay.com/photo/2013/07/12/13/27/earth-147053_1280.png"
    # 짱구 걷는 GIF URL (배경 투명)
    shinchan_gif_url = "https://media.tenor.com/P1yX_9V_TbwAAAAi/shin-chan-shinchan.gif"
    
    custom_css = f"""
    <style>
    /* 1. 배경 설정: 하늘색 배경 + 50% 투명도의 지구본을 우측 하단에 고정 */
    .stApp {{
        background-color: #E0F7FA; /* 아주 연한 하늘색 */
        background-image: url("{globe_url}");
        background-size: 800px; /* 지구본 크기 */
        background-position: right -100px bottom -100px; /* 우측 하단 구석에 배치 */
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* 지구본에 50% 투명도를 주기 위한 가상 요소(overlay) 기법 */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: #E0F7FA;
        opacity: 0.5; /* 50% 불투명한 하늘색을 덧씌워서 배경 이미지를 투명하게 만듦 */
        z-index: -1;
    }}

    /* 2. 걸어다니는 짱구 애니메이션 설정 */
    .walking-shinchan {{
        position: fixed;
        bottom: 10px; /* 화면 가장 밑에 배치 */
        left: -150px; /* 왼쪽 화면 밖에서 시작 */
        width: 120px; /* 짱구 크기 */
        z-index: 9999;
        animation: walk-across 15s linear infinite; /* 15초 동안 일정한 속도로 무한 반복 */
    }}

    /* 짱구가 왼쪽에서 오른쪽으로 걸어가는 키프레임 */
    @keyframes walk-across {{
        0% {{
            left: -150px;
        }}
        100% {{
            left: 110%; /* 화면 오른쪽 밖으로 완전히 나감 */
        }}
    }}
    </style>
    
    <!-- 짱구 이미지를 화면에 주입 -->
    <img src="{shinchan_gif_url}" class="walking-shinchan" alt="Walking Shinchan">
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# UI 적용 함수 실행
apply_custom_ui()

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
pochacco_path = os.path.join(current_dir, 'pochacco.png')

if os.path.exists(pochacco_path):
    with open(pochacco_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    # 텍스트 오른쪽에 포차코 이미지 배치
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