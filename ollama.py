import subprocess
import json
import re

# Processes and refines extracted data using Ollama's LLaMA2 model
def process_with_ollama(extracted_data):
    print("DEBUG: Entering process_with_ollama...")

    if not extracted_data or "raw_text" not in extracted_data or "key_value_pairs" not in extracted_data:
        print("ERROR: Missing required keys in extracted_data")
        raise ValueError("extracted_data must contain 'raw_text' and 'key_value_pairs' keys.")

    print("DEBUG: extracted_data keys are valid.")

    # Prepare input data for the model
    raw_text = extracted_data["raw_text"]
    key_value_pairs = json.dumps(extracted_data["key_value_pairs"], indent=4)

    print(f"DEBUG: raw_text: {raw_text[:50]}...")
    print(f"DEBUG: key_value_pairs: {key_value_pairs[:50]}...")

    # Enhanced prompt for Ollama
    prompt = f"""
    You are an AI assistant. Given the raw text and key-value pairs below, create a structured JSON object.
    - Fill in all known fields: first_name, last_name, address, insurance_status, start_date, end_date, policy_number, etc.
    - Infer missing data if possible or mark as "Not available."
    - Ensure output is valid JSON only with no additional text.

    Raw Text:
    {raw_text}

    Key-Value Pairs:
    {key_value_pairs}

    Output JSON:
    {{
        "first_name": "<first name>",
        "last_name": "<last name>",
        "address": "<address>",
        "insurance_status": "<active/inactive>",
        "policy_start_date": "<start date>",
        "policy_end_date": "<end date>",
        "policy_number": "<policy number>",
        "dob": "<date of birth>",
        "mobile_number": "<mobile number>",
        "email": "<email>",
        "nationality": "<nationality>",
        "gender": "<gender>",
        "visa_type": "<visa type>",
        "doctor": "<doctor>",
        "emergency_contact_relation": "<relation>",
        "emergency_contact_name": "<name>",
        "emergency_contact": "<number>"
    }}
    """

    try:
        print("DEBUG: Running Ollama subprocess...")
        result = subprocess.run(
            ["ollama", "run", "llama2"],
            input=prompt,
            text=True,
            capture_output=True
        )

        print("DEBUG: Ollama subprocess completed.")
        structured_output = result.stdout.strip()
        print(f"DEBUG: Full output from Ollama:\n{structured_output[:200]}...")

        try:
            structured_json = json.loads(structured_output)
            print("DEBUG: Successfully parsed JSON from Ollama response.")
            return structured_json
        except json.JSONDecodeError:
            print("ERROR: Output is not valid JSON. Attempting to extract JSON...")
            match = re.search(r"\{.*\}", structured_output, re.DOTALL)
            if match:
                extracted_json = match.group(0)
                return json.loads(extracted_json)
            else:
                raise ValueError("No valid JSON found in the Ollama output.")

    except Exception as e:
        print(f"ERROR: An error occurred: {e}")
        raise

