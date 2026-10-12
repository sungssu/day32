# day32_application.py
# 주제: 월간 예산 계획
#
# 파일: day32_application.py
# 준비: sql/schema_tasks.sql 적용, DATABASE_URL 설정
#
# 1) 계획 제목(1~80자)과 수입·지출(0~100000000원 정수)을 입력받으세요.
# 2) 예상 잔액=수입-지출. 음수 잔액도 정상 결과로 표시하세요.
# 3) 계산 미리보기와 DB 저장을 별도 버튼으로 구현하세요.
# 4) 미리보기 결과와 UUID 요청 키를 session_state에 보관하세요.
# 5) 동일 키 재시도에는 한 행만 저장하도록 UNIQUE와 충돌 처리를 사용하세요.
# 6) 제목 검색 목록과 ID별 상세를 구성하세요.
# 7) 전체 계획 건수와 전체 잔액 합계는 DB 집계로 표시하세요.
# 8) DB 실패 시 미리보기와 요청 키를 유지하세요.

# 검증: 수입 100000, 지출 70000 → 잔액 30000.
# 수입 0, 지출 10000 → 잔액 -10000. 같은 키 재저장 → 건수 유지.
# 두 계획의 잔액 합계 20000. 검색해도 전체 통계는 변하지 않음.
# 앱 재시작 후 이력 유지, 다른 브라우저에서 같은 기록 확인.
#
#
# CREATE TABLE IF NOT EXISTS budget_plans (
#  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
#  title VARCHAR(80) NOT NULL,
#  income INTEGER NOT NULL CHECK (income >= 0),
#  expense INTEGER NOT NULL CHECK (expense >= 0),
#  balance INTEGER NOT NULL,
#  request_key UUID UNIQUE NOT NULL
# );

import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import streamlit as st
from util.print_util import pp, up
import uuid

def analyze_plan(title_text, income_text, expense_text):
    title = title_text.strip()
    if not title or len(title) > 80:
        raise ValueError('제목을 1~80자로 입력하세요.')

    try:
        income = int(income_text.strip())
    except ValueError:
        raise ValueError('수입을 올바른 숫자로 입력하세요.')

    if not (0 <= income <= 100000000):
        raise ValueError('0~100000000원 사이로 입력하세요.')

    try:
        expense = int(expense_text.strip())
    except ValueError:
        raise ValueError('지출을 올바른 숫자로 입력하세요.')

    if not (0 <= expense <= 100000000):
        raise ValueError('0~100000000원 사이 사이로 입력하세요.')

    balance = income - expense

    return {
        'title': title,
        'income': income,
        'expense': expense,
        'balance': balance
    }

# DB
load_dotenv()

# sql 파일경로
SQL_DIR = Path(__file__).resolve().parent / "sql"


# SQL 실행 함수
def execute(name, params=()):
    url = os.getenv("DATABASE_URL", '').strip()
    if not url:
        raise ValueError('DATABASE_URL 환경변수를 설정하세요.')
    sql = (SQL_DIR / name).read_text(encoding='utf-8')
    with psycopg.connect(
            url,
            connect_timeout=15,
            row_factory=dict_row
    ) as conn:
        return conn.execute(sql, params).fetchall()

# 저장함수
def save_run(result):
    rows = execute('application_save.sql', (
        result['title'],
        result['income'],
        result['expense'],
        result['balance']
    ))
    return rows[0]['id']

# 조회 함수
def get_run(record_id):
    rows = execute('application_detail.sql', (record_id,))
    return rows[0] if rows else None

# UI 결과 표시 함수
def show_result(result):
    left, right = st.columns(2)
    left.metric('수입', f"{result['income']:,}g")
    right.metric('지출', f"{result['expense']:,}원")

def main():
    st.set_page_config(
        page_title='월간 예산 계획',
        layout='wide'
    )
    st.title('월간 예산 계획')

    if 'request_key' not in st.session_state:
        st.session_state['request_key'] = str(uuid.uuid4())
    if 'result' not in st.session_state:
        st.session_state['result'] = None
    if 'saved' not in st.session_state:
        st.session_state['saved'] = False

    analysis, lookup = st.tabs(['수입과 지출', '기록 조회'])
    with analysis:
        with st.form('quote_form'):
            title_input = st.text_input('계획 제목', max_chars=50)
            income_input = st.text_input('수입(원)', placeholder='예: 1500')
            expense_input = st.text_input('지출(원)', placeholder='예: 1500')
            submitted = st.form_submit_button('미리보기')
            db_submitted = st.form_submit_button('DB저장')

        if db_submitted:
            try:
                # 1) 입력값 검증 및 계산 수행
                result = analyze_plan(title_input, income_input, expense_input)
                st.session_state['result'] = result
                st.session_state['request_key'] = str(uuid.uuid4())
                st.session_state['saved'] = False
            except ValueError as e:
                st.warning(str(e))

        result = st.session_state['result']
        if result is not None:
            st.subheader(f"계획명: {result['title']}")
            show_result(result)





if __name__ == '__main__':
    main()