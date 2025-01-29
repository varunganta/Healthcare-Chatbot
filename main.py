import json
import re
from textract import extract_text_and_fields  # Step 1: Extract data
from ollama import process_with_ollama  # Step 2: Further refine data locally


# Validation Functions
def is_valid_date(date_str):
    try:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", date_str):
            return False
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_email(email_str):
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email_str) is not None


def is_valid_phone_number(phone_str):
    return re.fullmatch(r"\d{10}", phone_str) is not None

# Interactively collects missing information from the user, validating input where necessary
def chatbot_collect_additional_info(missing_fields):
    user_data = {}
    print("\nLet's gather the missing information step-by-step.")

    for field in missing_fields:
        attempts = 3
        while attempts > 0:
            user_input = input(f"Please enter {field['name']}: ").strip()
            if field["validation"](user_input):
                user_data[field["key"]] = user_input
                print(f"✅ {field['name']} saved.\n")
                break
            else:
                print(f"❌ Invalid input for {field['name']}. Please try again.")
                attempts -= 1

        if attempts == 0:
            print(f"⚠️ You have exhausted all attempts. Leaving {field['name']} blank.\n")
            user_data[field["key"]] = ""

    return user_data

# Calling methods to process document
def process_document(file_path):
    try:
        print("Extracting data using AWS Textract...")
        extracted_data = extract_text_and_fields(file_path)

        print("Processing data locally using Ollama...")
        refined_data = process_with_ollama(extracted_data)

        print("Processing complete!")
        return refined_data

    except Exception as e:
        print(f"Error during processing: {e}")
        return None

# Identifying missing fields
def identify_missing_fields(data):
    fields = [
        {"name": "Policyholder's First Name", "key": "first_name", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Policyholder's Last Name", "key": "last_name", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Policy Number", "key": "policy_number", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Date of Birth (YYYY-MM-DD)", "key": "dob", "validation": is_valid_date},
        {"name": "Mobile Number", "key": "mobile_number", "validation": is_valid_phone_number},
        {"name": "Email", "key": "email", "validation": is_valid_email},
        {"name": "Nationality", "key": "nationality", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Gender", "key": "gender", "validation": lambda x: x.strip().lower() in ["male", "female", "other"]},
        {"name": "Visa Type", "key": "visa_type", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Doctor's Name", "key": "doctor", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Emergency Contact Relation", "key": "emergency_contact_relation", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Emergency Contact Name", "key": "emergency_contact_name", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Emergency Contact", "key": "emergency_contact", "validation": is_valid_phone_number},
        {"name": "Address", "key": "address", "validation": lambda x: len(x.strip()) > 0},
        {"name": "Insurance Status", "key": "insurance_status", "validation": lambda x: x.strip().lower() in ["active", "inactive"]},
        {"name": "Policy Start Date (YYYY-MM-DD)", "key": "policy_start_date", "validation": is_valid_date},
        {"name": "Policy End Date (YYYY-MM-DD)", "key": "policy_end_date", "validation": is_valid_date},
    ]

    missing_fields = []
    for field in fields:
        value = data.get(field["key"])
        if not value or value.lower() == "not available" or value.startswith("<"):
            missing_fields.append(field)

    return missing_fields

# Mimics chatbot by mapping expected key words in queries to responses
def policy_query_chatbot(policy_data):
    print("\nChatbot: You can now ask questions about your health insurance policy.")
    print("Type 'exit' to end the conversation.\n")

    while True:
        user_query = input("You: ").strip().lower()
        if user_query in ["exit", "quit"]:
            print("Chatbot: Thank you! Have a great day!")
            break

        # Some mapped queries
        if "policy number" in user_query:
            print(f"Chatbot: Your policy number is {policy_data.get('policy_number', 'Not available')}.")
        elif "policyholder" in user_query or "name" in user_query:
            print(f"Chatbot: The policyholder is {policy_data.get('first_name', 'Unknown')} {policy_data.get('last_name', '')}.")
        elif "expire" in user_query or "end date" in user_query:
            print(f"Chatbot: Your policy expires on {policy_data.get('policy_end_date', 'Not available')}.")
        elif "copay" in user_query:
            copay_details = policy_data.get("copay_details", {})
            consultation = copay_details.get("consultation", "Not specified")
            pharma = copay_details.get("pharma", "Not specified")
            physio = copay_details.get("physio", "Not specified")
            print(f"Chatbot: Copay details:\n  - Consultation: {consultation}\n  - Pharma: {pharma}\n  - Physio: {physio}")
        elif "active" in user_query or "status" in user_query:
            print(f"Chatbot: Your insurance status is {policy_data.get('insurance_status', 'Not specified')}.")
        elif "emergency contact" in user_query:
            relation = policy_data.get("emergency_contact_relation", "Not specified")
            name = policy_data.get("emergency_contact_name", "Not specified")
            number = policy_data.get("emergency_contact", "Not specified")
            print(f"Chatbot: Emergency Contact:\n  - Relation: {relation}\n  - Name: {name}\n  - Contact Number: {number}")
        elif "doctor" in user_query:
            print(f"Chatbot: Your assigned doctor is {policy_data.get('doctor', 'Not specified')}.")
        else:
            print("Chatbot: I'm sorry, I couldn't understand your question. Please try again!")


if __name__ == "__main__":
    print("Step 1: Processing the document...")
    file_path = "Example_Insurance_Policy.pdf"
    processed_data = process_document(file_path)

    if processed_data:
        print("\nStep 2: Identifying missing fields...")
        missing_fields = identify_missing_fields(processed_data)

        if missing_fields:
            print(f"⚠️ Missing fields detected: {[field['name'] for field in missing_fields]}")
            print("\nStep 3: Gathering missing information via chatbot...")
            additional_info = chatbot_collect_additional_info(missing_fields)

            processed_data.update(additional_info)

        print("\nStep 4: Starting the query chatbot...")
        policy_query_chatbot(processed_data)

        output_file = "output.json"
        with open(output_file, "w") as f:
            json.dump(processed_data, f, indent=4)

        print(f"\nFinal validated output saved to {output_file}")

