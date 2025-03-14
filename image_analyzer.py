import pathlib
import json
import base64
import boto3
from PIL import Image
import io
from utils import wait_with_backoff
from config import BEDROCK_REGION, BEDROCK_MODEL_ID, MAX_RETRIES, TEMP_DIR

def encode_image_to_base64(image_path):
    """이미지 파일을 base64로 인코딩"""
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def analyze_image(bedrock_client, image_path, retry_count=0):
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
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read().decode())
        return response_body['content'][0]['text']
    
    except Exception as e:
        if "ThrottlingException" in str(e) and retry_count < MAX_RETRIES:
            print(f"Throttling error occurred. Retrying in {2**retry_count * 3} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
            wait_with_backoff(retry_count)
            return analyze_image(bedrock_client, image_path, retry_count + 1)
        else:
            print(f"Error analyzing image {image_path}: {str(e)}")
            return None

def analyze_images_in_markdown(md_path):
    """마크다운 파일의 모든 이미지 분석"""
    bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)
    content = md_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    new_lines = []
    analyzed_images = set()

    for line in lines:
        new_lines.append(line)
        if '![' in line and '](' in line:
            image_name = line.split('(')[-1].split(')')[0]
            if image_name not in analyzed_images:
                image_path = pathlib.Path(TEMP_DIR) / pathlib.Path(image_name).name
                print(f"Analyzing image: {image_path.name}")
                description = analyze_image(bedrock_client, image_path)
                if description:
                    # 이미지 경로 수정
                    new_lines[-1] = f'![](./temp/{image_name})'
                    new_lines.append(f"\n> **이미지 설명:**")
                    for desc_line in description.split('\n'):
                        new_lines.append(f"> {desc_line}")
                    new_lines.append("")
                analyzed_images.add(image_name)
                wait_with_backoff(0)  # API 쓰로틀링 방지

    enhanced_content = '\n'.join(new_lines)
    enhanced_path = md_path.with_name(md_path.stem.replace('-1-init', '-2-enhanced') + md_path.suffix)
    enhanced_path.write_text(enhanced_content, encoding='utf-8')
    return enhanced_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python image_analyzer.py <markdown_file>")
        sys.exit(1)
    
    md_path = pathlib.Path(sys.argv[1])
    if not md_path.exists():
        print(f"Error: File {md_path} does not exist")
        sys.exit(1)
    
    enhanced_path = analyze_images_in_markdown(md_path)
    print(f"Enhanced markdown created: {enhanced_path}")
