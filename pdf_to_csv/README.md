# PDF OCR to CSV Service

A Flask-based web service that converts PDF documents to CSV files using AI-powered OCR. The service uses free OpenRouter models to extract text from PDFs and intelligently structure it into CSV format.

## Features

- Upload PDF files via POST endpoint
- OCR extraction using free OpenRouter vision models
- Intelligent CSV conversion using free OpenRouter chat models
- Easy configuration via environment variables
- Docker support for reproducible deployments
- Health check endpoint

## Prerequisites

### Option 1: Docker (Recommended - No Manual Setup Required!)
- Docker and Docker Compose
- OpenRouter API key (free at https://openrouter.ai/keys)

### Option 2: Manual Setup
- Python 3.8 or higher
- Poppler (for PDF processing)
- OpenRouter API key (free at https://openrouter.ai/keys)

### Installing Poppler (Manual Setup Only)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download from: http://blog.alivate.com.au/poppler-windows/

## Setup

### Option 1: Docker Setup (Easiest!)

1. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_api_key_here
```

Get a free API key at: https://openrouter.ai/keys

2. **Build and run with Docker Compose:**
```bash
docker-compose up -d
```

That's it! The service will be running at `http://localhost:5000`

**Docker Commands:**
```bash
# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Check service health
curl http://localhost:5000/health
```

### Option 2: Manual Setup

1. **Clone or navigate to the project directory:**
```bash
cd fiverr_automation
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_api_key_here
```

Get a free API key at: https://openrouter.ai/keys

5. **Run the application:**
```bash
python app.py
```

The server will start at `http://localhost:5000`

## Usage

### Convert PDF to CSV

**Using curl:**
```bash
curl -X POST -F "file=@your_document.pdf" http://localhost:5000/pdf-to-csv -o output.csv
```

**Using Python:**
```python
import requests

with open('your_document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/pdf-to-csv', files=files)

    with open('output.csv', 'wb') as output:
        output.write(response.content)
```

**Using JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('file', pdfFile);

fetch('http://localhost:5000/pdf-to-csv', {
    method: 'POST',
    body: formData
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.csv';
    a.click();
});
```

### Health Check

```bash
curl http://localhost:5000/health
```

## Configuration

All configuration is done via the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `VISION_MODEL` | `google/gemini-flash-1.5-8b` | Vision model for OCR |
| `CHAT_MODEL` | `google/gemini-flash-1.5-8b` | Chat model for CSV conversion |

### Alternative Free Models

You can try these free models in your `.env` file:

```bash
# For vision (OCR):
VISION_MODEL=google/gemini-flash-1.5-8b
VISION_MODEL=google/gemini-flash-1.5

# For chat (CSV conversion):
CHAT_MODEL=google/gemini-flash-1.5-8b
CHAT_MODEL=google/gemini-2.0-flash-exp:free
CHAT_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

Check https://openrouter.ai/models for the latest free models.

## API Endpoints

### POST /pdf-to-csv

Converts a PDF file to CSV format.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: PDF file with key `file`

**Response:**
- Success: CSV file (200 OK)
- Error: JSON with error message (400 or 500)

**Example Response (Error):**
```json
{
    "error": "No file provided"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "PDF OCR to CSV"
}
```

## How It Works

1. **PDF Upload**: Client sends PDF file to `/pdf-to-csv` endpoint
2. **PDF to Images**: PDF is converted to images (one per page)
3. **OCR**: Each image is sent to OpenRouter's vision model to extract text
4. **CSV Conversion**: Extracted text is sent to OpenRouter's chat model with instructions to structure it as CSV
5. **Response**: CSV file is returned to the client

## Troubleshooting

**"poppler not found" error:**
- Install Poppler following the prerequisites section above

**"OPENROUTER_API_KEY not set" error:**
- Make sure you've created a `.env` file with your API key
- Verify the key is valid at https://openrouter.ai/keys

**Poor OCR quality:**
- Try increasing DPI in `pdf_to_images()` function (default is 200)
- Use a different vision model in `.env`

**Poor CSV structure:**
- The chat model tries to intelligently detect structure
- You may need to adjust the prompt in `text_to_csv()` function for specific document types
- Try a different chat model in `.env`

## Production Deployment

### Docker Deployment (Recommended)

The Docker setup is production-ready. For production use:

1. **Use Docker Compose with custom configuration:**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  pdf-ocr-service:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

2. **Run in production mode:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment with Gunicorn

For production use without Docker, consider:

1. Use a production WSGI server (gunicorn, uWSGI)
2. Add authentication/rate limiting
3. Implement file size limits
4. Add request logging
5. Use environment-based configuration
6. Set up proper error monitoring

**Example with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

This project is open source and available for use.
