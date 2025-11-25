import os
import base64
import io
import csv
import time
import random
from flask import Flask, request, jsonify, send_file
from pdf2image import convert_from_bytes
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Free models on OpenRouter
VISION_MODEL = os.getenv('VISION_MODEL', 'google/gemini-flash-1.5-8b')  # Free vision model
CHAT_MODEL = os.getenv('CHAT_MODEL', 'google/gemini-flash-1.5-8b')  # Free chat model


def make_api_request_with_retry(url, headers, json_data, max_retries=5):
    """Make API request with exponential backoff retry for 429 errors."""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)
            
            if response.status_code == 429:
                print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries}")
                # Default wait 5s, or use Retry-After header if available
                wait_time = 5
                if 'Retry-After' in response.headers:
                    try:
                        wait_time = int(response.headers['Retry-After'])
                    except ValueError:
                        pass
                
                # Add exponential backoff + jitter
                sleep_time = wait_time * (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                continue
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Max retries reached. Final error: {e}")
                raise
            
            print(f"Request error: {e}. Retrying...")
            time.sleep(2 ** attempt + random.uniform(0.5, 1.5))
            
    raise Exception("Max retries reached")


def pdf_to_images(pdf_bytes):
    """Convert PDF bytes to list of PIL images."""
    images = convert_from_bytes(pdf_bytes, dpi=100)
    return images


def image_to_base64(image):
    """Convert PIL image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def ocr_with_openrouter(images):
    """Use OpenRouter vision model to extract text from images."""
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'PDF OCR Service'
    }

    all_text = []

    for idx, image in enumerate(images):
        base64_image = image_to_base64(image)

        payload = {
            'model': VISION_MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Extract all text from this image. Return only the text content, nothing else.'
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/png;base64,{base64_image}'
                            }
                        }
                    ]
                }
            ]
        }

        response = make_api_request_with_retry(OPENROUTER_API_URL, headers=headers, json_data=payload)
        
        result = response.json()
        text = result['choices'][0]['message']['content']
        all_text.append(f"--- Page {idx + 1} ---\n{text}")

    return "\n\n".join(all_text)


def text_to_csv(text):
    """Use OpenRouter chat model to convert text to CSV format."""
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'PDF OCR Service'
    }

    payload = {
        'model': CHAT_MODEL,
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant that converts text data into CSV format. Analyze the text and identify tabular data, lists, or structured information, then output it as properly formatted CSV. Return ONLY the CSV data with no markdown formatting, no code blocks, no explanations.'
            },
            {
                'role': 'user',
                'content': f'Convert the following text into a useful CSV format. Identify patterns and structure the data logically:\n\n{text}'
            }
        ]
    }

    response = make_api_request_with_retry(OPENROUTER_API_URL, headers=headers, json_data=payload)
    
    result = response.json()
    csv_content = result['choices'][0]['message']['content']

    # Clean up any markdown code blocks if present
    if '```' in csv_content:
        csv_content = csv_content.split('```')[1]
        if csv_content.startswith('csv'):
            csv_content = csv_content[3:]
        csv_content = csv_content.strip()

    return csv_content


@app.route('/pdf-to-csv', methods=['POST'])
def pdf_to_csv():
    """
    POST endpoint that accepts a PDF file, OCRs it, and returns CSV.

    Usage:
        curl -X POST -F "file=@document.pdf" http://localhost:5000/pdf-to-csv -o output.csv
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        # Read PDF bytes
        pdf_bytes = file.read()

        # Step 1: Convert PDF to images
        images = pdf_to_images(pdf_bytes)

        # Step 2: OCR with OpenRouter vision model
        extracted_text = ocr_with_openrouter(images)

        # Step 3: Convert text to CSV using OpenRouter chat model
        csv_content = text_to_csv(extracted_text)

        # Return CSV file
        csv_bytes = io.BytesIO(csv_content.encode('utf-8'))
        csv_bytes.seek(0)

        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='output.csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'PDF OCR to CSV'})


if __name__ == '__main__':
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set in environment variables!")
        print("Please create a .env file with your OpenRouter API key.")
        exit(1)

    app.run(debug=True, host='0.0.0.0', port=5000)
