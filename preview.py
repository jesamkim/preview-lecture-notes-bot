import sys
import pathlib
import shutil
import time
import json
import base64
import boto3
from PIL import Image
import io
import pymupdf4llm

def create_initial_markdown(pdf_path, temp_dir):
    """PDF를 파싱하여 초기 마크다운 파일 생성"""
    pdf_name = pathlib.Path(pdf_path).stem
    
    # PDF를 마크다운으로 변환
    md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
    
    # 초기 마크다운 파일 생성
    output_path = pathlib.Path(f"{pdf_name}-1-init.md")
    output_path.write_text(md_text, encoding="utf-8")
    
    # 이미지 파일들을 temp 디렉토리로 이동
    for file in pathlib.Path().glob(f"{pdf_name}*.png"):
        shutil.move(str(file), str(temp_dir / file.name))
    
    return output_path

def encode_image_to_base64(image_path):
    """이미지 파일을 base64로 인코딩"""
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def analyze_image_with_bedrock(bedrock_client, image_path, max_retries=3, retry_count=0):
    """Bedrock을 사용하여 이미지 분석"""
    try:
        base64_image = encode_image_to_base64(image_path)
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": "이 이미지를 5문장 이내로 설명해주세요. 학술적인 내용이 포함된 경우 전문적이면서 이해하기 쉽게 설명해주세요."
                        }
                    ]
                }
            ]
        }

        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read().decode())
        return response_body['content'][0]['text']
    
    except Exception as e:
        if "ThrottlingException" in str(e) and retry_count < max_retries:
            print(f"Throttling error occurred. Retrying in 3 seconds... (Attempt {retry_count + 1}/{max_retries})")
            time.sleep(3)
            return analyze_image_with_bedrock(bedrock_client, image_path, max_retries, retry_count + 1)
        else:
            print(f"Error analyzing image {image_path}: {str(e)}")
            return None

def create_enhanced_markdown(init_md_path, temp_dir, bedrock_client):
    """이미지 분석 결과를 추가한 향상된 마크다운 생성"""
    pdf_name = init_md_path.stem.replace('-1-init', '')
    enhanced_path = pathlib.Path(f"{pdf_name}-2-enhanced.md")
    
    # 초기 마크다운 내용 읽기
    content = init_md_path.read_text(encoding='utf-8')
    
    # 이미지 분석 및 설명을 이미지 바로 아래에 추가
    lines = content.split('\n')
    new_lines = []
    analyzed_images = set()  # 이미 분석한 이미지 추적
    
    for line in lines:
        if '![' in line and '](' in line:  # 이미지 라인 발견
            image_name = line.split('(')[-1].split(')')[0]  # 이미지 파일명 추출
            # temp 디렉토리 경로를 포함하여 이미지 라인 추가
            new_lines.append(f'![](temp/{image_name})')
            
            # 이미지 분석 및 설명 추가
            if image_name not in analyzed_images:  # 아직 분석하지 않은 이미지만 처리
                image_path = temp_dir / pathlib.Path(image_name).name
                print(f"Analyzing image: {image_path.name}")
                description = analyze_image_with_bedrock(bedrock_client, image_path, max_retries=3)
                if description:
                    new_lines.append(f"\n> **이미지 설명:**")
                    for desc_line in description.split('\n'):
                        new_lines.append(f"> {desc_line}")
                    new_lines.append("")  # 빈 줄 추가
                analyzed_images.add(image_name)  # 분석 완료된 이미지 추적
                time.sleep(8)  # API 쓰로틀링 방지 (더 긴 대기 시간)
        else:  # 일반 텍스트 라인은 그대로 추가
            new_lines.append(line)
    
    # 향상된 마크다운 파일 생성
    enhanced_content = '\n'.join(new_lines)
    enhanced_path.write_text(enhanced_content, encoding='utf-8')
    
    return enhanced_path

def create_final_markdown(enhanced_md_path, bedrock_client, max_retries=3, retry_count=0):
    """최종 마크다운 파일 생성"""
    pdf_name = enhanced_md_path.stem.replace('-2-enhanced', '')
    final_path = pathlib.Path(f"{pdf_name}-3-completed.md")
    
    # 향상된 마크다운 내용 읽기
    content = enhanced_md_path.read_text(encoding='utf-8')
    
    # Bedrock을 사용하여 최종 내용 생성
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
인공지능 대학원 강의 자료를 사전 지식이 없는 상태에서 예습에 활용할 수 있도록 다음 지시사항에 맞게 개선해주세요.

<instruction>
1. 문서 구조화:
   - 주제별로 명확한 섹션 구분
   - 핵심 개념을 bullet point로 정리
   - 수식이 나올 때마다 직관적인 설명 추가

2. 이미지 통합:
   - 각 이미지 설명을 해당 섹션의 내용과 자연스럽게 통합
   - 이미지가 설명하는 개념과 텍스트 내용을 연결
   - 이미지의 세부 요소들이 전체 맥락에서 어떤 의미를 갖는지 이해하기 쉽게 설명

3. 개념 설명:
   - 전문 용어에 대한 설명을 이해하기 쉽게 포함
   - 각 전문 용어(term)에 대해 구체적인 예시 포함
   - 복잡한 개념은 이해하기 쉽게 단계별로 설명
   - 실제 응용 사례나 직관적인 쉬운 비유 추가

4. 중요: 
   - 수식은 수학적 의미뿐만 아니라 실제 적용 관점에서도 설명
   - 이전 개념과 새로운 개념의 연결성 강조
   
5. 내용은 이해하기 쉽게 하는 것이 목적이므로 충분히 풍부하게 작성합니다.
</instruction>

노트 내용:
<content>
{content}
</content>
"""
                        }
                    ]
                }
            ]
        }

        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read().decode())
        final_content = response_body['content'][0]['text']
        
        # 최종 마크다운 파일 생성
        final_path.write_text(final_content, encoding='utf-8')
        return final_path
    
    except Exception as e:
        if "ThrottlingException" in str(e) and retry_count < max_retries:
            print(f"Throttling error occurred. Retrying in 3 seconds... (Attempt {retry_count + 1}/{max_retries})")
            time.sleep(3)
            return create_final_markdown(enhanced_md_path, bedrock_client, max_retries, retry_count + 1)
        else:
            print(f"Error creating final markdown: {str(e)}")
            return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python preview.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = pathlib.Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        sys.exit(1)
    
    # Bedrock 클라이언트 설정
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-west-2'
    )
    
    # 임시 디렉토리 생성
    temp_dir = pathlib.Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 1. 초기 마크다운 생성
        print("Creating initial markdown...")
        init_md_path = create_initial_markdown(pdf_path, temp_dir)
        print(f"Initial markdown created: {init_md_path}")
        
        # 2. 이미지 분석 결과가 포함된 향상된 마크다운 생성
        print("Creating enhanced markdown with image analyses...")
        enhanced_md_path = create_enhanced_markdown(init_md_path, temp_dir, bedrock_client)
        print(f"Enhanced markdown created: {enhanced_md_path}")
        
        # 3. 최종 마크다운 생성
        print("Creating final markdown...")
        final_md_path = create_final_markdown(enhanced_md_path, bedrock_client, max_retries=3)
        if final_md_path:
            print(f"Final markdown created: {final_md_path}")
            print("\nProcess completed successfully!")
        else:
            print("Error: Failed to create final markdown")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
