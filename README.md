# Customer Service Chatbot - Production Ready

A production-ready customer service chatbot built with LangChain, FastAPI, and Streamlit. Features include conversation memory, RAG (Retrieval-Augmented Generation), API endpoints, and a user-friendly interface.

## Features

✨ **Core Capabilities**
- 💬 Natural conversation with memory
- 📚 Knowledge base integration (RAG)
- 🔄 Session management
- 🌐 RESTful API
- 🎨 Interactive web UI (Streamlit)
- 🔒 API authentication & rate limiting
- 📊 Comprehensive logging
- 🐳 Docker support

## Architecture

```
customer_service_bot/
├── main.py                    # FastAPI application
├── chatbot.py                 # Core chatbot logic
├── config.py                  # Configuration management
├── streamlit_app.py          # Streamlit UI
├── build_knowledge_base.py   # Knowledge base builder
├── test_chatbot.py           # Test suite
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose setup
├── .env.example              # Environment template
└── data/
    ├── knowledge_base/       # Source documents
    └── vectorstore/          # Vector embeddings
```

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key or Anthropic API key
- Docker (optional)

### Installation

1. **Clone and navigate to the project:**
```bash
cd customer_service_bot
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. **Build knowledge base:**
```bash
python build_knowledge_base.py build --docs-dir ./data/knowledge_base
```

6. **Run the application:**

**Option A: API Server**
```bash
python main.py
# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Option B: Streamlit UI**
```bash
streamlit run streamlit_app.py
# UI available at http://localhost:8501
```

**Option C: Docker Compose (Both)**
```bash
docker-compose up -d
# API at http://localhost:8000
# UI at http://localhost:8501
```

## Configuration

### Environment Variables

Edit `.env` file with your configuration:

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4-turbo-preview

# Or use Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
MODEL_NAME=claude-3-sonnet-20240229

# Business Info
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@yourcompany.com
BUSINESS_HOURS=Monday-Friday, 9 AM - 5 PM EST
```

### Supported LLM Providers

**OpenAI:**
- `gpt-4-turbo-preview`
- `gpt-4`
- `gpt-3.5-turbo`

**Anthropic:**
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

## Usage

### API Endpoints

#### Send a Message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your business hours?",
    "session_id": "user-123"
  }'
```

#### Get Conversation History
```bash
curl "http://localhost:8000/conversation/user-123"
```

#### Clear Conversation
```bash
curl -X DELETE "http://localhost:8000/conversation/user-123"
```

### Python Client Example

```python
import requests

# Send a message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "How can I track my order?",
        "session_id": "customer-456"
    }
)

result = response.json()
print(f"Bot: {result['response']}")
print(f"Session: {result['session_id']}")
```

### Knowledge Base Management

#### Add Documents

1. Place your documents in `data/knowledge_base/`:
   - Supported formats: `.txt`, `.pdf`, `.csv`, `.md`

2. Build/update the vector store:
```bash
python build_knowledge_base.py build
```

#### Search Knowledge Base
```bash
python build_knowledge_base.py search --query "return policy"
```

#### Update Existing Knowledge Base
```bash
python build_knowledge_base.py update --docs-dir ./new_documents
```

## Testing

Run the test suite:
```bash
pytest test_chatbot.py -v
```

Run with coverage:
```bash
pytest test_chatbot.py --cov=. --cov-report=html
```

## Deployment

### Docker Deployment

1. **Build and run:**
```bash
docker-compose up -d
```

2. **View logs:**
```bash
docker-compose logs -f
```

3. **Stop services:**
```bash
docker-compose down
```

### Production Considerations

**Security:**
- [ ] Enable API key authentication (`REQUIRE_API_KEY=true`)
- [ ] Configure CORS origins
- [ ] Use HTTPS in production
- [ ] Implement rate limiting with Redis
- [ ] Add request validation

