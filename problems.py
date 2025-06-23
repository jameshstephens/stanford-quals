#!/usr/bin/env python3
"""
Cleanup script for tagged problems repository.
Identifies missing problems and reprocesses PDFs that didn't extract exactly 10 problems.
"""

import os
import json
import glob
import re
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_existing_problems():
    """Analyze the existing tagged problems to identify missing ones"""
    print("Analyzing existing tagged problems...")
    
    try:
        with open('tagged_problems_repository.json', 'r', encoding='utf-8') as f:
            problems = json.load(f)
    except FileNotFoundError:
        print("Error: tagged_problems_repository.json not found")
        return {}, {}
    
    # Track problems by year/semester/session/number
    existing_problems = defaultdict(set)
    problems_by_pdf = defaultdict(list)
    
    for problem in problems:
        year = problem.get('year')
        semester = problem.get('semester')
        session = problem.get('session')
        problem_number = problem.get('problem_number')
        filename = problem.get('filename')
        
        if all([year, semester, session, problem_number]):
            key = f"{year}_{semester}_{session}_{problem_number}"
            existing_problems[f"{year}_{semester}"].add(key)
            problems_by_pdf[filename].append(problem)
    
    return existing_problems, problems_by_pdf

def identify_missing_problems():
    """Identify all missing problems for years 2009-2024"""
    print("Identifying missing problems...")
    
    existing_problems, problems_by_pdf = analyze_existing_problems()
    
    expected_problems = set()
    missing_problems = set()
    
    # Generate expected problems for each year 2009-2024
    for year in range(2009, 2025):
        for semester in ['Autumn', 'Spring']:
            for session in ['morning', 'afternoon']:
                for problem_num in range(1, 6):  # Problems 1-5 for each session
                    expected_key = f"{year}_{semester}_{session}_{problem_num}"
                    expected_problems.add(expected_key)
                    
                    year_sem_key = f"{year}_{semester}"
                    if expected_key not in existing_problems.get(year_sem_key, set()):
                        missing_problems.add(expected_key)
    
    print(f"Expected total problems: {len(expected_problems)}")
    print(f"Missing problems: {len(missing_problems)}")
    
    # Analyze PDFs with incorrect problem counts
    pdfs_with_wrong_count = {}
    for filename, file_problems in problems_by_pdf.items():
        if len(file_problems) != 10:
            pdfs_with_wrong_count[filename] = len(file_problems)
            print(f"  {filename}: {len(file_problems)} problems (should be 10)")
    
    # Also check for completely missing PDFs
    expected_pdfs = set()
    for year in range(2009, 2025):
        for semester in ['Autumn', 'Spring']:
            expected_pdfs.add(f"{year} {semester} Real Analysis Qual.pdf")
    
    existing_pdfs = set(problems_by_pdf.keys())
    missing_pdfs = expected_pdfs - existing_pdfs
    
    print(f"\nPDFs completely missing from repository:")
    for pdf in sorted(missing_pdfs):
        print(f"  {pdf}")
        pdfs_with_wrong_count[pdf] = 0  # Add to reprocess list
    
    return missing_problems, pdfs_with_wrong_count, problems_by_pdf

def find_pdf_for_problem(problem_key):
    """Find the PDF filename for a given problem key"""
    year, semester, session, problem_num = problem_key.split('_')
    return f"{year} {semester} Real Analysis Qual.pdf"

