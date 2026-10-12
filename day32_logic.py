# day32_logic.py
# 텍스트 분석 규칙 로직

import re
from collections import Counter

ANALYSIS_VERSION = 'rule-v1' # 결과를 만든 처리 규칙 버전

# 텍스트 분석 함수
def analyze_text(text):
    text = text.strip()
    if not text or len(text) > 5000:
        raise ValueError('분석 문장을 1~5000자로 입력하세요.')
    # 한글, 영문대문자, 영문소문자, 숫가 가 1개 이상 나오는 패턴에 해당하는 문자열들의 리스트
    tokens = re.findall(r'[가-힣A-Za-z0-9]+', text.lower())
    # 전체 문자열, 문자 수, 빈도 수 상위 5개 토큰 리스트, 버전 반환
    return {
        'text': text,
        'char_count': len(re.sub(r'\s', '', text)), # 공백문자 제거한 문자열 길이
        'word_count': len(text.split()), # 공백 기준으로 분리한 단어 수
        'top_tokens': Counter(tokens).most_common(5), # (토큰, 빈도 수) 리스트
        'version': ANALYSIS_VERSION,
    }