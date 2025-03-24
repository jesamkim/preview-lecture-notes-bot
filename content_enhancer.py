import pathlib
import json
import boto3
from utils import wait_with_backoff
from config import BEDROCK_REGION, BEDROCK_MODEL_ID, MAX_RETRIES, CHUNK_SIZE

def process_chunk(bedrock_client, chunk, instruction, retry_count=0):
    """청크를 처리하고 결과를 반환"""
    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
{instruction}

노트 내용:
<content>
{chunk}
</content>
"""
                        }
                    ]
                }
            ]
        }

        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read().decode())
        return response_body['content'][0]['text']
    
    except Exception as e:
        if "ThrottlingException" in str(e) and retry_count < MAX_RETRIES:
            print(f"Throttling error occurred. Retrying in {2**retry_count * 3} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            wait_with_backoff(retry_count)
            return process_chunk(bedrock_client, chunk, instruction, retry_count + 1)
        else:
            print(f"Error processing chunk: {str(e)}")
            return None

def enhance_content(enhanced_md_path):
    """최종 마크다운 파일 생성"""
    bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)
    pdf_name = enhanced_md_path.stem.replace('-2-enhanced', '')
    final_path = pathlib.Path(f"{pdf_name}-3-completed.md")
    log_path = pathlib.Path(f"{pdf_name}-3-completed.log")
    
    # 향상된 마크다운 내용 읽기
    content = enhanced_md_path.read_text(encoding='utf-8')
    
    # 처리 지침
    instruction = """
다음 지시사항에 따라 주어진 텍스트를 개선해주세요:

1. 문서의 기본 구조와 형식, 문서 전체에서 다루는 주제(context)를 유지하세요.
2. png 파일 경로로 되어 있는 이미지는 모두 유지합니다.
3. 모든 이미지 참조와 이미지 설명을 그대로 유지하세요. 단 문서의 주제에 대해 설명이 변경되어 하는 경우에는 수정하세요.
4. 전문 용어가 나오면 괄호 안에 영문 약어(있는 경우)와 함께 이해하기 쉽게 설명을 추가하세요. 예: 인공지능(AI, Artificial Intelligence: 컴퓨터가 인간의 지능을 모방하는 기술)
5. 설명이 부족한 부분이 있다면 더 자세하고 이해하기 쉬운 설명을 추가하세요. 특히 수식에 대해서는 그대로 표현하면서도 어떤 내용인지 해설을 해주세요.
6. 내용의 흐름을 자연스럽게 만들고, 각 섹션 간의 연결을 강화하세요.
7. 복잡한 개념은 일상적인 예시나 비유를 사용하여 설명하세요.
8. 각 주요 개념이나 기술에 대해 실제 응용 사례를 1-2개 추가하세요.
9. 각 섹션의 끝에 해당 섹션의 핵심 내용을 요약하는 1-2문장을 추가하세요.
10. "개선된 버전을 제시하겠습니다:" 와 같은 응답성 메세지는 출력하지 마세요.

주의: 필요한 경우가 아니라면 원본 내용의 의미를 변경하거나 새로운 주제를 추가하지 마세요. 학생을 위해 원본 내용을 더 이해하기 쉽고 풍부하게 만드는 것이 목표입니다.
"""
    
    # 내용을 청크로 나누기
    chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]
    
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        processed_chunk = process_chunk(bedrock_client, chunk, instruction)
        if processed_chunk:
            processed_chunks.append(processed_chunk)
        else:
            print(f"Error: Failed to process chunk {i+1}")
    
    if processed_chunks:
        # 처리된 청크 결합
        processed_content = "\n\n".join(processed_chunks)
        
        # 최종 마크다운 파일 생성
        final_path.write_text(processed_content, encoding='utf-8')
        # 로그 파일에 전체 내용 저장
        log_path.write_text(processed_content, encoding='utf-8')
        print(f"Enhanced content preview:\n{processed_content[:1000]}...")  # 처리된 내용의 미리보기 길이를 1000자로 늘림
        print(f"Full content saved to log file: {log_path}")
        return final_path
    else:
        print("Error: Failed to process all chunks")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python content_enhancer.py <enhanced_markdown_file>")
        sys.exit(1)
    
    enhanced_md_path = pathlib.Path(sys.argv[1])
    if not enhanced_md_path.exists():
        print(f"Error: File {enhanced_md_path} does not exist")
        sys.exit(1)
    
    final_path = enhance_content(enhanced_md_path)
    print(f"Final markdown created: {final_path}")
