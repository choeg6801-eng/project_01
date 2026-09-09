import os
import platform
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# 페이지 설정 (가장 먼저 호출되어야 함)
st.set_page_config(
    page_title='무역 분석 대시보드', page_icon='📊', layout='wide'
)

# 운영체제별 한글 폰트 설정 및 캐시 비우기
env_os = platform.system()
if env_os == 'Windows':
  plt.rcParams['font.family'] = 'Malgun Gothic'
elif env_os == 'Darwin':  # Mac
  plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (Streamlit Cloud 등)
  plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지


# 데이터 로드 함수
@st.cache_data
def load_data():
  if not os.path.exists('baci_85_sample.csv'):
    raise FileNotFoundError('baci_85_sample.csv 파일을 찾을 수 없습니다.')
  baci_df = pd.read_csv('baci_85_sample.csv')

  if os.path.exists('country_codes_sample.csv'):
    country_df = pd.read_csv('country_codes_sample.csv')
  else:
    country_df = pd.DataFrame(columns=['country_code', 'country_name'])

  return baci_df, country_df


try:
  baci, country_codes = load_data()
except FileNotFoundError as e:
  st.error(f'필요한 데이터 파일 오류: {e}')
  st.stop()

# 사이드바 설정
st.sidebar.header('🔍 필터 옵션')

# 국가 선택 (컬럼 'i'가 존재할 때)
if 'i' in baci.columns:
  unique_countries = baci['i'].unique()
  selected_countries = st.sidebar.multiselect(
      '국가 선택 (비워두면 전체)',
      options=unique_countries,
      default=unique_countries[: min(5, len(unique_countries))],
  )
  if selected_countries:
    baci = baci[baci['i'].isin(selected_countries)]

# 무역액 등급 선택 (대, 중, 소)
if 'v' in baci.columns:
  baci['trade_grade'] = pd.qcut(baci['v'], q=3, labels=['소', '중', '대'])
elif 'trade_grade' not in baci.columns:
  baci['trade_grade'] = '중'

grades = ['대', '중', '소']
selected_grades = st.sidebar.multiselect(
    '무역액 등급 선택', options=grades, default=grades
)
if selected_grades and 'trade_grade' in baci.columns:
  baci = baci[baci['trade_grade'].isin(selected_grades)]

# --- 오른쪽 화면 구성 ---
st.title('📈 무역 분석 대시보드')
st.markdown('---')

# 1. baci_85_sample.csv 파일의 결측치
st.subheader('1. 데이터 결측치 현황')
null_data = baci.isnull().sum().reset_index()
null_data.columns = ['컬럼명', '결측치 수']
st.dataframe(null_data.T, use_container_width=True)

st.markdown('---')

# 2. 총 거래건수 및 총 수출액(달러)
st.subheader('2. 전체 무역 요약 지표')
total_transactions = len(baci)
total_export = baci['v'].sum() if 'v' in baci.columns else 0

col1, col2 = st.columns(2)
with col1:
  st.metric(label='총 거래 건수', value=f'{total_transactions:,} 건')
with col2:
  st.metric(label='총 수출액 (달러)', value=f'${total_export:,.2f}')

st.markdown('---')

# 3. 국가*연도 수출액 히트맵(상위 8개국) & 무역액 등급분포 (두 열로 나누기)
st.subheader('3. 국가별 연도별 수출액 히트맵 및 무역액 등급 분포')
col_a, col_b = st.columns(2)

with col_a:
  st.markdown('**상위 8개국 국가*연도 수출액 히트맵**')
  if (
      'i' in baci.columns
      and 't' in baci.columns
      and 'v' in baci.columns
  ):
    top_8_countries = baci.groupby('i')['v'].sum().nlargest(8).index
    heatmap_data = baci[baci['i'].isin(top_8_countries)].pivot_table(
        index='i', columns='t', values='v', aggfunc='sum', fill_value=0
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(heatmap_data, cmap='Blues', annot=True, fmt=',.0f', ax=ax)
    ax.set_title('상위 8개국 연도별 수출액')
    ax.set_xlabel('연도 (t)')
    ax.set_ylabel('국가 코드 (i)')
    st.pyplot(fig)
  else:
    st.info('히트맵을 위한 필수 컬럼(i, t, v)이 부족합니다.')

with col_b:
  st.markdown('**무역액 등급 분포**')
  if 'trade_grade' in baci.columns:
    grade_counts = baci['trade_grade'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    grade_counts.plot(
        kind='bar', color=['#ff9999', '#66b3ff', '#99ff99'], ax=ax
    )
    ax.set_title('무역액 등급별 분포')
    ax.set_xlabel('무역액 등급')
    ax.set_ylabel('건수')
    st.pyplot(fig)
  else:
    st.info('등급 분포를 표시할 수 없습니다.')

st.markdown('---')

# 4. 상위 5개국 * 무역액 등급 교차표 (원본건수 / 정규화비율)
st.subheader('4. 상위 5개국 및 무역액 등급 교차표')
if 'i' in baci.columns and 'trade_grade' in baci.columns:
  top_5_countries = (
      baci.groupby('i')['v'].sum().nlargest(5).index
      if 'v' in baci.columns
      else baci['i'].value_counts().head(5).index
  )
  filtered_cross_df = baci[baci['i'].isin(top_5_countries)]

  cross_count = pd.crosstab(
      filtered_cross_df['i'], filtered_cross_df['trade_grade']
  )
  cross_norm = pd.crosstab(
      filtered_cross_df['i'], filtered_cross_df['trade_grade'], normalize='index'
  )

  st.markdown('##### 📌 원본 건수 교차표')
  st.dataframe(cross_count, use_container_width=True)

  st.markdown('##### 📌 정규화 비율 교차표 (행 기준)')
  st.dataframe(cross_norm.style.format('{:.2%}'), use_container_width=True)
else:
  st.info('교차표를 생성하기 위한 데이터 컬럼이 부족합니다.')