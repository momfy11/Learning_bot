# 📚 Learning Bot

A chatbot learning platform that guides users to find answers rather than giving direct responses. Built with React, FastAPI, and RAG (Retrieval Augmented Generation).

## 🎯 Project Overview

**Learning Bot** is an educational chatbot that helps students learn by guiding them to resources rather than providing direct answers. When you ask a question, the bot:

- Provides **hints** about the topic
- Tells you **where to find the answer** (book, chapter, page)
- Encourages **independent learning** and exploration

This approach promotes deeper understanding and retention compared to simply receiving answers.

## ✨ Features

### Core Features
- 💬 **Guided Chat** - Ask questions and receive learning guidance, not direct answers
- 📚 **RAG-Powered** - Upload books/documents and get specific page/chapter references
- 🎤 **Voice Chat** - Speak your questions and listen to responses
- 👤 **User Accounts** - Register, login, and manage your profile
- 💾 **Chat History** - All conversations are saved and can be revisited

### Learning Profiles
- Create custom learning profiles (like ChatGPT's custom instructions)
- Choose your learning style:
  - **Guided** - Step-by-step hints
  - **Socratic** - Learn through questions
  - **Exploratory** - Minimal guidance
- Set difficulty level: Beginner, Intermediate, Advanced

### Document Management
- Upload PDF, TXT, or EPUB files
- Documents are chunked and embedded for semantic search
- The bot references exact pages and chapters in responses

### Privacy-Focused
- Questions are stored **separately** from user details
- Anonymized questions can be used for future training
- No personal information leaks into training data

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI library
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client
- **Web Speech API** - Voice input/output (browser native)

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database (with asyncpg driver for async support)
- **ChromaDB** - Vector database for RAG embeddings
- **Sentence Transformers** - Text embeddings (all-MiniLM-L6-v2)
- **Mistral AI** - LLM API for generating personalized guidance responses

## 📁 Project Structure

```
Learning_bot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py          # User & ChatProfile
│   │   │   ├── chat.py          # Conversation, Message, TrainingQuestion
│   │   │   └── document.py      # Document & DocumentChunk
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── chat.py          # Chat functionality
│   │   │   ├── documents.py     # Document upload
│   │   │   ├── profiles.py      # Chat profiles
│   │   │   └── voice.py         # Voice endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── auth_service.py  # JWT & password handling
│   │   │   ├── llm_service.py   # Mistral AI integration
│   │   │   └── rag_service.py   # RAG functionality
│   │   └── utils/               # Helper functions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   ├── hooks/               # Custom hooks (voice)
│   │   ├── context/             # Auth context
│   │   ├── App.jsx              # Main app
│   │   └── main.jsx             # Entry point
│   ├── package.json
│   └── tailwind.config.js
├── .env.example                 # Environment variables template
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** - Backend
- **Node.js 18+** - Frontend
- **Mistral AI API Key** - Get free at https://console.mistral.ai/

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Learning_bot
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Edit .env and add your Mistral API key
# MISTRAL_API_KEY=your-api-key-here
```

### 3. Frontend Setup

```bash
# Navigate to frontend (new terminal)
cd frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Start Backend (Terminal 1):**
```bash
cd backend
# Make sure venv is activated
uvicorn app.main:app --reload
```
Backend runs at: http://localhost:8000

**Start Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
Frontend runs at: http://localhost:5173

### 5. Access the Application
1. Open http://localhost:5173 in your browser
2. Register a new account
3. Upload some learning materials (PDF, TXT, EPUB)
4. Start asking questions!

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get token |
| `/api/auth/me` | GET | Get current user |
| `/api/chat/send` | POST | Send message, get guidance |
| `/api/chat/conversations` | GET | List conversations |
| `/api/documents/upload` | POST | Upload document |
| `/api/documents/` | GET | List documents |
| `/api/profiles/` | GET/POST | Manage profiles |
| `/api/voice/transcript` | POST | Process voice input |

## ⚙️ Configuration

All configuration is done via environment variables in the `.env` file. Copy `.env.example` to `.env` and fill in your values:

```env
# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/learning_bot

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Mistral AI (required for chat guidance)
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=mistral-small-2506

# RAG Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_CONTEXT_TOKENS=2000
TOP_K_RESULTS=3

# File Upload
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,txt,epub
UPLOAD_DIR=uploads

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

### Database Setup (PostgreSQL)

**Local Development with Docker:**
```bash
docker run --name learning_bot_db \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=learning_bot \
  -p 5432:5432 \
  -d postgres:15-alpine
```

**Or use Docker Compose (recommended):**
```bash
docker compose up -d
```

## 🎤 Voice Feature

The voice feature uses the browser's native **Web Speech API**:

- **Speech Recognition**: Converts voice to text
- **Speech Synthesis**: Reads responses aloud

No additional setup needed - it works in modern browsers (Chrome, Edge, Safari).

**Usage:**
1. Click the microphone button
2. Speak your question
3. The bot's response will be read aloud automatically

## 🧠 How RAG Works

1. **Upload**: Upload learning materials (books, PDFs)
2. **Chunk**: Documents are split into smaller pieces
3. **Embed**: Each chunk is converted to a vector (number array)
4. **Store**: Vectors are stored in ChromaDB
5. **Search**: When you ask a question, similar chunks are found
6. **Reference**: The bot tells you exactly where to find the answer

## 🔒 Security Notes

- Passwords are hashed with bcrypt
- JWT tokens for authentication
- CORS configured for frontend origin
- File upload validation (type, size)
- SQL injection prevented by SQLAlchemy ORM

## 🧪 Testing

```bash
# Backend tests (from backend directory)
pytest

# Frontend (from frontend directory)
npm run lint
```

## 📝 Development Notes

### Adding New Features
1. Backend: Add router in `app/routers/`
2. Add service logic in `app/services/`
3. Define schemas in `app/schemas/`
4. Frontend: Add service in `src/services/`
5. Add component/page as needed

### Database Changes

The database schema is automatically created on startup. For changes:
1. Modify models in `app/models/`
2. Use Alembic for migrations (recommended for production)

**Reset Database (development only):**
```bash
# Drop all tables (WARNING: loses all data)
docker compose down -v
docker compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for educational purposes as part of a school project.

## 🙏 Acknowledgments

- **Mistral AI** for the free LLM API
- **ChromaDB** for simple vector storage
- **FastAPI** for the excellent Python framework
- **Tailwind CSS** for beautiful styling

---

**Happy Learning! 📚**