**Scalability:**
- [ ] Use PostgreSQL for conversation history
- [ ] Implement Redis for session management
- [ ] Deploy behind load balancer
- [ ] Use managed vector store (Pinecone, Weaviate)
- [ ] Enable auto-scaling

**Monitoring:**
- [ ] Set up logging aggregation (ELK, CloudWatch)
- [ ] Add Prometheus metrics
- [ ] Configure health checks
- [ ] Set up alerts
- [ ] Track API usage and costs

### Cloud Deployment Options

**AWS:**
```bash
# Deploy to ECS/Fargate
aws ecs create-service ...

# Or use Elastic Beanstalk
eb init -p docker customer-service-bot
eb create production
```

**Google Cloud:**
```bash
# Deploy to Cloud Run
gcloud run deploy chatbot-api \
  --image gcr.io/project/chatbot \
  --platform managed
```

**Azure:**
```bash
# Deploy to Container Apps
az containerapp create \
  --name chatbot-api \
  --resource-group chatbot-rg \
  --image chatbot:latest
```

## Customization

### Custom Prompt Template

Edit the prompt in `chatbot.py`:

```python
def _get_custom_prompt(self) -> PromptTemplate:
    template = """Your custom prompt here...
    
    Context: {context}
    History: {chat_history}
    Question: {question}
    
    Response:"""
    
    return PromptTemplate(...)
```

### Add New Features

1. **Custom Tools/Agents:**
   - Modify `chatbot.py` to add LangChain tools
   - Example: Calculator, web search, database queries

2. **Different Memory Types:**
   - Change `CONVERSATION_MEMORY_TYPE` in `.env`
   - Options: `buffer`, `summary`, `window`

3. **Multi-language Support:**
   - Add language detection
   - Use language-specific prompts

### Integrate with Existing Systems

```python
# Example: Connect to your CRM
from chatbot import get_bot

bot = get_bot()

# Custom metadata with CRM info
response, sources = await bot.chat(
    message="What's my order status?",
    session_id=session_id,
    metadata={
        "user_id": "CRM-12345",
        "customer_tier": "premium",
        "last_order_date": "2024-01-15"
    }
)
```

## Monitoring & Logging

Logs are stored in `./logs/app.log` with structured format:

```
2024-01-15 10:30:00 | INFO | Processing message for session abc123...
2024-01-15 10:30:01 | INFO | Generated response for session abc123
```

View real-time logs:
```bash
tail -f logs/app.log
```

## Troubleshooting

### Common Issues

**Issue: "No module named 'langchain'"**
```bash
pip install -r requirements.txt
```

**Issue: "API key not found"**
- Ensure `.env` file exists and contains your API key
- Check that environment variables are loaded

**Issue: "Vector store not found"**
```bash
python build_knowledge_base.py build
```

**Issue: Rate limit errors**
- Adjust `MAX_REQUESTS_PER_MINUTE` in `.env`
- Implement Redis-based rate limiting for production

**Issue: High API costs**
- Use cheaper models (gpt-3.5-turbo, claude-haiku)
- Reduce `MAX_TOKENS` in configuration
- Implement token counting and budgets
- Cache common responses

## Performance Optimization

1. **Vector Store:** Use Pinecone or Weaviate for larger datasets
2. **Caching:** Implement Redis caching for frequent queries
3. **Batch Processing:** Process multiple requests concurrently
4. **Model Selection:** Use faster models for simple queries
5. **Connection Pooling:** Reuse HTTP connections

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - feel free to use for commercial projects

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@yourcompany.com
- Documentation: [Link to docs]

## Roadmap

- [ ] Multi-language support
- [ ] Voice interface integration
- [ ] Advanced analytics dashboard
- [ ] A/B testing framework
- [ ] Integration with popular CRMs
- [ ] Sentiment analysis
- [ ] Automated escalation to human agents
- [ ] Fine-tuning on company data

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [OpenAI](https://openai.com/)
- [Anthropic](https://www.anthropic.com/)

---

**Built for production. Scale with confidence.** 🚀
