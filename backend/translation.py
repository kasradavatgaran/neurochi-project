import json
import os
from pathlib import Path
import google.generativeai as genai
import time

# Configure Gemini API
genai.configure(api_key="")

def translate_to_farsi(text: str) -> str:
    """Translate text to Farsi using Gemini API"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite") 

        
        prompt = f"Translate the following text to Farsi (Persian). Only provide the translation, nothing else:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error translating text: {e}")
        return ""

def process_json_files(input_folder: str, output_folder: str):
    """
    Process all JSON files in input folder and save translated content to output folder
    """
    
    os.makedirs(output_folder, exist_ok=True)
    
    json_files = list(Path(input_folder).glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_folder}")
        return
    
    print(f"Found {len(json_files)} JSON files to process\n")
    
    success_count = 0
    skip_count = 0
    
    for json_file in json_files:
        output_filename = json_file.stem + ".txt"
        output_path = os.path.join(output_folder, output_filename)
        
        if os.path.exists(output_path):
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            

            headline = data.get("title_text", "")
            article_body = data.get("content_text", "")
            
            if not headline and not article_body:
                headline = data.get("headline", "")
                article_body = data.get("articleBody", "")

            if headline is None: headline = ""
            if article_body is None: article_body = ""
            
            if not headline and not article_body:
                print(f"⚠ Skipping {json_file.name}: No recognized content found")
                skip_count += 1
                continue
            
            content_to_translate = f"Title: {headline}\n\nArticle Content:\n{article_body}"
            
            print(f"Processing: {json_file.name}...")
            
            translated_text = translate_to_farsi(content_to_translate)
            
            if translated_text:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                print(f"  ✓ Saved to: {output_filename}")
                success_count += 1
                
                time.sleep(1) 
            else:
                print(f"  ✗ Translation failed for {json_file.name}")

        except json.JSONDecodeError:
            print(f"✗ Error: {json_file.name} is not a valid JSON file")
            skip_count += 1
        except Exception as e:
            print(f"✗ Error processing {json_file.name}: {e}")
            skip_count += 1

    print("\n" + "=" * 50)
    print(f"Processing Complete.")
    print(f"Successfully translated: {success_count}")
    print(f"Skipped/Failed: {skip_count}")
    print("=" * 50)

# Main execution
if __name__ == "__main__":
    INPUT_FOLDER = "./kinedu"      
    OUTPUT_FOLDER = "./farsi_translations" 
    
    print("=" * 50)
    print("JSON to Farsi Translation Tool (Dual Format Support)")
    print("=" * 50 + "\n")
    
    process_json_files(INPUT_FOLDER, OUTPUT_FOLDER)
