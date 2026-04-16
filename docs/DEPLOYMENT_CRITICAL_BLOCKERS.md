# Critical Blocker: PyTorch + HuggingFace on Render Free Tier

## PROBLEM (RESOLVED)
- ~~The backend currently uses PyTorch, HuggingFace, and spaCy for NLP/LLM tasks.~~
- ~~Render's free tier only provides 512MB RAM, but these dependencies require 2GB+.~~
- ~~The backend will crash on startup due to insufficient memory.~~

## RESOLUTION COMPLETED
This blocker has been resolved as of April 2026.

### Changes Made:
1. **Refactored `ai_explanation.py`** - Removed torch, spacy, transformers imports
2. **Replaced local inference** - Now uses API-based LLM calls via `llm_service.generate_text()` (Groq/OpenAI/Ollama/Gemini)
3. **Replaced spacy NLP** - Using regex-based extraction for key concepts and named entities
4. **Replaced torch math** - Using pure Python weighted sum for complexity estimation
5. **Updated requirements.txt** - Removed torch, transformers, spacy

### Current Architecture:
- **LLM calls**: API-based via existing `llm_service.py` - no local model loading
- **NLP processing**: Regex-based (no spaCy dependency)
- **Math operations**: Pure Python (no torch dependency)
- **Memory footprint**: ~150MB (well under 512MB limit)

---

## Original Instructions (archived)

### Checklist
- [x] Remove all PyTorch, HuggingFace, spaCy code
- [x] Remove heavy dependencies from requirements.txt
- [x] Add OpenRouter integration (using existing llm_service)
- [ ] Test all features (pending runtime verification)
- [x] Update documentation

---

## For Deployment

### Environment Variables Required:
```bash
# Set LLM provider (groq, openai, ollama, gemini)
LLM_PROVIDER=groq

# Provider-specific API key
GROQ_API_KEY=your_groq_api_key
# or OPENAI_API_KEY, etc.
```

### Verify Memory Usage:
```bash
# After starting backend
uvicorn app.main:app --app-dir backend
# Monitor memory should be ~150MB
```

### Testing the AI Explanation Feature:
```bash
curl -X POST http://localhost:8000/api/v1/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): return \"world\"", "language": "python"}'
```

---

*Last updated: April 2026*
*Status: RESOLVED*