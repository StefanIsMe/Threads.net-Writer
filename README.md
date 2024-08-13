# Threads.net Status Update Generator

This project provides a workflow for generating high-quality text-only status updates for Threads.net, leveraging the power of a local large language model (LLM). It utilizes a state graph, powered by **LangGraph**, to manage the process, involving a user, researcher, draft analyzer, writer, and editor.  The script will prompt you for your initial status update draft.

## Features

* **Iterative Refinement:** The draft undergoes multiple rounds of analysis, writing, and editing to ensure quality.
* **Researcher Insights:** A researcher analyzes the draft for target audience, relevant topics, and potential opinion groups.
* **Draft Analyzer:** Provides a detailed breakdown of the draft's structure and adherence to Threads.net guidelines.
* **Writer Expertise:** A writer incorporates feedback from the researcher and editor to refine the draft.
* **Editor Review:** An editor provides constructive feedback and a score based on specific criteria.
* **User Approval:** The user has the final say on the draft's approval.
* **Version History:** Tracks different versions of the draft for comparison, including reasons for rejection.
* **Character Limit Enforcement:** Ensures the draft stays within the 500-character limit of Threads.net.
* **Detailed Feedback:**  The writer receives specific feedback on each component of the status update (Hook, Introduction, Main Content, Value Proposition, Call to Action).
* **Conciseness Guidance:** The writer receives guidance on how to make the draft more concise, focusing on impactful information.

## Requirements

* Python 3.7 or higher
* A local LLM running at `http://localhost:1234/v1` (e.g., LM Studio)

## Installation

1. Clone this repository.
2. Install the required packages:

```bash
pip install langgraph langchain-core openai
```

## Usage

1. Start your local LLM.
2. Run the script: `python main.py`
3. **You will be prompted to enter your initial draft for the status update.**
4. Follow the prompts to provide feedback and approve or request revisions.

## Workflow

The workflow follows these steps:

1. **User:** Submits the initial draft.
2. **Draft Analyzer:** Analyzes the draft's structure and provides suggestions.
3. **Researcher:** Analyzes the draft's content and provides insights.
4. **Writer:** Incorporates feedback and creates a new draft.
5. **Editor:** Reviews the draft and provides feedback and a score.
6. **User:** Reviews the final draft and approves or requests further revisions.

## How LangGraph is Used

This project leverages **LangGraph** to define and manage the workflow as a state graph. LangGraph provides a framework for creating and executing these complex, multi-step processes. Each step in the workflow (user input, researcher analysis, writer revisions, etc.) is represented as a node in the state graph. LangGraph then orchestrates the transitions between these nodes based on the defined conditions and the current state of the draft. This allows for a flexible and dynamic workflow that can adapt to different scenarios and feedback.

## Configuration

You can adjust the behavior of the workflow by modifying the parameters in the `main.py` file, such as the maximum number of iterations or the temperature for the LLM.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

## License

This project is licensed under the Apache 2.0 License.