def remove_problems_from_incomplete_pdfs(pdfs_with_wrong_count, problems_by_pdf):
    """Remove all problems from PDFs that don't have exactly 10 problems"""
    print("Removing problems from incomplete PDFs...")
    
    try:
        with open('tagged_problems_repository.json', 'r', encoding='utf-8') as f:
            all_problems = json.load(f)
    except FileNotFoundError:
        print("Error: tagged_problems_repository.json not found")
        return
    
    # Create set of filenames to remove
    files_to_remove = set(pdfs_with_wrong_count.keys())
    
    # Filter out problems from incomplete PDFs
    cleaned_problems = []
    removed_count = 0
    
    for problem in all_problems:
        if problem.get('filename') in files_to_remove:
            removed_count += 1
            print(f"  Removing: {problem.get('title', 'Unknown')}")
        else:
            cleaned_problems.append(problem)
    
    print(f"Removed {removed_count} problems from {len(files_to_remove)} incomplete PDFs")
    
    # Save cleaned repository
    with open('tagged_problems_repository.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_problems, f, indent=2, ensure_ascii=False)
    
    print("Cleaned repository saved")

def load_syllabus_tags():
    """Load the syllabus tags from the generated file"""
    try:
        with open('syllabus_tags.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            tags = data.get('tags', [])
            print(f"Loaded {len(tags)} syllabus tags")
            return tags
    except FileNotFoundError:
        print("Error: syllabus_tags.json not found. Please run generate_tags.py first.")
        return []
    except Exception as e:
        print(f"Error loading syllabus tags: {e}")
        return []

def parse_filename(filename):
    """Parse PDF filename to extract year, semester, and session info"""
    basename = os.path.basename(filename)
    
    # Extract year
    year_match = re.search(r'(\d{4})', basename)
    year = year_match.group(1) if year_match else "Unknown"
    
    # Extract semester
    if "Spring" in basename:
        semester = "Spring"
    elif "Autumn" in basename or "Fall" in basename:
        semester = "Autumn"
    else:
        semester = "Unknown"
    
    return year, semester

def extract_problems_from_pdf(pdf_path):
    """Use GPT-4.1 to extract individual problems from a PDF"""
    client = OpenAI()
    
    year, semester = parse_filename(pdf_path)
    
    prompt = f"""
    Extract all individual problems from this Real Analysis qualifying exam PDF.
    
    For each problem:
    1. Identify if it's from morning or afternoon session (if indicated)
    2. Extract the problem number
    3. Extract the complete problem statement

    Extract EXACTLY 10 problems from the PDF. If a problem has multiple parts (a) and (b), extract them TOGETHER as ONE PROBLEM.  
    Return the results as a JSON array where each object has:
    - "session": "morning" or "afternoon". The morning is the first set of five problems. The afternoon is the second set of five problems.
    - "problem_number": the problem number
    - "content": the complete problem statement in exact LaTeX format.
    
    Your output in content must be precise LaTeX. NEVER USE ITEMIZE OR ENUMERATE OR SIMILAR ENVIRONMENTS. Only vanilla LaTeX!
    """
    
    try:
        # Upload the PDF file
        file = client.files.create(
            file=open(pdf_path, "rb"),
            purpose="user_data"
        )
        
        # Use GPT-4.1 with direct PDF processing
        response = client.responses.create(
            model="gpt-4.1-mini",
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
        
        # Get the response content using the correct format
        response_content = response.output[0].content[0].text
        
        # Extract JSON from the response content
        if '```json' in response_content:
            start_idx = response_content.find('```json') + 7
            end_idx = response_content.find('```', start_idx)
            json_str = response_content[start_idx:end_idx].strip()
        else:
            # Try to find JSON array directly
            start_idx = response_content.find('[')
            end_idx = response_content.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
            else:
                print(f"Could not extract JSON from response for {pdf_path}")
                print("Full response:", response_content)
                return []
        
        # Parse JSON response with robust handling
        try:
            problems_data = json.loads(json_str)
        except json.JSONDecodeError:
            print(f"Standard JSON parsing failed for {pdf_path}, trying robust parsing...")
            # Try to extract JSON using regex
            import re
            json_match = re.search(r'\[.*\]', json_str, re.DOTALL)
            if json_match:
                try:
                    problems_data = json.loads(json_match.group(0))
                except:
                    print(f"Regex failed, trying manual parsing...")
                    return []
            else:
                print(f"Failed to parse JSON response for {pdf_path}")
                return []
        
        # Process the extracted problems
        processed_problems = []
        for i, problem_data in enumerate(problems_data):
            session = problem_data.get('session', 'morning' if i < 5 else 'afternoon')
            problem_number = problem_data.get('problem_number', (i % 5) + 1)
            content = problem_data.get('content', '')
            
            # Create problem title
            title = f"{year}_{semester}_{session}_{problem_number}"
            
            processed_problem = {
                'title': title,
                'content': content,
                'year': year,
                'semester': semester,
                'session': session,
                'problem_number': problem_number,
                'filename': os.path.basename(pdf_path)
            }
            processed_problems.append(processed_problem)
        
        print(f"  Extracted {len(processed_problems)} problems from {os.path.basename(pdf_path)}")
        return processed_problems
        
    except Exception as e:
        print(f"Error extracting problems from {pdf_path}: {e}")
        return []

def tag_problem(problem_content, syllabus_tags):
    """Use gpt-4.1-mini to tag a problem with relevant syllabus topics"""
    client = OpenAI()
    
    tags_list = "\n".join([f"- {tag}" for tag in syllabus_tags])
    
    prompt = f"""You are tasked with tagging a Real Analysis qualifying exam problem with relevant topics from the syllabus.

Given problem:
{problem_content}

Available syllabus tags:
{tags_list}

Instructions:
1. Read the problem carefully and identify the main mathematical concepts
2. Select 1-3 most relevant tags from the syllabus list above
3. Return ONLY a JSON array of the selected tags, nothing else
4. Example output: ["Integration", "Banach spaces"]

Your response:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        response_content = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            tags = json.loads(response_content)
            return tags if isinstance(tags, list) else []
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\[(.*?)\]', response_content)
            if json_match:
                try:
                    tags = json.loads(f'[{json_match.group(1)}]')
                    return tags if isinstance(tags, list) else []
                except:
                    pass
            
            print(f"Failed to parse tagging response: {response_content}")
            return []
    
    except Exception as e:
        print(f"Error tagging problem: {e}")
        return []

def reprocess_pdf(pdf_path, syllabus_tags):
    """Reprocess a single PDF to extract and tag problems"""
    print(f"Reprocessing {os.path.basename(pdf_path)}...")
    
    # Extract problems
    problems = extract_problems_from_pdf(pdf_path)
    
    if len(problems) != 10:
        print(f"  Warning: Extracted {len(problems)} problems (expected 10)")
        return []
    
    # Tag each problem
    tagged_problems = []
    for i, problem in enumerate(problems, 1):
        print(f"  Tagging problem {i}/10: {problem['title']}")
        tags = tag_problem(problem['content'], syllabus_tags)
        problem['tags'] = tags
        tagged_problems.append(problem)
        print(f"    Assigned tags: {tags}")
    
    return tagged_problems

def update_repository(new_problems, pdf_name):
    """Add new problems to the repository and update immediately"""
    try:
        with open('tagged_problems_repository.json', 'r', encoding='utf-8') as f:
            existing_problems = json.load(f)
    except FileNotFoundError:
        existing_problems = []
    
    # Add new problems
    existing_problems.extend(new_problems)
    
    # Save updated repository immediately
    with open('tagged_problems_repository.json', 'w', encoding='utf-8') as f:
        json.dump(existing_problems, f, indent=2, ensure_ascii=False)
    
    print(f"  Added {len(new_problems)} problems from {pdf_name} to repository (total: {len(existing_problems)})")

def main():
    """Main cleanup function"""
    print("=== CLEANUP SCRIPT STARTED ===")
    
    # Load syllabus tags
    syllabus_tags = load_syllabus_tags()
    if not syllabus_tags:
        print("Cannot proceed without syllabus tags")
        return
    
    # Analyze existing problems
    missing_problems, pdfs_with_wrong_count, problems_by_pdf = identify_missing_problems()
    
    print(f"\nFound {len(pdfs_with_wrong_count)} PDFs with incorrect problem counts:")
    for filename, count in pdfs_with_wrong_count.items():
        print(f"  {filename}: {count} problems")
    
    # Remove problems from incomplete PDFs
    if pdfs_with_wrong_count:
        remove_problems_from_incomplete_pdfs(pdfs_with_wrong_count, problems_by_pdf)
    
    # Reprocess PDFs that had wrong counts
    print("\n=== REPROCESSING INCOMPLETE PDFs ===")
    total_reprocessed = 0
    
    for filename in pdfs_with_wrong_count.keys():
        pdf_path = filename
        if os.path.exists(pdf_path):
            new_problems = reprocess_pdf(pdf_path, syllabus_tags)
            if len(new_problems) == 10:
                # Update repository immediately after each PDF
                update_repository(new_problems, filename)
                total_reprocessed += len(new_problems)
                print(f"  Successfully reprocessed {filename}")
            else:
                print(f"  Failed to get exactly 10 problems from {filename}")
        else:
            print(f"  PDF file not found: {filename}")
    
    print(f"\n=== CLEANUP COMPLETE ===")
    print(f"Reprocessed {len(pdfs_with_wrong_count)} PDFs")
    print(f"Added {total_reprocessed} new problems")

if __name__ == "__main__":
    main()