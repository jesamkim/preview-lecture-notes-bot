# 강의 자료 프리뷰 도구

이 도구는 대학원 강의 자료(PDF)를 AI 기술을 활용하여 자동으로 분석하고 이해하기 쉬운 형태로 재구성하는 Python 스크립트입니다.

## 주요 기능

- PDF 파일에서 텍스트와 이미지 자동 추출
- 이미지 내용 자동 분석 및 설명 생성
- 구조화된 마크다운 문서 생성
- 수식과 전문 용어에 대한 직관적인 설명 추가
- 개념 간의 연결성 강조

## 사전 준비사항

### 1. Python 환경
- Python 3.8 이상 설치 필요
- 가상 환경 사용 권장

### 2. AWS 설정

#### AWS CLI 설정
1. AWS CLI 설치
```bash
# macOS
brew install awscli

# Windows
choco install awscli
```

2. AWS 자격 증명 설정
```bash
aws configure
```
- AWS Access Key ID 입력
- AWS Secret Access Key 입력
- Default region: us-west-2
- Default output format: json

#### Amazon Bedrock 설정
1. AWS Console에서 Bedrock 서비스 접근 권한 확인
2. Claude 3.5 Sonnet v2 모델 사용 권한 확인
   - Model ID: us.anthropic.claude-3-5-sonnet-20241022-v2:0
   - 모델 버전: Claude 3.5 Sonnet v2 (2024년 10월 22일 버전)
   - API 사용량 및 제한 확인 (Quota)

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/jesamkim/preview-lecture-notes-bot.git
cd preview-lecture-notes-bot
```

2. 가상 환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

3. 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법
```bash
python preview.py your_lecture.pdf
```

### 생성되는 파일과 디렉토리
1. `temp/` 디렉토리
   - PDF에서 추출된 이미지 파일들이 임시 저장되는 위치
   - 실행 시마다 자동으로 생성됨

2. `{원본파일명}-1-init.md`
   - PDF에서 추출된 초기 텍스트와 이미지
   - 기본적인 마크다운 형식 적용

3. `{원본파일명}-2-enhanced.md`
   - 이미지 분석 결과가 추가된 버전
   - 각 이미지에 대한 상세 설명 포함

4. `{원본파일명}-3-completed.md`
   - 최종 구조화된 문서
   - 섹션별 명확한 구분
   - 핵심 개념 정리
   - 수식 설명
   - 실제 응용 사례
   - 개념 간 연결성 강조

### 출력 예시
```markdown
# 강의 주제

## 핵심 개념
- 개념 1: 설명 및 예시
- 개념 2: 설명 및 예시

## 수식 설명
y = ax + b의 의미:
- 수학적 의미: 일차 함수의 기본 형태
- 실제 적용: 선형 관계를 모델링하는 기초 수식
  예) 주행 거리(y)와 소요 시간(x)의 관계

## 이미지 분석
[이미지와 관련된 설명 및 해석]
```

## 주의사항

### API 호출 제한
- Amazon Bedrock API는 호출 횟수 제한이 있음
- 쓰로틀링 발생 시 자동으로 3초 대기 후 최대 3번 재시도
- 대규모 PDF 처리 시 시간 소요 예상

### 처리 시간 예상
- 이미지 1개당 약 5-10초 소요 (API 호출 대기 시간 포함)
- 최종 문서 생성에 약 10-20초 소요
- 예시) 이미지 4개 포함된 10페이지 PDF 기준: 총 1-2분 소요

### 에러 처리
1. PDF 파싱 에러
   - PDF 파일 깨짐 여부 확인
   - PDF 텍스트 추출 가능 여부 확인

2. 이미지 처리 에러
   - 이미지 형식 확인
   - 이미지 품질 확인

3. API 호출 에러
   - AWS 자격 증명 확인
   - Bedrock 모델 접근 권한 확인
   - 네트워크 연결 상태 확인

## 문제 해결

### 일반적인 문제
1. `ImportError` 발생 시
   - requirements.txt 재설치
   - Python 버전 확인

2. AWS 인증 관련 에러
   - AWS CLI 자격 증명 재설정
   - IAM 권한 확인

3. 메모리 부족 에러
   - 큰 PDF 파일의 경우 분할 처리 고려
   - 시스템 리소스 확인

### 기타 문제
- 이슈 리포트 작성 시 에러 메시지 전체 포함
- 실행 환경 정보 포함 (OS, Python 버전 등)
