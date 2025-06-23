#!/usr/bin/env python3
"""
Program to read syllabus.pdf and generate tags using GPT-4 with direct PDF processing
"""

import os
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_tags_with_gpt4(pdf_path):
    """Use GPT-4.1 to analyze PDF syllabus and generate relevant tags"""
    client = OpenAI()
    
    prompt = """
    Extract the title for each numbered SUBsection from this Real Analysis syllabus PDF document. There should be more than 10 tags.

    Return these headings as a clean JSON array of strings, keeping the original wording as much as possible.
    """
    
    try:
        # Upload the PDF file
        file = client.files.create(
            file=open(pdf_path, "rb"),
            purpose="user_data"
        )
        
        # Use GPT-4.1 with direct PDF processing
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": file.id,
                        },
                        {
                            "type": "input_text", 
                            "text": prompt,
                        },
                    ]
                }
            ]
        )
        
        # Extract the JSON array from the response
        content = response.output[0].content[0].text
        
        # Extract JSON from markdown code block
        if '```json' in content:
            start_idx = content.find('```json') + 7
            end_idx = content.find('```', start_idx)
            json_str = content[start_idx:end_idx].strip()
        else:
            # Try to find JSON array directly
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
            else:
                print("Could not extract JSON from GPT-4 response")
                print("Full response:", content)
                return None
        
        try:
            tags = json.loads(json_str)
            return tags
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print("JSON string:", json_str)
            return None
            
    except Exception as e:
        print(f"Error calling GPT-4 API: {e}")
        return None

def save_tags_to_file(tags, output_file):
    """Save tags to a JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump({
                "generated_from": "syllabus.pdf",
                "tags": tags,
                "total_tags": len(tags)
            }, f, indent=2)
        print(f"Tags saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving tags: {e}")
        return False

def main():
    # File paths
    syllabus_path = "syllabus.pdf"
    output_path = "syllabus_tags.json"
    
    print("Processing syllabus.pdf with GPT-4.1...")
    
    tags = generate_tags_with_gpt4(syllabus_path)
    
    if not tags:
        print("Failed to generate tags")
        return
    
    print(f"Generated {len(tags)} tags")
    print("Sample tags:", tags[:5] if len(tags) > 5 else tags)
    
    if save_tags_to_file(tags, output_path):
        print(f"Successfully created indexed tags database in {output_path}")
    else:
        print("Failed to save tags")

if __name__ == "__main__":
    main()