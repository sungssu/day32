# day32_ex.py
# 텍스트 분석 기록 앱 UI : 입력 -> 처리 -> 저장 -> 이력 -> 통계

# 경로 : cd D:\aihuman9\work_space\python\webservice\day32\
# python -m streamlit run day32_ex.py

import uuid # 유일한 식별값 생성 라이브러리

import psycopg
import streamlit as st

from day32_logic import analyze_text
from day32_db import save_run, list_runs, get_run, summary, delete_run
from util.print_util import pp, up

# 결과 표시 함수
def show_result(result):
    left, right = st.columns(2)
    left.metric('공백 제외 글자 수', result['char_count'])
    right.metric('공백 기준 단어 수', result['word_count'])
    st.write('상위 토큰: ', result['top_tokens'])

def main():

    st.set_page_config(
        page_title='텍스트 분석 기록',
        layout='wide'
    )
    st.title('텍스트 분석과 클라우드 기록')

    # session_state에 request_key가 없다면
    if 'request_key' not in st.session_state: # 요청 식별키
        # uuid 라이브러리를 활용해서 uuid 생성해 저장
        st.session_state['request_key'] = str(uuid.uuid4())
    if 'result' not in st.session_state: # 분석결과
        st.session_state['result'] = None
    if 'saved' not in st.session_state: # 저장여부
        st.session_state['saved'] = False

    analysis, history = st.tabs(['분석과 저장', '이력과 통계'])

    with analysis:
        with st.form('analyze'):
            text = st.text_area('분석할 문장', max_chars=5000)
            submitted = st.form_submit_button('분석 실행')
        if submitted:
            try:
                result = analyze_text(text)
                st.session_state['result'] = result
                st.session_state['request_key'] = str(uuid.uuid4())
                st.session_state['saved'] = False
            except ValueError as e:
                st.warning(str(e))
        result = st.session_state['result']

        if result is not None:
            st.text(result['text'])
            show_result(result)
            title = st.text_input('기록 제목', max_chars=80)
            if st.button('결과 저장', disabled=st.session_state['saved']):
                try:
                    rid = save_run(
                        title, result, st.session_state['request_key']
                    )
                    st.session_state['saved'] = True
                    st.success('이미 저장한 결과입니다.' if rid is None else f'기록 {rid} 저장 완료')
                    pp('분석 저장 완료')
                except ValueError as ve:
                    st.warning(str(ve))
                except psycopg.Error as pe:
                    pp('저장 오류: ', type(pe).__name__)
                    st.error('저장 실패. 연결/권한/테이블을 확인하고 재시도하세요.')
                except OSError as oe:
                    st.error('sql폴더를 확인하세요.')
    with history:
        try:
            stats = summary()
            a, b, c = st.columns(3)
            a.metric('전체 저장 건수', stats['total'])
            b.metric('누적 글자 수', stats['total_chars'])
            c.metric('평균 단어 수', str(stats['average_word']))

            keyword = st.text_input('기록 제목 검색', max_chars=80)

            st.button('이력 새로고침')

            rows = list_runs()
            st.caption('목록은 최신 100건, 위 통계는 전체 저장 데이터 기준입니다.')
            st.dataframe(rows,  hide_index=True, use_container_width=True)

            if rows:
                rid = st.selectbox('상세 기록 ID', [x['id'] for x in rows])
                record = get_run(rid)
                if record:
                    st.subheader(record['title'])
                    st.text(record['source_text'])
                    show_result(record)
                    st.caption(f'처리 버전: {record["analysis_version"]}')
                    confirm = st.checkbox('선택한 기록 삭제 확인')
                    if st.button('기록 삭제', disabled=not confirm):
                        if delete_run(rid):
                            st.rerun()
                        else:
                            st.warning('이미 삭제된 기록입니다.')
                else:
                    st.info('기록이 사라졌습니다. 새로고침하세요.')
            else:
                st.info('저장된 기록 또는 검색 결과가 없습니다.')

        except ValueError as ve:
            st.warning(str(ve))
        except psycopg.Error as pe:
            pp('조회 오류: ', type(pe).__name__)
            st.error('이력 조회 실패. DB 연결과 text_runs 테이블을 확인하세요.')
        except OSError as oe:
            st.error('sql폴더를 확인하세요.')

if __name__ == '__main__':
    main()

up(5)