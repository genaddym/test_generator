# Network Testing Infrastructure

A comprehensive infrastructure for creating and executing network tests, specifically designed for testing network devices (routers) through CLI interfaces. This framework enables automated testing of network configurations, routing protocols, and device behaviors.

## Features

- **CLI Session Management**
  - Base interface for managing CLI sessions with network devices
  - Support for multiple vendor implementations through abstract base class
  - SSH-based device connections
  - Command execution with response handling
  - Configuration management (edit, commit, rollback)

- **Response Parsing**
  - Framework for parsing CLI command responses into structured data
  - Decipher abstract base class for defining parsing interfaces
  - Conversion of raw CLI text output into structured Python objects
  - Support for vendor-specific parsing implementations

- **Testing Capabilities**
  - Automated device configuration verification
  - Routing protocol validation
  - Multi-device consistency checks
  - Complex network topology testing

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

- Python >= 3.8
- OpenAI >= 1.12.0
- python-dotenv >= 1.0.0
- PyYAML
- pytest

## Project Structure

```
automation_utils/
├── ai_tools/            # AI integration tools
├── tests/              # Test suites and examples
│   ├── base/          # Base test utilities
│   └── lab1/          # Lab-specific test cases
└── code_snippets.py   # Utility code snippets
```

## Target Users

- Network engineers and operators
- Network testing teams
- Network device vendors
- Service providers
- Network automation teams

## Development

To contribute to this project:

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest`

## License

[Add your chosen license here] 