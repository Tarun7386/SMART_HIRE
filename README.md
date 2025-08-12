
# Recruitment System

This project is a recruitment system designed to streamline the hiring process by automating various tasks such as job description analysis, CV parsing, candidate matching, and interview scheduling.

## Project Structure

- **agents/**: Contains various agents responsible for different tasks in the recruitment process.
  - `jd_analyzer.py`: Analyzes job descriptions.
  - `cv_parser.py`: Parses CVs.
  - `matcher.py`: Matches candidates to job descriptions.
  - `scheduler.py`: Coordinates interviews.

- **data/**: Stores job descriptions and resumes.
  - `job_descriptions/`: Directory for job description files.
  - `resumes/`: Directory for CV files.

- **db/**: Contains database-related files.
  - `models.py`: Defines database models.
  - `database.py`: Handles database operations.

- **utils/**: Contains utility functions for various tasks.
  - `document_processor.py`: Handles document processing.
  - `text_extractor.py`: Extracts text from PDFs and DOCX files.
  - `llm_connector.py`: Interfaces with the Ollama language model.

- `config.py`: Configuration settings for the application.
- `main.py`: Main entry point of the application.
- `requirements.txt`: Lists project dependencies.

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To run the application, execute:

```
python main.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
