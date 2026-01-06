# Competitor Analysis Tool

A simple competitor analysis tool based on LLM and search API to discover and analyze competitors in specified domains.

## Features

- LLM-powered search query optimization
- Web search via Anspire API
- Intelligent competitor information extraction
- Clean React frontend interface

## Project Structure

```
prototype/
├── backend/              # Backend code
│   ├── api/              # API entry point
│   │   └── main.py
│   ├── agent/            # Agent module
│   │   └── competitor_agent.py
│   ├── llm/              # LLM client module
│   │   └── client.py
│   ├── tools/            # Tools module
│   │   └── anspire_search.py
│   └── requirements.txt
├── frontend/             # Frontend code
│   ├── src/
│   │   ├── App.tsx
│   │   └── styles/
│   └── package.json
├── .env.example          # Environment variables example
└── README.md
```

## Tech Stack

- **Backend**: Python, FastAPI, OpenAI SDK, Requests, Loguru
- **Frontend**: React, TypeScript, Vite, TailwindCSS

## Quick Start

### Backend

```bash
# Install dependencies
cd prototype
pip install -r backend/requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and fill in your API keys

# Start backend server
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open browser and visit: `http://localhost:8888`

## Environment Variables

```env
# Anspire Search API
ANSPIRE_API_KEY=your_anspire_api_key

# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=your_llm_base_url
LLM_MODEL=gpt-4
```

## Usage

1. Enter the analysis domain (e.g., "AI Education")
2. Enter the product name (e.g., "My AI Assistant")
3. Click "Start Analysis" button
4. Wait for analysis to complete and view competitor list

## TODO List

### High Priority
- [ ] Add user authentication
- [ ] Add analysis history storage
- [ ] Support multiple search engines (Bocha, Tavily, etc.)
- [ ] Add rate limiting for API calls

### Medium Priority
- [ ] Add competitor comparison feature
- [ ] Export analysis report (PDF/Word)
- [ ] Add data visualization (charts, graphs)
- [ ] Support batch analysis
- [ ] Add caching mechanism for search results

### Low Priority
- [ ] Add dark mode support
- [ ] Multi-language support (i18n)
- [ ] Add unit tests and integration tests
- [ ] Docker containerization
- [ ] CI/CD pipeline setup

### Future Enhancements
- [ ] Knowledge graph integration
- [ ] Real-time market trend analysis
- [ ] Email notification for completed analysis
- [ ] Team collaboration features
- [ ] API documentation (Swagger/OpenAPI)

## License

MIT
