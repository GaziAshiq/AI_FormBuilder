# 🎯 AI Form Generator

A smart, AI-powered form generator that creates and manages form structures through natural language conversations. Built with Python and powered by Ollama/OpenAI.

## ✨ Features

- 🤖 **Natural Language Form Creation** - Just describe your form in plain English
- 🔄 **Interactive Updates** - Add, modify, or remove fields through conversation
- 🎯 **Smart Field Detection** - Automatically determines appropriate field types
- 📝 **JSON Template Based** - Clean, consistent form structure output
- 🔌 **Multiple AI Backends** - Supports both Ollama and OpenAI
- 💾 **State Management** - Maintains form context between interactions
- 🚀 **API Ready** - FastAPI integration for web service deployment (Coming Soon)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-form-generator.git

# Install dependencies
pip install -r requirements.txt

# Run the form generator CLI
python form_generator.py

# Run the API server (Coming Soon)
python api_server.py
```

## 💡 Usage Example

```bash
# Start a conversation with the AI form generator
> Create a registration form with name and email

> Add phone number field

> Make email required

> Show current form
{
    "fields": [
        {
            "type": "text",
            "label": "Full Name",
            "name": "full_name",
            "required": false
        },
        {
            "type": "email",
            "label": "Email Address",
            "name": "email",
            "required": true
        },
        {
            "type": "text",
            "label": "Phone Number",
            "name": "phone_number",
            "required": false
        }
    ]
}
```

## 🛠️ Supported Field Types

- 📝 Text
- 📧 Email
- 🔢 Number
- 📅 Date
- 📋 Dropdown
- ⭕ Radio Buttons
- ✅ Checkboxes
- 📎 File Upload

## 🔧 Configuration

```python:README.md
# Configure AI backend in ai_server.py
client = AIClient(
    use_ollama=True,  # Set False for OpenAI
    model="deepseek-r1:8b"  # Choose your model
)
```

## 🗺️ Roadmap

- ⚡ FastAPI Integration
  - REST API endpoints for form generation
  - Swagger documentation
  - Web interface for form creation
- 📋 Form Templates
- 🔄 Import/Export functionality
- 🔒 Authentication and rate limiting

## 📝 License

MIT License - feel free to use this project for your own work!

## 🙏 Acknowledgments

- Powered by [Ollama](https://github.com/ollama/ollama)
- Compatible with [OpenAI](https://openai.com/)

---
Made with ❤️ by [Gazi Ashiq]
