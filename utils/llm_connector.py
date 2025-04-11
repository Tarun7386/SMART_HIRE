import ollama
import json
import re

def query_llm(prompt, model_name="mistral", max_retries=3):
    """Query the Ollama LLM with retries"""
    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error querying LLM (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
            else:
                print(f"Failed to query LLM after {max_retries} attempts: {e}")
                return f"Error: Unable to get response from the language model after {max_retries} attempts."

def extract_json_from_llm_response(response):
    """Extract JSON data from an LLM response"""
    # Look for JSON inside code blocks
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # If no code blocks, try to find JSON-like structure directly
        json_str = response
    
    # Try to parse the JSON
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract object notation
        try:
            # Remove comments if any
            cleaned = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
            # Replace single quotes with double quotes
            cleaned = cleaned.replace("'", '"')
            # Try parsing again
            data = json.loads(cleaned)
            return data
        except:
            # Return None if all parsing attempts fail
            return None
