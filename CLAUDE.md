# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Backend (FastAPI)
- **Run development server**: `uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload`
- **Install dependencies**: `pip install -r requirements.txt` or `uv pip install --system -r requirements.txt`
- **Build Docker image**: `docker build -t hajimi .`
- **Run with Docker**: `docker run -p 7860:7860 hajimi`

### Frontend (Vue.js)
Both `hajimiUI/` and `page/` directories contain Vue.js applications:
- **Development server**: `npm run dev` (or `yarn dev`)
- **Build for production**: `npm run build`
- **Custom build**: `npm run build:app` (uses build.js script)
- **Preview build**: `npm run preview`

## Project Architecture

### Core Structure
This is a **Gemini API proxy service** that provides OpenAI-compatible API endpoints for Google's Gemini models. The project has three main components:

1. **Backend API** (`app/` directory) - FastAPI application
2. **Dashboard UI** (`hajimiUI/` directory) - Vue.js admin interface  
3. **Public UI** (`page/` directory) - Vue.js public interface

### Backend Architecture (`app/`)
```
app/
├── main.py              # FastAPI app entry point, startup logic
├── api/                 # API route handlers
│   ├── routes.py        # Main OpenAI-compatible endpoints
│   ├── dashboard.py     # Admin dashboard endpoints
│   ├── stream_handlers.py
│   └── nonstream_handlers.py
├── services/            # External service integrations
│   ├── gemini.py        # Google Gemini API client
│   └── OpenAI.py        # OpenAI compatibility layer
├── vertex/              # Google Vertex AI integration
│   ├── main.py          # Vertex AI FastAPI app
│   ├── auth.py          # Authentication
│   ├── credentials_manager.py
│   └── routes/          # Vertex-specific API routes
├── config/              # Configuration management
│   ├── settings.py      # Environment variables and settings
│   ├── persistence.py   # Settings persistence
│   └── safety.py        # Content safety settings
├── utils/               # Utility modules
│   ├── api_key.py       # API key management and rotation
│   ├── cache.py         # Response caching
│   ├── rate_limiting.py # Rate limiting
│   ├── auth.py          # Authentication utilities
│   └── logging.py       # Logging configuration
└── models/
    └── schemas.py       # Pydantic models for API
```

### Key Features
- **API Key Rotation**: Automatically manages multiple Gemini API keys with failover
- **Response Caching**: Caches responses for identical requests to reduce API calls
- **Rate Limiting**: Configurable per-minute and per-IP limits
- **Fake Streaming**: Provides streaming-like responses for better client compatibility
- **Concurrent Requests**: Supports concurrent requests with caching for faster responses
- **Vertex AI Support**: Alternative Google Vertex AI integration
- **Web Dashboard**: Vue.js admin interface for configuration and monitoring

### Environment Configuration
Main settings are configured via environment variables in `app/config/settings.py`:
- `HOST`: Server listen address (default: "0.0.0.0")
- `PORT`: Server listen port (default: 7860)
- `GEMINI_API_BASE_URL`: Gemini API upstream address (default: "https://generativelanguage.googleapis.com")
- `VERTEX_API_BASE_URL`: Vertex AI API upstream address (default: "https://aiplatform.googleapis.com")
- `HTTP_PROXY`: HTTP proxy address (e.g., "http://proxy.example.com:8080")
- `HTTPS_PROXY`: HTTPS proxy address (e.g., "https://user:pass@proxy.example.com:8080")
- `SOCKS_PROXY`: SOCKS5 proxy address (e.g., "socks5://user:pass@proxy.example.com:1080")
- `ALL_PROXY`: Fallback proxy for all protocols
- `GEMINI_API_KEYS`: Comma-separated Gemini API keys
- `PASSWORD`: API access password (default: "123")
- `FAKE_STREAMING`: Enable fake streaming (default: true)
- `CONCURRENT_REQUESTS`: Number of concurrent requests (default: 1)
- `ENABLE_VERTEX`: Enable Vertex AI mode (default: false)
- `MAX_REQUESTS_PER_MINUTE`: Rate limiting (default: 30)
- `NATIVE_API_ENCRYPT_FULL`: Enable encrypt-full mode for native Gemini API (default: false)

#### Proxy Configuration
The service supports HTTP, HTTPS, and SOCKS5 proxies for upstream requests:
- **HTTP Proxy**: `HTTP_PROXY=http://proxy.example.com:8080`
- **HTTP Proxy with auth**: `HTTP_PROXY=http://user:pass@proxy.example.com:8080`
- **HTTPS Proxy**: `HTTPS_PROXY=https://proxy.example.com:8080`
- **HTTPS Proxy with auth**: `HTTPS_PROXY=https://user:pass@proxy.example.com:8080`
- **SOCKS5 Proxy**: `SOCKS_PROXY=socks5://proxy.example.com:1080`
- **SOCKS5 Proxy with auth**: `SOCKS_PROXY=socks5://user:pass@proxy.example.com:1080`
- **All protocols**: `ALL_PROXY=http://proxy.example.com:8080` (fallback for all protocols)

Proxy priority: Protocol-specific proxy (HTTP_PROXY/HTTPS_PROXY) > SOCKS_PROXY > ALL_PROXY

### API Endpoints
The service provides OpenAI-compatible endpoints:
- `POST /v1/chat/completions` - Chat completions (streaming and non-streaming)
- `GET /v1/models` - List available models
- Dashboard endpoints for configuration and monitoring

### Deployment
- **Local**: Run with uvicorn directly
- **Docker**: Uses Python 3.12-slim with uv for fast dependency installation
- **Cloud**: Supports deployment on Hugging Face Spaces, Render, Zeabur, etc.
- Default port: 7860 (standard for Hugging Face Spaces)

## Testing
No formal test suite is configured. Manual testing should focus on:
- API endpoint functionality with various Gemini models
- Frontend dashboard configuration changes
- Docker container builds and deployments
- API key rotation and failover scenarios