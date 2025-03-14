import pathlib
import time

def create_temp_dir():
    """임시 디렉토리 생성"""
    temp_dir = pathlib.Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def get_pdf_name(pdf_path):
    """PDF 파일 이름 추출"""
    return pathlib.Path(pdf_path).stem

def wait_with_backoff(retry_count, base_wait_time=3):
    """지수 백오프를 사용한 대기"""
    wait_time = base_wait_time * (2 ** retry_count)
    time.sleep(wait_time)
