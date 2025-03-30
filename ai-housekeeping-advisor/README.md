# AI Housekeeping Advisor Bot

A web application that provides practical housekeeping advice based on uploaded images of home environments.

## Project Overview

This application allows users to upload images of their home environment (kitchen, bathroom, bedroom, etc.) and receive AI-generated housekeeping advice based on the image content. The application uses Google Cloud Vision API to analyze the images and Google Vertex AI Gemini API to generate contextual advice.

## Architecture

The application follows a three-tier architecture:

### Backend (Python with FastAPI)

Three separate microservices:
1. **API Gateway**: Handles HTTP requests from the frontend, orchestrates calls to other services
2. **Image Processor**: Processes images using Google Cloud Vision API
3. **Message Generator**: Generates advice using Google Vertex AI Gemini API

### Frontend (React with TypeScript)

A simple, functional UI that allows users to:
- Upload images of their home environment
- Provide optional context for the advice
- View the generated housekeeping advice

## Setup and Installation

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- Google Cloud SDK
- Google Cloud Project with Vision API and Vertex AI API enabled

### Backend Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies for each service:
   ```bash
   cd api-gateway
   pip install -r requirements.txt
   cd ../image-processor
   pip install -r requirements.txt
   cd ../message-generator
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the `backend` directory
   - Add the following variables:
     ```
     GOOGLE_CLOUD_PROJECT=your-project-id
     IMAGE_PROCESSOR_URL=http://localhost:8081
     MESSAGE_GENERATOR_URL=http://localhost:8082
     ```

4. Run the backend services locally:
   ```bash
   cd backend
   python run_local.py
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables:
   - Create a `.env` file in the `frontend` directory
   - Add the following variables:
     ```
     VITE_API_URL=http://localhost:8080
     ```

3. Run the frontend development server:
   ```bash
   npm run dev
   ```

4. Access the application at `http://localhost:3000`

## Deployment

### Backend Deployment (Google Cloud Functions)

1. Deploy the API Gateway:
   ```bash
   cd backend/api-gateway
   gcloud functions deploy api-gateway --runtime python39 --trigger-http --allow-unauthenticated
   ```

2. Deploy the Image Processor:
   ```bash
   cd backend/image-processor
   gcloud functions deploy image-processor --runtime python39 --trigger-http --allow-unauthenticated
   ```

3. Deploy the Message Generator:
   ```bash
   cd backend/message-generator
   gcloud functions deploy message-generator --runtime python39 --trigger-http --allow-unauthenticated
   ```

### Frontend Deployment

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Deploy to a static hosting service (e.g., Firebase Hosting, Netlify, Vercel)

## Usage

1. Open the application in a web browser
2. Click "Select Image" to upload an image of your home environment
3. Optionally, provide additional context in the text area
4. Click "Get Advice" to process the image and receive housekeeping advice
5. View the generated advice and image analysis results

## Development Guidelines

- **Backend**: Follow FastAPI best practices, maintain separation of concerns
- **Frontend**: Use functional components and React Hooks, keep UI simple and functional
- **Error Handling**: Implement robust error handling on both frontend and backend
- **Testing**: Write unit tests for backend functions and frontend components

## License

This project is licensed under the MIT License - see the LICENSE file for details.
