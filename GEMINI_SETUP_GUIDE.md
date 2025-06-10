# Google Gemini 2.0 Flash Experimental Setup Guide

## 🚀 Quick Setup

AUTONOBOT is now configured to use Google's Gemini 2.0 Flash Experimental as the default LLM provider. Follow these steps to complete the setup:

### 1. Get Your Google API Key

1. **Visit Google AI Studio**: https://aistudio.google.com/
2. **Sign in** with your Google account
3. **Click "Get API Key"** in the top navigation
4. **Create a new API key** or use an existing one
5. **Copy the API key** (starts with `AIza...`)

### 2. Configure the API Key

**Option A: Edit the .env file**
```bash
# Open the .env file and replace the placeholder
GOOGLE_API_KEY=your_actual_api_key_here
```

**Option B: Set in the Web UI**
1. Open AUTONOBOT at http://127.0.0.1:7788
2. Go to **🔧 LLM Configuration** tab
3. Paste your API key in the **API Key** field
4. Click **🔄 Update Task Processor Config**

### 3. Verify Configuration

1. **Check the LLM Provider** is set to `gemini`
2. **Check the Model** is set to `gemini-2.0-flash-exp`
3. **Test with Run Agent**: Try a simple task like "go to google.com"
4. **Test with Task Queue**: Add a task and start queue processing

## 🔧 Configuration Details

### Default Settings
- **Provider**: `gemini`
- **Model**: `gemini-2.0-flash-exp`
- **Temperature**: `1.0`
- **Vision**: `Enabled`
- **Max Steps**: `100`

### Available Gemini Models
- `gemini-2.0-flash-exp` (Default - Latest experimental)
- `gemini-2.0-flash-thinking-exp`
- `gemini-1.5-flash-latest`
- `gemini-1.5-flash-8b-latest`
- `gemini-2.0-flash-thinking-exp-1219`

## 🛠️ Troubleshooting

### Common Issues

**1. "Connection error" in Task Queue**
- **Solution**: Make sure your API key is set in the .env file
- **Check**: Click "🔄 Update Task Processor Config" in the Task Queue tab

**2. "API key not configured"**
- **Solution**: Set `GOOGLE_API_KEY=your_key_here` in the .env file
- **Alternative**: Enter the key in the LLM Configuration tab

**3. "Browser closed" errors**
- **Solution**: Enable "Keep Browser Open" in Browser Settings
- **Check**: Set `CHROME_PERSISTENT_SESSION=true` in .env

**4. Task Queue not using Gemini**
- **Solution**: Click "🔄 Update Task Processor Config" after changing settings
- **Verify**: Check the logs for "Task processor updated with LLM: gemini"

### Verification Steps

1. **Check Logs**: Look for these messages in the terminal:
   ```
   ✅ Task processor configured with gemini (gemini-2.0-flash-exp)
   ✅ API key configured (length: XX)
   ```

2. **Test Run Agent**: Should work immediately with UI settings

3. **Test Task Queue**: Should work after clicking "Update Task Processor Config"

## 🎯 Usage Tips

### For Best Results
- **Use descriptive tasks**: "Go to google.com and search for 'OpenAI', then click the first result"
- **Enable recording**: To see what the agent is doing
- **Use vision mode**: Gemini 2.0 Flash Experimental has excellent vision capabilities
- **Keep browser open**: For queue processing efficiency

### Example Tasks
```
1. "Go to google.com and search for 'Python tutorials'"
2. "Navigate to github.com and find the trending repositories"
3. "Visit wikipedia.org and search for 'artificial intelligence'"
```

## 📊 Performance

### Gemini 2.0 Flash Experimental Benefits
- **Fast response times**: Optimized for speed
- **Excellent vision**: Can understand screenshots and UI elements
- **Cost-effective**: Competitive pricing
- **Latest features**: Access to newest capabilities

### Rate Limits
- **Free tier**: 15 requests per minute
- **Paid tier**: Higher limits available
- **Monitor usage**: Check Google AI Studio dashboard

## 🔄 Switching Between Providers

You can easily switch between different LLM providers:

1. **In the UI**: Change LLM Provider dropdown
2. **Update config**: Click "🔄 Update Task Processor Config"
3. **Verify**: Check logs for confirmation

### Supported Providers
- **Gemini** (Default)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- DeepSeek
- Ollama (Local)

---

**Status**: ✅ CONFIGURED FOR GEMINI 2.0 FLASH EXPERIMENTAL
**Next**: Add your API key and start automating!
