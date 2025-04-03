# Tax Agent

An AI-powered tax assistant that answers tax questions by referencing the US Tax Code using local Large Language Models.

## Overview

This project provides a conversational tax agent that:

1. Responds to natural language tax questions from users
2. Leverages local LLMs via Ollama to process and understand tax-related queries
3. References and cites specific sections of the US Tax Code in its responses
4. Processes tax code documents for accurate information retrieval

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) with LLM models installed (e.g., `llama3.1:8b`)
- Required Python packages:

```txt
lxml
beautifulsoup4
bs4
ollama
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/ErikCohenDev/tax_agent.git
cd tax_agent
```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama and download models:

   ```bash
   # Install Ollama following instructions at https://ollama.ai/
   # Pull the LLM model
   ollama pull llama3.1:8b
   ```

4. Prepare the tax code data:
   ```bash
   mkdir -p data/output logs
   # Run the XML to MD conversion pipeline to prepare the tax code data
   python src/main.py --xml data/usc26.xml --output data/output/usc26_formatted.md
   ```

## Usage

Start the tax agent:

```bash
python src/main.py
```

Example interaction:

```
Welcome to Tax Agent! Ask me any tax-related questions.
> What is the standard deduction for 2023?

The standard deduction for 2023 depends on your filing status:
- For single taxpayers and married filing separately: $13,850
- For married filing jointly: $27,700
- For head of household: $20,800

Source: 26 USC §63(c)(7)(A) [Standard Deduction]
```

## Features

- **Natural Language Understanding**: Ask questions in plain English
- **Source Citations**: All responses include specific references to the tax code
- **Context Awareness**: Maintains conversation context for follow-up questions
- **Comprehensive Coverage**: Access to the complete US Tax Code

## Project Structure

```
tax_agent/
├── src/
│   ├── main.py               # Main application and query handling
│   ├── xml_to_markdown.py    # Tax code document processing
│   ├── format_markdown.py    # Document formatter using LLMs
│   ├── agent.py              # Tax agent implementation (query processing)
├── data/
│   ├── *.xml                 # Raw tax code files
│   ├── *.md                  # Processed tax code documents
│   ├── intermediate/         # Processing files
│   ├── output/               # Formatted tax code ready for reference
├── logs/                     # Processing logs
├── requirements.txt          # Project dependencies
```

## How It Works

1. **Document Processing**: Converts raw tax code XML to searchable Markdown
2. **Query Processing**: Analyzes user questions to identify relevant tax concepts
3. **Information Retrieval**: Searches the processed tax code for applicable sections
4. **Response Generation**: Formulates clear answers with direct citations to the tax code

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Implement your changes
4. Add tests if applicable
5. Ensure code quality and formatting
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add comments for complex logic
- Include docstrings for functions and modules

### Areas for Improvement

- Implement document retrieval optimization
- Add support for tax forms and instructions
- Develop natural language understanding for complex queries
- Create a web interface
- Add historical tax code versions for different tax years
- Implement state tax code support

## License

MIT
