import boto3
import json

# Extracts text and structured fields from an image or PDF using AWS Textract
def extract_text_and_fields(file_path):
    textract = boto3.client('textract')

    with open(file_path, 'rb') as document:
        response = textract.analyze_document(
            Document={'Bytes': document.read()},
            FeatureTypes=["FORMS"] 
        )

    if "Blocks" not in response or not response["Blocks"]:
        raise ValueError("Textract response does not contain valid Blocks data.")

    raw_text = ""
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            raw_text += block.get('Text', '') + "\n"

    # Extract structured fields (key-value pairs)
    key_value_pairs = {}
    key_blocks = {block['Id']: block for block in response['Blocks']
                  if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', [])}
    value_blocks = {block['Id']: block for block in response['Blocks']
                    if block['BlockType'] == 'KEY_VALUE_SET' and 'VALUE' in block.get('EntityTypes', [])}

    # Match keys to values
    for key_id, key_block in key_blocks.items():
        key_text = ""
        if "Relationships" not in key_block:
            continue

        # Extract key text
        for relationship in key_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                key_text = " ".join([
                    block.get('Text', '')
                    for block in response['Blocks']
                    if block['Id'] in relationship.get('Ids', [])
                ])

        value_text = ""
        # Extract value text
        value_ids = [
            rel['Id'] for rel in key_block['Relationships']
            if rel['Type'] == 'VALUE' and 'Id' in rel
        ]
        for value_id in value_ids:
            if value_id in value_blocks:
                value_text += " ".join([
                    block.get('Text', '')
                    for block in response['Blocks']
                    if block['Id'] in value_blocks[value_id].get('Relationships', {}).get('Ids', [])
                ])

        if key_text:
            key_value_pairs[key_text.strip().lower()] = value_text.strip()

    if "name" in key_value_pairs:
        name_parts = key_value_pairs["name"].split(" ", 1)
        key_value_pairs["first_name"] = name_parts[0] if len(name_parts) > 0 else "Not available"
        key_value_pairs["last_name"] = name_parts[1] if len(name_parts) > 1 else "Not available"

    return {
        "raw_text": raw_text.strip(),
        "key_value_pairs": key_value_pairs
    }
