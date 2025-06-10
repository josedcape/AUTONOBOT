# AUTONOBOT Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install AUTONOBOT

#### Windows Users
```cmd
# Download the repository and run:
install.bat
```

#### Linux/macOS Users
```bash
# Download the repository and run:
chmod +x install.sh
./install.sh
```

### Step 2: Configure API Keys

Edit the `.env` file and add your API key for at least one LLM provider:

```env
# Choose one or more providers:
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
```

### Step 3: Launch the Application

#### Windows
```cmd
start_autonobot.bat
```

#### Linux/macOS
```bash
./start_autonobot.sh
```

The web interface will open at: http://127.0.0.1:7788

## 🎯 Your First Task Queue

### 1. Configure Basic Settings
- Go to the **🔧 LLM Configuration** tab
- Select your LLM provider (e.g., "openai")
- Choose a model (e.g., "gpt-4o")
- Verify your API key is set

### 2. Set Browser Preferences
- Go to the **🌐 Browser Settings** tab
- Enable "Keep Browser Open" for queue processing
- Adjust window size if needed (default: 1280x1100)
- Enable recording to save task videos

### 3. Create Your First Task Queue
- Go to the **📋 Task Queue** tab
- Add your first task:
  - **Task Name**: "Google Search Test"
  - **Description**: "Go to google.com and search for 'OpenAI'"
  - **Priority**: 1
- Click **➕ Add to Queue**

### 4. Add More Tasks
Add a few more tasks to see the queue in action:

**Task 2:**
- **Name**: "Check Weather"
- **Description**: "Go to weather.com and check weather for New York"
- **Priority**: 2

**Task 3:**
- **Name**: "News Headlines"
- **Description**: "Go to news.google.com and read the top technology headline"
- **Priority**: 1

### 5. Start the Queue
- Click **▶️ Start Queue**
- Watch the queue status update in real-time
- Monitor task progress in the status display

## 🎮 Queue Management

### Adding Tasks While Running
- You can add new tasks even while the queue is processing
- New tasks will be queued and executed in priority order
- No need to stop the current execution

### Controlling Queue Execution
- **⏸️ Pause**: Temporarily halt queue (current task continues)
- **⏯️ Resume**: Continue processing paused queue
- **⏹️ Stop**: Stop queue and current task immediately

### Managing Individual Tasks
- Copy the Task ID from the queue display
- Paste it in the "Task ID" field
- Use **⬆️ Move Up** or **⬇️ Move Down** to reorder
- Use **🗑️ Remove** to delete pending tasks

## 🔧 Essential Settings

### For Best Queue Performance
1. **Enable "Keep Browser Open"** in Browser Settings
2. **Set "Headless Mode" to false** to see browser actions
3. **Enable Recording** to save task videos
4. **Use appropriate priorities** (1-10, higher = more important)

### Recommended Configuration
```
Agent Type: custom
Max Steps: 100
Use Vision: ✓ Enabled
LLM Provider: openai (or your preferred provider)
Model: gpt-4o
Keep Browser Open: ✓ Enabled
Headless Mode: ✗ Disabled (so you can watch)
Recording: ✓ Enabled
```

## 📊 Understanding Queue Status

### Status Indicators
- **⏳ Pending**: Task waiting to be executed
- **🔄 Running**: Task currently being processed
- **✅ Completed**: Task finished successfully
- **❌ Failed**: Task encountered an error
- **⏸️ Paused**: Queue is paused
- **🚫 Cancelled**: Task was cancelled

### Queue Information
The status display shows:
- Total number of tasks
- Count by status (pending, running, completed, failed)
- Whether queue is paused or running
- Details of current running task

## 🎯 Example Workflows

### Morning Information Routine
1. Check weather for your city
2. Read top news headlines
3. Check stock market status
4. Review calendar for today

### Research Project
1. Search Wikipedia for topic overview
2. Find recent news articles
3. Look for academic papers
4. Check YouTube for educational videos

### Shopping Research
1. Search for product on Amazon
2. Compare prices on other sites
3. Read customer reviews
4. Check product specifications

## 🚨 Troubleshooting

### Common Issues and Solutions

#### "Task queue is empty"
- Add tasks using the "Add New Task" section
- Make sure to click "Add to Queue" button

#### "Queue not starting"
- Check that you have pending tasks
- Verify LLM configuration is correct
- Ensure API key is valid

#### "Browser not opening"
- Check browser settings
- Try disabling "Headless Mode"
- Verify Chrome/browser installation

#### "Tasks failing"
- Check internet connection
- Verify website URLs are accessible
- Simplify task descriptions
- Check LLM provider status

### Getting Help
- Check the **📊 Results** tab for detailed error messages
- Review task descriptions for clarity
- Try running single tasks first before queuing
- Check the console output for technical errors

## 🎉 Next Steps

### Explore Advanced Features
- Try different LLM providers and models
- Experiment with task priorities
- Use the recording feature to review task execution
- Save and load configuration presets

### Join the Community
- Report bugs and request features on GitHub
- Share your task automation workflows
- Contribute to documentation and examples

### Scale Your Automation
- Create task templates for repeated workflows
- Build complex multi-step automation sequences
- Integrate with your daily productivity routines

## 📚 Additional Resources

- **FEATURES.md**: Complete feature documentation
- **INSTALLATION.md**: Detailed installation guide
- **examples/**: Sample tasks and configurations
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Community support and discussions

---

**Happy Automating! 🤖✨**

The AUTONOBOT task queue system is designed to make browser automation accessible and powerful. Start with simple tasks and gradually build more complex workflows as you become familiar with the system.
