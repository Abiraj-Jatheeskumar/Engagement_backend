# Engagement Classifier - Backend

FastAPI backend for Real-Time Engagement Monitoring & Adaptive Question Delivery System.

## Features

- **Question Generation**: Extract text from PDF/PPTX and generate questions (mock ML)
- **Engagement Classification**: Rules-based classification ready for ML integration
- **Adaptive Engine**: Automatically adjusts question frequency based on engagement
- **Zoom Integration**: Live participant tracking from Zoom meetings
- **Real-Time WebSockets**: Instant communication with frontend
- **PostgreSQL Database**: Full CRUD operations with SQLAlchemy ORM

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Zoom API credentials (optional)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/env.example backend/.env
# Edit backend/.env with your credentials

# Initialize database
python backend/setup_db.py

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Questions
- `POST /api/questions/upload-slides` - Upload and generate questions
- `GET /api/questions` - List all questions
- `POST /api/questions` - Create question manually

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}/dashboard` - Get dashboard data
- `POST /api/sessions/{id}/start` - Start session
- `POST /api/sessions/{id}/stop` - Stop session

### Engagement
- `POST /api/engagement/log` - Log engagement
- `GET /api/engagement/session/{id}/stats` - Get stats

### Responses
- `POST /api/responses/` - Submit response
- `GET /api/responses/session/{id}` - Get responses

### Zoom
- `GET /api/zoom/meetings/{id}/participants` - Get participants
- `POST /api/zoom/session/{id}/sync-participants` - Sync

### WebSockets
- `ws://localhost:8000/api/students/{id}/session/{id}/ws` - Student
- `ws://localhost:8000/api/sessions/{id}/ws` - Instructor

## Project Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── api/                       # REST API endpoints
├── services/                  # Business logic
├── database/                  # Models and schemas
├── engagement_classifier/     # ML-ready classifier
├── zoom_integrator/           # Zoom API integration
├── websocket/                 # WebSocket handlers
└── requirements.txt           # Dependencies
```

## Mock ML Components

- **Question Generator**: `services/question_generator.py::generate_questions_mock()`
- **Engagement Classifier**: Rules-based (ready for deep learning)

## Configuration

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/engagement_db
ZOOM_API_KEY=your_key
ZOOM_API_SECRET=your_secret
ZOOM_ACCOUNT_ID=your_account_id
DEBUG=True
```

## License

MIT

