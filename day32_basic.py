# day32_basic.py

# 배송비 견적 기록

# 파일: day32_basic.py
# 준비: sql/schema_tasks.sql 적용, DATABASE_URL 설정
#
# 1) 견적 제목(1~80자)과 무게(1~20000g 정수)를 입력받으세요.
# 2) 1000g 이하 3000원, 초과하면 시작된 1000g 구간마다 1000원 추가.
# 3) 계산 함수는 UI·DB를 참조하지 않도록 작성하세요.
# 4) 계산 결과와 무게·제목·shipping-v1 버전을 shipping_quotes에 저장하세요.
# 5) 저장 성공 후 요금과 ID를 표시하고 최신 100건 목록을 표시하세요.
# 6) 공백 제목과 DB 연결 실패를 안내하세요.

# 검증: 1g=3000, 1000g=3000, 1001g=4000, 2000g=4000, 2001g=5000.
# 앱 재시작 후 저장된 견적이 유지되는지 확인하세요.
# 제출: 전체 코드, 공개 URL, 계산값과 DB 값 비교.
# 평가: 계산 30, 저장 30, 목록 20, 검증·배포 20.
# 풀이: day32_basic_sol.py. 제출 UI는 '계산하고 저장' 방식입니다.
# 각 제출은 새 견적입니다. 이 과제에는 요청 키 중복 방지가 필수는 아닙니다.
#
# CREATE TABLE IF NOT EXISTS shipping_quotes (
#  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
#  label VARCHAR(80) NOT NULL,
#  weight INTEGER NOT NULL CHECK (weight > 0),
#  fee INTEGER NOT NULL CHECK (fee >= 0),
#  rule_version VARCHAR(20) NOT NULL
# );

import re
from collections import Counter

import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb # JSON데이터 처리
from util.print_util import pp, up
from dotenv import load_dotenv
import streamlit as st

import uuid # 유일한 식별값 생성 라이브러리


# logic
shipping_quotes = 'shipping-v1' # 결과를 만든 처리 규칙 버전

def analyze_weight(text):
    label = text.strip()
    if not label or len(label) > 80:
        raise ValueError('견적 제목을 1~80자로 입력하세요.')
    weight = text.strip()
    if not weight or len(weight) > 20000:
        raise ValueError('무게를 1~20000g로 입력하세요.')
    fee = 3000 + ((weight - 1) // 1000) * 1000

    return{
        'label': label,
        'weight': weight,
        'fee': fee,
        'rule_version': shipping_quotes,
    }

# DB

# local 실행을 위한 .env
load_dotenv()

# sql 파일경로
SQL_DIR = Path(__file__).resolve().parent / "sql"

# SQL 실행 함수
def execute(name, params=()):
    # 환경변수에서 데이터베이스URL 획득
    url = os.getenv("DATABASE_URL", '').strip()
    if not url:
        raise ValueError('DATABASE_URL 환경변수를 설정하세요.')
    # sql 파일의 문자열 획득
    sql = (SQL_DIR / name).read_text(encoding='utf-8')
    with psycopg.connect(
        url, # 접속 URL
        connect_timeout=15, # 접속까지 15초는 대기
        row_factory=dict_row # 행을 딕셔너리로
    ) as conn:
        # sql 실행후 결과를 리스트러 변환
        return conn.execute(sql, params).fetchall()

# 저장
def save_run(result, request_key):
    rows = execute('basic_save.sql', (
        result['text'],
        result['weight'],
        result['fee'],
        request_key
    ))
    return rows[0]['id']

# 조회
def get_run(record_id):
    rows = execute('basic_detail.sql', (record_id,))
    # 조회된 행이 있으면 반환, 그렇지 않으면 None 반환
    return rows[0] if rows else None

# UI
# 결과 표시 함수
def show_result(result):
    left, right = st.columns(2)
    left.metric('무게(g)', f"{result['weight']:,}g")
    right.metric('산정 배송비', f"{result['fee']:,}원")

def main():

    st.set_page_config(
        page_title='배송비 견적 기록',
        layout='wide'
    )
    st.title('무게에 따른 배송비 견적')

    # session_state에 request_key가 없다면
    if 'request_key' not in st.session_state: # 요청 식별키
        # uuid 라이브러리를 활용해서 uuid 생성해 저장
        st.session_state['request_key'] = str(uuid.uuid4())
    if 'result' not in st.session_state: # 분석결과
        st.session_state['result'] = None
    if 'saved' not in st.session_state: # 저장여부
        st.session_state['saved'] = False

    # 탭 구성: [견적 산출과 저장, 기록 조회]
    analysis, lookup = st.tabs(['견적 산출과 저장', '기록 조회'])

    with analysis:
        with st.form('quote_form'):
            label_input = st.text_input('견적 제목 (Label)', max_chars=80)
            weight_input = st.text_input('무게 (g)', placeholder='예: 1500')
            submitted = st.form_submit_button('견적 계산 및 실행')

        if submitted:
            try:
                result = analyze_weight(label_input, weight_input)
                st.session_state['result'] = result
                st.session_state['request_key'] = str(uuid.uuid4())
                st.session_state['saved'] = False
            except ValueError as e:
                st.warning(str(e))

        result = st.session_state['result']
        if result is not None:
            st.subheader(f"견적명: {result['label']}")
            show_result(result)

            if st.button('견적 결과 저장', disabled=st.session_state['saved']):
                try:
                    rid = save_run(result, st.session_state['request_key'])
                    st.session_state['saved'] = True
                    if rid is None:
                        st.warning('이미 저장된 견적 결과입니다.')
                    else:
                        st.success(f'배송비 견적 기록 {rid} 저장 완료')
                        pp('견적 저장 완료')
                except ValueError as ve:
                    st.warning(str(ve))
                except psycopg.Error as pe:
                    pp('저장 오류: ', type(pe).__name__)
                    st.error(f'저장 실패. DB 연결 및 테이블을 확인하세요: {pe}')
                except OSError as oe:
                    st.error('sql 폴더 경로를 확인하세요.')

    with lookup:
        st.subheader('저장된 견적 조회')
        record_id_input = st.number_input('조회할 기록 ID 입력', min_value=1, step=1)
        if st.button('기록 조회 실행'):
            try:
                record = get_run(record_id_input)
                if record:
                    st.success(f"기록 ID {record['id']} 조회 성공")
                    st.subheader(record['label'])
                    show_result(record)
                    st.caption(f'규칙 버전: {record["rule_version"]}')
                else:
                    st.info('해당 ID의 기록이 존재하지 않습니다.')
            except Exception as e:
                st.error(f'조회 중 오류 발생: {e}')


if __name__ == '__main__':
    main()

up(5)















