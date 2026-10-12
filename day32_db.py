# day32_db.py
# Neon PostgreSQL에 입력과 처리 결과를 함께 저장하는 함수


import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb # JSON데이터 처리
from util.print_util import pp, up
from dotenv import load_dotenv

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
# title : 기록제목, result:JSON 문자열, request_key: 요청키
def save_run(title, result, request_key):
    title = title.strip()
    if not title or len(title) > 80:
        raise ValueError('기록 제목은 1~80자로 입력하세요.')
    rows = execute('save.sql', (
        title,
        result['text'],
        result['char_count'],
        result['word_count'],
        # 키에 해당하는 문자열을 PostgreSQL에 저장할 Jsonb 타입으로 변환
        Jsonb(result['top_tokens']),
        result['version'],
        request_key
    ))
    return rows[0]['id']

# 리스트
def list_runs(keyword=''):
    return execute('list.sql', (f'%{keyword.strip()}%',))

# 조회
def get_run(record_id):
    rows = execute('detail.sql', (record_id,))
    # 조회된 행이 있으면 반환, 그렇지 않으면 None 반환
    return rows[0] if rows else None

# 요약
def summary():
    return execute('summary.sql')[0]

# 삭제
def delete_run(record_id):
    return bool(execute('delete.sql', (record_id,))) # 삭제 여부 반환
