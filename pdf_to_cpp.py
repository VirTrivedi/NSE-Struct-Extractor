import os
import json
from pathlib import Path
from numind import NuMind
import anthropic
import argparse
from dotenv import load_dotenv

load_dotenv()

def extract_schema_from_pdf(api_key: str, pdf_path: str, project_id: str):
    client = NuMind(api_key=api_key)

    try:
        file_path = Path(pdf_path)
        with file_path.open("rb") as file:
            input_file = file.read()
        output_schema = client.extract(project_id, input_file=input_file)

        if hasattr(output_schema, 'result'):
            output_data = output_schema.result
        else:
            output_data = output_schema

        print(f"Successfully extracted data from: {pdf_path}")
        return output_data

    except FileNotFoundError:
        print(f"Error: The file was not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"An error occurred processing {pdf_path}: {e}")
        return None


def process_pdf_folder(api_key: str, folder_path: str, project_id: str):
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: Folder does not exist or is not a directory: {folder_path}")
        return []
    
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in folder: {folder_path}")
        return []
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    all_results = []
    
    for pdf_file in pdf_files:
        result = extract_schema_from_pdf(api_key, str(pdf_file), project_id)
        
        if result is not None:
            all_results.append(result)
        else:
            print(f"Failed to process {pdf_file.name}")
    
    print(f"Successfully processed {len(all_results)} out of {len(pdf_files)} PDF files")
    return all_results


def convert_json_to_cpp_structs(schema_entries, example_file_path, output_path, claude_api_key):
    """
    Converts JSON schema entries to C++ structs using Claude API
    """
    with open(example_file_path, 'r') as f:
        example_content = f.read()
    
    client = anthropic.Anthropic(api_key=claude_api_key)
    
    all_cpp_structs = []
    total_entries = len(schema_entries)
    
    print(f"Converting {total_entries} JSON schemas to C++ structs...")
    
    for i, entry in enumerate(schema_entries):
        print(f"Processing schema {i+1}/{total_entries}...")
        
        prompt = f"""
I need to convert a JSON schema definition to a C++ struct. 
Here's an example of how the conversion should work:

{example_content}

Now convert the following JSON schema to a C++ struct following the same pattern:

{json.dumps(entry, indent=2)}

Respond with only the C++ struct code.
"""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0,
                system="You convert JSON to C++ structs and can only respond with the C++ struct code.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            cpp_struct = message.content[0].text.strip()
            all_cpp_structs.append(cpp_struct)
            
        except Exception as e:
            print(f"Error processing schema {i+1}: {e}")
    
    with open(output_path, 'w') as f:
        f.write("\n\n".join(all_cpp_structs))
    
    print(f"Successfully converted {len(all_cpp_structs)} out of {total_entries} schemas")
    print(f"C++ structs saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Converts PDF schemas to C++ structs')
    parser.add_argument('--input', '-i', type=str, help='Input folder containing PDF files', required=True)
    parser.add_argument('--output', '-o', type=str, help='Output file path for C++ structs', default="cpp_structs.txt")
    args = parser.parse_args()

    numind_api_key = os.getenv("NUMIND_API_KEY")
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not numind_api_key:
        print("Error: NUMIND_API_KEY environment variable not set.")
    elif not claude_api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
    else:
        input_folder = args.input
        cpp_output = args.output
        project_id = "5482394a-f01b-447e-b4ec-5f1e2b13dc47"
        example_path = os.path.join(os.path.dirname(__file__), "example.txt")

        print(f"Processing PDFs from: {input_folder}")
        print(f"Output will be saved to: {cpp_output}")

        schema_data = process_pdf_folder(
            api_key=numind_api_key,
            folder_path=input_folder,
            project_id=project_id
        )
        
        if schema_data:
            convert_json_to_cpp_structs(
                schema_entries=schema_data,
                example_file_path=example_path,
                output_path=cpp_output,
                claude_api_key=claude_api_key
            )
        else:
            print("No schema data to convert.")