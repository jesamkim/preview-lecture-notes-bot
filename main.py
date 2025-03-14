import sys
import pathlib
from pdf_parser import parse_pdf
from image_analyzer import analyze_images_in_markdown
from content_enhancer import enhance_content

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = pathlib.Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} does not exist")
        sys.exit(1)
    
    try:
        # 1. PDF 파싱
        print("Step 1: Parsing PDF...")
        init_md_path = parse_pdf(pdf_path)
        print(f"Initial markdown created: {init_md_path}")
        
        # 2. 이미지 분석
        print("\nStep 2: Analyzing images...")
        enhanced_md_path = analyze_images_in_markdown(init_md_path)
        print(f"Enhanced markdown created: {enhanced_md_path}")
        
        # 3. 콘텐츠 개선
        print("\nStep 3: Enhancing content...")
        final_md_path = enhance_content(enhanced_md_path)
        print(f"Final markdown created: {final_md_path}")
        
        print("\nProcess completed successfully!")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
