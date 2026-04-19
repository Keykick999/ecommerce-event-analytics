import uuid
import re

# [Trace ID Management]
def generate_trace_id():
    """요청 단위의 추적성을 보장하기 위한 고유 ID를 생성합니다."""
    return str(uuid.uuid4())

# [PII Deep Sanitizer]
def mask_pii(data):
    """
    재귀적으로 데이터 구조를 탐색하여 개인정보(비밀번호, 토큰 등)를 마스킹합니다.
    데이터 내의 중첩된 JSON 구조까지 모두 탐색하여 보안을 확보합니다.
    """
    sensitive_patterns = [
        r'password', r'token', r'secret', r'card_number', r'ssn', r'email'
    ]
    
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if any(re.search(pattern, k, re.IGNORECASE) for pattern in sensitive_patterns):
                new_dict[k] = "********"
            else:
                new_dict[k] = mask_pii(v)
        return new_dict
    elif isinstance(data, list):
        return [mask_pii(item) for item in data]
    else:
        return data

# [Severity Multi-factor Classification]
def classify_severity(api_path, error_code):
    """
    API 경로와 에러 코드의 조합으로 장애의 심각도를 분류합니다.
    - 결제(/api/payment) 관련 에러는 무조건 CRITICAL
    - 5xx 서버 에러는 HIGH
    - 4xx 클라이언트 에러는 MEDIUM
    """
    # 1. 경로 기반 분석
    if api_path and "/api/payment" in api_path:
        return "CRITICAL"
    
    # 2. 에러 코드 기반 분석 (문자열인 경우 숫자로 변환 시도)
    try:
        code = int(error_code) if error_code else 0
        if code >= 500:
            return "HIGH"
        elif code >= 400:
            return "MEDIUM"
    except (ValueError, TypeError):
        # 코드가 숫자가 아닌 경우 (예: 'DB_CONN_ERROR')
        if "ERROR" in str(error_code).upper():
            return "HIGH"
            
    return "LOW"
