# Threads.net Status Update Generator

This project provides a workflow for generating high-quality, personalized text-only status updates for Threads.net, leveraging the power of a local large language model (LLM). It utilizes a state graph, powered by **LangGraph**, to manage the process, involving a user, writer, and editor. The script will prompt you for your initial status update draft and then refine it iteratively based on feedback and specific user persona information.

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Workflow](#workflow)
* [How LangGraph is Used](#how-langgraph-is-used)
* [Configuration](#configuration)
    * [New Features and Changes](#new-features-and-changes)
* [Known Issues](#known-issues)
* [Feature Roadmap](#feature-roadmap)
* [Contributing](#contributing)
* [License](#license)

## Features

* **Iterative Refinement:** The draft undergoes multiple rounds of editing and feedback to ensure quality.
* **Writer Expertise:** A writer incorporates feedback from the editor to refine the draft.
* **Editor Review:** An editor provides constructive feedback and a score based on specific criteria and the `USER_PERSONA`.
* **User Approval:** The user has the final say on the draft's approval.
* **Version History:** Tracks different versions of the draft for comparison, including reasons for rejection.
* **Character Limit Enforcement:** Ensures the draft stays within the 450-500 character limit of Threads.net.
* **Question Limit Enforcement:** Ensures the draft contains no more than two questions.
* **Personalized Content:** The generated status update is tailored to the specific `USER_PERSONA` provided.

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
2. **Writer:** Refines the draft based on the `USER_PERSONA` and previous feedback.
3. **Editor:** Reviews the draft and provides feedback and a score.
4. **User:** Reviews the final draft and approves or requests further revisions.


## How LangGraph is Used

This project leverages **LangGraph** to define and manage the workflow as a state graph. LangGraph provides a framework for creating and executing these complex, multi-step processes. Each step in the workflow (user input, writer revisions, editor feedback, etc.) is represented as a node in the state graph. LangGraph then orchestrates the transitions between these nodes based on the defined conditions and the current state of the draft. This allows for a flexible and dynamic workflow that can adapt to different scenarios and feedback.

## Configuration

You can adjust the behavior of the workflow by modifying the parameters in the `main.py` file, such as the maximum number of iterations or the temperature for the LLM. You can also modify the `USER_PERSONA` dictionary to tailor the generated content to a specific user.

### New Features and Changes

* **August 17, 2024 - Enhanced Personalization and Streamlined Workflow:**
    * Introduced a detailed `USER_PERSONA` dictionary for personalized content generation.
    * Streamlined the workflow by removing the `draft_analyzer` and `researcher` nodes.
    * Enhanced the prompts for the `writer` and `editor` nodes to provide more context and guidance.
    * Enforced stricter character limits (450-500 characters) and a maximum of two questions per update.
    * Improved error handling and added a seed parameter for reproducibility.

## Known Issues

* **Complex Initial Drafts:** The writer may struggle with complex initial status updates and could go into indefinite loops if it cannot make the initial draft concise enough to write content within the character limit.
* **Personal Content:** The quality of generated status updates for personal content tends to be poor, and the workflow may take a long time to complete.
* **Incorrect Timer:** The timer that tracks the total workflow time from initial draft submission to editor approval is currently inaccurate and does not reflect the actual time taken.

## Feature Roadmap

* **Fact Checker Node:** Add a fact-checking node that compares the writer's draft with the initial user-provided draft to ensure factual accuracy.
* **Improved Personal Content Generation:** Investigate and address the issues related to generating high-quality personal status updates, potentially by analyzing the specific challenges and exploring different prompting strategies or LLM fine-tuning.
* **Reintroduce Researcher Node:** Reintroduce the `researcher` node to incorporate external research and insights into the status update generation process.


## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

## License

This project is licensed under the Apache 2.0 License.
