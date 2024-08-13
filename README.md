# Threads.net Status Update Generator

This project provides a workflow for generating high-quality text-only status updates for Threads.net, leveraging the power of a local large language model (LLM). It utilizes a state graph to manage the process, involving a user, researcher, draft analyzer, writer, and editor.

## Features

* **Iterative Refinement:** The draft undergoes multiple rounds of analysis, writing, and editing to ensure quality.
* **Researcher Insights:** A researcher analyzes the draft for target audience, key message, writing style, and potential gaps.
* **Draft Analyzer:** Provides a detailed breakdown of the draft's structure and adherence to Threads.net guidelines.
* **Writer Expertise:** A writer incorporates feedback from the researcher and editor to refine the draft.
* **Editor Review:** An editor provides constructive feedback and a score based on specific criteria.
* **User Approval:** The user has the final say on the draft's approval.
* **Version History:** Tracks different versions of the draft for comparison.
* **Character Limit Enforcement:** Ensures the draft stays within the 500-character limit of Threads.net.

## Requirements

* Python 3.7 or higher
* A local LLM running at `http://localhost:1234/v1` (e.g., LM Studio)

## Installation

1. Clone this repository.
2. Install the required packages. You can do this manually or by creating a `requirements.txt` file.

**Manual Installation:**

```bash
pip install langgraph langchain-core openai
```

**Using a `requirements.txt` file:**

1. Create a file named `requirements.txt` in the project directory with the following contents:

```
langgraph
langchain-core
openai
```

2. Then run:

```bash
pip install -r requirements.txt
```

## Usage

1. Start your local LLM.
2. Run the script: `python main.py`
3. Follow the prompts to provide your initial draft and feedback.

## Workflow

The workflow follows these steps:

1. **User:** Submits the initial draft.
2. **Draft Analyzer:** Analyzes the draft's structure and provides suggestions.
3. **Researcher:** Analyzes the draft's content and provides insights.
4. **Writer:** Incorporates feedback and creates a new draft.
5. **Editor:** Reviews the draft and provides feedback and a score.
6. **User:** Reviews the final draft and approves or requests further revisions.

## Configuration

You can adjust the behavior of the workflow by modifying the parameters in the `main.py` file, such as the maximum number of iterations or the temperature for the LLM.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

## License

This project is licensed under the Apache 2.0 License.
