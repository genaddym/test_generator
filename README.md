# Network Testing Infrastructure

This project provides a comprehensive infrastructure for creating and executing network tests, specifically designed for testing network devices (routers) through CLI interfaces.

## Features

- CLI Session Management
- Response Parsing Framework
- Automated Test Generation
- Multi-vendor Support
- Comprehensive Error Handling
- Detailed Logging

## Project Structure

```
.
├── ai_tools/              # AI-powered test generation tools
├── tests/                 # Test implementations
│   └── lab-1/            # Lab-specific tests
│       └── test_anycast_sid/  # Example test implementation
├── requirements.txt       # Project dependencies
└── README.md             # Project documentation
```

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

1. Create a new test folder with:
   - `test_flow.md`: Test flow documentation
   - `command_outputs.md`: CLI command outputs

2. Generate test implementation:
```python
from ai_tools.openai_client import OpenAIClient

client = OpenAIClient()
implementation_guide = client.generate_test("path/to/test/folder")
```

## Requirements

- Python 3.8+
- OpenAI API key
- Network device access

## License

[Add your license here] 