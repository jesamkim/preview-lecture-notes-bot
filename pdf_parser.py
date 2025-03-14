import pathlib
import shutil
import pymupdf4llm
from utils import create_temp_dir, get_pdf_name
from config import TEMP_DIR

def parse_pdf(pdf_path):
    """PDF를 파싱하여 초기 마크다운 파일 생성"""
    pdf_name = get_pdf_name(pdf_path)
    temp_dir = create_temp_dir()
    
    # PDF를 마크다운으로 변환
    md_text = pymupdf4llm.to_markdown(pdf_path, write_images=True)
    
    # 초기 마크다운 파일 생성
    output_path = pathlib.Path(f"{pdf_name}-1-init.md")
    output_path.write_text(md_text, encoding="utf-8")
    
    # 이미지 파일들을 temp 디렉토리로 이동
    for file in pathlib.Path().glob(f"{pdf_name}*.png"):
        shutil.move(str(file), str(temp_dir / file.name))
    
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python pdf_parser.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = pathlib.Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        sys.exit(1)
    
    output_path = parse_pdf(pdf_path)
    print(f"Initial markdown created: {output_path}")
