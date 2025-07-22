import os
import json
from pathlib import Path
from numind import NuMind

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


def process_pdf_folder(api_key: str, folder_path: str, project_id: str, output_path: str):
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: Folder does not exist or is not a directory: {folder_path}")
        return
    
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in folder: {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    all_results = []
    
    for pdf_file in pdf_files:
        result = extract_schema_from_pdf(api_key, str(pdf_file), project_id)
        
        if result is not None:
            all_results.append(result)
        else:
            print(f"Failed to process {pdf_file.name}")
    
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Successfully processed {len(all_results)} out of {len(pdf_files)} PDF files")
    print(f"Combined results saved to: {output_path}")


if __name__ == "__main__":
    api_key = os.getenv("NUMIND_API_KEY")

    if not api_key:
        print("Error: NUMIND_API_KEY environment variable not set.")
    else:
        input_folder = r"\pdfs" # Folder containing PDFs
        output_json = "combined_output.json"
        project_id = "5482394a-f01b-447e-b4ec-5f1e2b13dc47"

        process_pdf_folder(
            api_key=api_key,
            folder_path=input_folder,
            project_id=project_id,
            output_path=output_json
        )
