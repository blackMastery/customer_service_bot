# Quick Reference Guide

## 🚀 Getting Started in 5 Minutes

```bash
# 1. Run setup script
chmod +x setup.sh
./setup.sh

# 2. Edit .env with your API keys
nano .env

# 3. Start the chatbot
python main.py
# OR
streamlit run streamlit_app.py
```

## 📝 Common Commands

### Development
```bash
# Run API server
python main.py

# Run Streamlit UI
streamlit run streamlit_app.py

# Run tests
pytest test_chatbot.py -v

# Build knowledge base
python build_knowledge_base.py build
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Makefile
```bash
make install      # Install dependencies
make run-api      # Run API
make run-ui       # Run UI
make build-kb     # Build knowledge base
make test         # Run tests
make docker-up    # Start Docker
```

## 🔧 Configuration Cheat Sheet

### Environment Variables (.env)
```env
# Choose your LLM
LLM_PROVIDER=openai        # or anthropic
OPENAI_API_KEY=sk-...      # Your OpenAI key
MODEL_NAME=gpt-4-turbo-preview

# Business settings
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@company.com
BUSINESS_HOURS=Mon-Fri, 9 AM - 5 PM
```

### Switching Models

**OpenAI Models:**
- Fast & Cheap: `gpt-3.5-turbo`
- Balanced: `gpt-4-turbo-preview`
- Best Quality: `gpt-4`

**Anthropic Models:**
- Fast & Cheap: `claude-3-haiku-20240307`
- Balanced: `claude-3-sonnet-20240229`
- Best Quality: `claude-3-opus-20240229`

## 🌐 API Quick Reference

### Send Message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "user-123"}'
```

### Get History
```bash
curl "http://localhost:8000/conversation/user-123"
```

### Clear History
```bash
curl -X DELETE "http://localhost:8000/conversation/user-123"
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

## 📚 Knowledge Base Management

### Add Documents
```bash
# 1. Add files to data/knowledge_base/
cp my-policy.txt data/knowledge_base/

# 2. Rebuild vector store
python build_knowledge_base.py build
```

### Supported Formats
- `.txt` - Plain text
- `.pdf` - PDF documents
- `.csv` - CSV files
- `.md` - Markdown files

### Search Knowledge Base
```bash
python build_knowledge_base.py search --query "refund policy"
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `pip install -r requirements.txt` |
| API key error | Edit `.env` and add your keys |
| Vector store error | Run `python build_knowledge_base.py build` |
| Port already in use | Change `API_PORT` in `.env` |
| Rate limit error | Increase `MAX_REQUESTS_PER_MINUTE` |

## 💡 Tips & Best Practices

### Optimizing Costs
1. Use `gpt-3.5-turbo` for simple queries
2. Set lower `MAX_TOKENS` values
3. Implement caching for common questions
4. Monitor usage with OpenAI dashboard

### Improving Responses
1. Add comprehensive documents to knowledge base
2. Use specific, detailed prompts
3. Tune temperature (0.7 for balanced, 0.3 for focused)
4. Review and curate your knowledge base regularly

### Production Deployment
1. Enable API key authentication
2. Set up HTTPS with reverse proxy
3. Use managed vector store (Pinecone)
4. Implement Redis for sessions
5. Add monitoring and alerts
6. Set up log aggregation

## 📊 Monitoring

### View Logs
```bash
tail -f logs/app.log
```

### Check Service Status
```bash
curl http://localhost:8000/health
```

### Docker Logs
```bash
docker-compose logs -f api
docker-compose logs -f streamlit
```

## 🎯 Usage Examples

### Python Client
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "What are your hours?", "session_id": "user-1"}
)
print(response.json()["response"])
```

### JavaScript Client
```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'What are your hours?',
    session_id: 'user-1'
  })
})
.then(res => res.json())
.then(data => console.log(data.response));
```

## 🔐 Security Checklist

- [ ] Change default API keys
- [ ] Enable `REQUIRE_API_KEY=true`
- [ ] Configure `VALID_API_KEYS`
- [ ] Set appropriate `CORS_ORIGINS`
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Enable request logging
- [ ] Regular security updates

## 📈 Performance Tuning

### Fast Response Times
```env
MODEL_NAME=gpt-3.5-turbo  # or claude-3-haiku
TEMPERATURE=0.3
MAX_TOKENS=500
```

### Better Quality
```env
MODEL_NAME=gpt-4  # or claude-3-opus
TEMPERATURE=0.7
MAX_TOKENS=2000
```

### Balanced
```env
MODEL_NAME=gpt-4-turbo-preview  # or claude-3-sonnet
TEMPERATURE=0.7
MAX_TOKENS=1000
```

## 🆘 Getting Help

- Read the full README.md
- Check API docs: http://localhost:8000/docs
- Review logs: `tail -f logs/app.log`
- Test endpoint: http://localhost:8000/health
- GitHub Issues: [Create issue]

---

**Pro Tip:** Bookmark this guide for quick reference! 📌
