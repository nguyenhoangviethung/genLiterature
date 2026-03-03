import json
import time
import google.generativeai as genai

API_KEY = "AIzaSyCMbISntLwU_m3osTnLmfp941vcA61SV14"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemma-3-27b-it')

def augment_data(instruction, response, max_retries=5):
    """Gọi LLM với cơ chế tự động thử lại (retry) và thiết lập thời gian chờ (timeout)."""
    prompt = f"""
    Dưới đây là một cặp câu lệnh và bài văn nghị luận xã hội mẫu.
    Câu lệnh gốc: "{instruction}"
    Bài làm gốc: "{response}"

    Nhiệm vụ của bạn là tạo ra 2 phiên bản hoàn toàn mới dựa trên nội dung này để làm dữ liệu huấn luyện AI.
    - Biến thể 1: Đa dạng hóa câu lệnh. Viết lại bài làm với cách lập luận sắc bén hơn, thay đổi cách mở/kết bài, nhưng giữ độ dài khoảng 200 chữ.
    - Biến thể 2: Tiếp tục thay đổi cách hỏi trong câu lệnh. Viết lại bài làm với một giọng văn mềm mỏng, cảm xúc hơn hoặc thay đổi dẫn chứng, giữ độ dài khoảng 200 chữ.

    YÊU CẦU BẮT BUỘC: Chỉ trả về mảng JSON nguyên gốc (không có markdown ```json), đúng định dạng sau:
    [
      {{"instruction": "câu lệnh mới 1", "response": "bài làm mới 1"}},
      {{"instruction": "câu lệnh mới 2", "response": "bài làm mới 2"}}
    ]
    """
    
    for attempt in range(max_retries):
        try:
            result = model.generate_content(
                prompt, 
                request_options={"timeout": 60}
            )
            
            raw_text = result.text.strip().removeprefix('```json').removesuffix('```').strip()
            augmented_pairs = json.loads(raw_text)
            return augmented_pairs
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                wait_time = 40 * (attempt + 1)
                print(f"Request quota exceeded (error 429). Waiting {wait_time}s before retrying (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            else:
                print(f"Error occurred (JSON parse error or API timeout): {error_msg}")
                print(f"Trying again immediately (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(5) 
                
    print(f"Attempted {max_retries} times but still failed. Skipping this sample to continue.")
    return []

def main():
    input_file = 'data/social_discussion/hocmai_thpt_dataset.jsonl'
    output_file = 'data/social_discussion/hocmai_thpt_dataset_augmented.jsonl'
    
    all_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                all_data.append(json.loads(line.strip()))
                
    print(f"Attempted {len(all_data)} samples.")
    
    augmented_dataset = []
    
    for i, item in enumerate(all_data):
        print(f"Processing sample {i + 1}/{len(all_data)}...")
        
        augmented_dataset.append(item)
        
        new_variations = augment_data(item['instruction'], item['response'])
        augmented_dataset.extend(new_variations)
        
        time.sleep(2) 

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in augmented_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"Hoàn thành! Đã tạo ra {len(augmented_dataset)} mẫu dữ liệu và lưu vào {output_file}")

if __name__ == "__main__":
    main()