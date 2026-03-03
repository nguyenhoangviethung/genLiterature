import re
import json
import pdfplumber

class SocialDiscussionExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.dataset = []

    def extract(self, output_jsonl_path, skip_pages=4, 
                pattern_instruction=r'(?:\n|^)(?:\d+\.\s+|Đề \d+:\s*)([^\n]+)',
                sub_pattern=r'(Bài \d+|Đoạn văn \d+|Mẫu \d+|Bài số \d+)\s*\n'):
        
        full_text = ""
        print(f"Reading PDF: {self.pdf_path}...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i < skip_pages: 
                    continue
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        
        full_text = re.sub(r'Tổng hợp: Download\.vn', '', full_text)
        full_text = re.sub(r'\n+', '\n', full_text)
        
        matches = list(re.finditer(pattern_instruction, full_text))
        
        print("Đang phân tách Instruction và Response...")
        for i in range(len(matches)):
            start_idx = matches[i].end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
            
            instruction = matches[i].group(1).strip()
            response_text = full_text[start_idx:end_idx].strip()
            
            sub_matches = list(re.finditer(sub_pattern, response_text, re.IGNORECASE))
            
            if sub_matches:
                for j in range(len(sub_matches)):
                    sub_start = sub_matches[j].end()
                    sub_end = sub_matches[j+1].start() if j + 1 < len(sub_matches) else len(response_text)
                    sub_resp = response_text[sub_start:sub_end].strip()
                    sub_resp = re.sub(r'\n+', ' ', sub_resp).strip()
                    
                    if len(sub_resp) > 50: 
                        self.dataset.append({
                            "instruction": instruction,
                            "response": sub_resp
                        })
            else:
                response_text = re.sub(r'\n+', ' ', response_text).strip()
                if len(response_text) > 50:
                    self.dataset.append({
                        "instruction": instruction,
                        "response": response_text
                    })
                    
        print(f"Extract successful {len(self.dataset)} samples.")
        with open(output_jsonl_path, 'w', encoding='utf-8') as f:
            for item in self.dataset:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
        print(f"Done! Saved as: {output_jsonl_path}")
