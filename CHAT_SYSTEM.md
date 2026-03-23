# Chat System - YouTube Analysis Expert

## Overview

Sistem chat dengan knowledge base dari video YouTube yang sudah dianalisis. Chatbot bertindak sebagai **YouTube Analysis Expert** yang dapat menjawab pertanyaan tentang video-video yang telah diproses.

## Features

### Backend Features

1. **Knowledge Base Integration**
   - Semua video yang sudah dianalisis menjadi knowledge base
   - Chatbot dapat mengakses transcript, summary, topics, key points, dan insights
   - Context-aware responses berdasarkan video content

2. **Streaming Responses**
   - Real-time streaming chat responses menggunakan Server-Sent Events (SSE)
   - Progressive message display untuk UX yang lebih baik

3. **Session Management**
   - Persistent chat sessions
   - Message history tracking
   - Automatic session title generation

4. **Referenced Videos**
   - Tracking video mana yang digunakan sebagai context
   - Transparency dalam response generation

### Frontend Features

1. **Clean UI**
   - Minimal design sesuai dengan design system
   - User-friendly chat interface
   - Real-time message streaming

2. **Message Display**
   - User dan assistant messages dengan styling berbeda
   - Referenced videos indicator
   - Loading states

3. **Navigation**
   - Integrated dengan sistem navigasi existing
   - Easy access dari semua pages

## Architecture

### Database Schema

#### `chat_sessions` table
- `id`: UUID (primary key)
- `title`: Text (auto-generated from first message)
- `created_at`: DateTime
- `updated_at`: DateTime

#### `chat_messages` table
- `id`: UUID (primary key)
- `session_id`: UUID (foreign key to chat_sessions)
- `role`: String (user/assistant/system)
- `content`: Text (message content)
- `referenced_jobs`: JSON (list of job IDs used as context)
- `token_usage`: JSON (tracking token usage)
- `created_at`: DateTime

### API Endpoints

#### POST `/api/chat/sessions`
Create new chat session

**Response:**
```json
{
  "id": "uuid",
  "title": null,
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": []
}
```

#### GET `/api/chat/sessions`
List all chat sessions

**Query Parameters:**
- `limit`: Number (default: 50)

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "message_count": 5
  }
]
```

#### GET `/api/chat/sessions/{session_id}`
Get specific chat session with messages

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "string",
      "referenced_jobs": [],
      "created_at": "datetime"
    }
  ]
}
```

#### POST `/api/chat/message/stream`
Send message and stream response

**Request Body:**
```json
{
  "content": "Your message here",
  "session_id": "uuid or null for new session"
}
```

**Response:** Server-Sent Events stream
```
data: {"session_id": "uuid", "message_id": "uuid", "content": "chunk", "done": false}
data: {"session_id": "uuid", "message_id": "uuid", "content": "chunk", "done": false}
data: {"session_id": "uuid", "message_id": "uuid", "content": "", "done": true, "referenced_jobs": ["uuid"]}
```

#### DELETE `/api/chat/sessions/{session_id}`
Delete chat session and all messages

## How It Works

### Knowledge Base Building

1. Setiap video yang selesai dianalisis (status = DONE) otomatis menjadi bagian dari knowledge base
2. ChatService mengambil data dari tabel `jobs` yang memiliki `analysis` data
3. Context building includes:
   - Video URL dan title
   - Summary
   - Topics
   - Key points
   - Transcript excerpt

### Context-Aware Chat

1. User mengirim message
2. ChatService mencari relevant videos dari knowledge base
3. System prompt di-inject dengan video context
4. OpenAI GPT-4o generates response based on context
5. Response di-stream ke frontend
6. Referenced jobs di-track untuk transparency

### System Prompt

Chatbot menggunakan system prompt sebagai YouTube Analysis Expert:

```
You are a YouTube Analysis Expert AI assistant. You have access to a knowledge base of analyzed YouTube videos including their transcripts, summaries, topics, key points, and insights.

Your capabilities:
- Analyze video content and provide insights
- Answer questions about specific videos
- Compare multiple videos
- Identify trends and patterns across videos
- Provide recommendations based on video content
- Explain video topics in detail

Guidelines:
- Always cite specific videos when providing information
- Use video titles and URLs when referencing content
- Be accurate and base your responses on the actual video data
- If information is not in the knowledge base, clearly state that
- Provide timestamp references when available
- Give detailed, helpful responses focused on video analysis
```

## Setup Instructions

### 1. Database Migration

Run the migration to create chat tables:

```bash
cd backend
alembic upgrade head
```

### 2. Start Backend Server

Pastikan backend server running dengan chat router:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

### 4. Access Chat

Navigate to: `http://localhost:3000/chat`

## Usage Examples

### Example 1: Ask about a specific video
**User:** "Can you summarize the video about machine learning?"

**Assistant:** Based on the video "Introduction to Machine Learning" (https://youtube.com/watch?v=...), here's a summary: [provides detailed summary from the analyzed video]

### Example 2: Compare videos
**User:** "What are the differences between the two React tutorial videos?"

**Assistant:** Comparing the videos:
1. "React Hooks Tutorial" focuses on...
2. "React Context API" covers...
[provides detailed comparison]

### Example 3: Find insights
**User:** "What are the common topics across all the programming videos?"

**Assistant:** Analyzing all programming videos in the knowledge base, the common topics are:
- Data structures
- Algorithms
- Best practices
[provides aggregated insights]

## Design System

Chat interface mengikuti clean minimal design:

- **Colors:**
  - User messages: `bg-indigo-600 text-white`
  - Assistant messages: `bg-white border border-gray-200 text-gray-900`
  - Background: `bg-gray-50`

- **Typography:**
  - Headings: `font-semibold text-gray-900`
  - Body: `text-gray-700`

- **Components:**
  - Rounded corners: `rounded-lg`
  - Shadows: `shadow-sm` for cards
  - No gradients, solid colors only

## Future Enhancements

1. **Semantic Search**
   - Implement embedding-based search for better context retrieval
   - Use vector database for similarity search

2. **Multi-Modal Responses**
   - Include frame images in responses
   - Reference specific timestamps with frame previews

3. **Chat History UI**
   - Sidebar with session list
   - Quick access to previous conversations

4. **Export Conversations**
   - Export chat history as markdown
   - Share conversations

5. **Voice Input**
   - Speech-to-text for messages
   - More natural interaction

## Troubleshooting

### Chat not responding
1. Check backend logs for errors
2. Verify OpenAI API key is set
3. Check database connection

### Streaming not working
1. Verify SSE support in browser
2. Check CORS settings
3. Ensure proper content-type headers

### Empty knowledge base
1. Make sure videos are analyzed (status = DONE)
2. Check `jobs` table has analysis data
3. Verify ChatService.get_relevant_videos() returns results

## Technical Details

- **Backend:** FastAPI with async SQLAlchemy
- **Frontend:** Next.js 14 with TypeScript
- **Database:** PostgreSQL
- **AI Model:** OpenAI GPT-4o
- **Streaming:** Server-Sent Events (SSE)
- **Styling:** Tailwind CSS
