# Threads.net Status Update Assistant

This project provides a workflow for generating high-quality, personalized text-only status updates for Threads.net, leveraging the power of Google Gemini. It utilizes a state graph, powered by **LangGraph**, to manage the process, involving a user, content classifier, writer, relevance assessor, and editor. The script will prompt you for your initial status update draft and then refine it iteratively based on feedback and specific user persona information.

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Workflow](#workflow)
* [How LangGraph is Used](#how-langgraph-is-used)
* [Configuration](#configuration)
* [New Features and Changes](#new-features-and-changes)
* [Getting a Google Gemini API Key](#getting-a-google-gemini-api-key)
* [Setting the API Key as a System Variable](#setting-the-api-key-as-a-system-variable)
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
* **Question Limit Enforcement:** Ensures the draft contains no more than one question.
* **Personalized Content:** The generated status update is tailored to the specific `USER_PERSONA` provided.
* **Content Classification:** Automatically classifies the initial draft as "industry_news" or "personal" to tailor the writing process.
* **Relevance Assessment:** Evaluates the relevance of revised drafts to the initial draft to ensure content alignment.

## Requirements

* Python 3.7 or higher
* A Google Gemini API key (set as an environment variable named `GEMINI_API_KEY`)

## Installation

1. Clone this repository.
2. Install the required packages:

```bash
pip install langgraph langchain-core google-generativeai ratelimit scikit-learn
```

## Usage

1. Set your Google Gemini API key as an environment variable (see instructions below).
2. Run the script: `python main.py`
3. You will be prompted to enter your initial draft for the status update.
4. Follow the prompts to provide feedback and approve or request revisions.

## Workflow

The workflow follows these steps:

1. **User:** Submits the initial draft.
2. **Content Classifier:** Classifies the draft as "industry_news" or "personal".
3. **Writer:** Refines the draft based on the `USER_PERSONA`, content type, and previous feedback.
4. **Relevance Assessor:** Evaluates the relevance of the draft to the initial draft.
5. **Editor:** Reviews the draft and provides feedback and a score.
6. **User:** Reviews the final draft and approves or requests further revisions.

## How LangGraph is Used

This project leverages **LangGraph** to define and manage the workflow as a state graph. LangGraph provides a framework for creating and executing these complex, multi-step processes. Each step in the workflow (user input, writer revisions, editor feedback, etc.) is represented as a node in the state graph. LangGraph then orchestrates the transitions between these nodes based on the defined conditions and the current state of the draft. This allows for a flexible and dynamic workflow that can adapt to different scenarios and feedback.

## Configuration

You can adjust the behavior of the workflow by modifying the parameters in the `main.py` file, such as the maximum number of iterations or the temperature for Google Gemini. You can also modify the `USER_PERSONA` dictionary to tailor the generated content to a specific user.

## New Features and Changes

* **September 1, 2024 - Integrate Google Gemini, Enhance Workflow, and Add Content Classification:**
    - **Switched to Google Gemini for LLM inference, taking advantage of its capabilities and free daily request quota.** 
    - Introduced content classification and relevance assessment nodes.
    - Significantly enhanced the Editor's prompt for more comprehensive feedback.
    - Refined Writer prompts with more detailed instructions and examples.
    - Reduced the question limit to one per status update.
    - Implemented rate limiting and error handling for Google Gemini API calls.
    - Improved code readability and documentation.
    - Added post-processing to remove double spaces after full stops.
* **August 17, 2024 - Enhanced Personalization and Streamlined Workflow:**
    * Introduced a detailed `USER_PERSONA` dictionary for personalized content generation.
    * Streamlined the workflow by removing the `draft_analyzer` and `researcher` nodes.
    * Enhanced the prompts for the `writer` and `editor` nodes to provide more context and guidance.
    * Enforced stricter character limits (450-500 characters) and a maximum of two questions per update.
    * Improved error handling and added a seed parameter for reproducibility.


## Getting a Google Gemini API Key

1. Go to [Google AI Studio](https://studio.ai.google.com/).
2. In the left navigation bar, click the "Get API key" button.
3. On the API Keys page, click the "Create API Key" button.
4. Select an existing Google Cloud project with read-write access, or go to Google Cloud to create a new project.
5. Once you've selected a project, click the button to "Create API key in existing project".
6. You will now see the API key you generated. Copy this API key and proceed to set it up as your system variable.
7. You can close the window to go back to the API Keys page. You should notice that the Plan for this API key is marked as "Free of charge", which means you can access Gemini models API based on the limits detailed here: [https://ai.google.dev/pricing](https://ai.google.dev/pricing) 

## Setting the API Key as a System Variable

You need to set the API key as a system environment variable named `GEMINI_API_KEY` for the script to access it. Here's how you can do it on different operating systems:

**Windows:**

1. Open the Start menu and search for "Environment Variables".
2. Click on "Edit the system environment variables".
3. Click on the "Environment Variables" button.
4. Under "System variables", click on "New".
5. Enter "GEMINI_API_KEY" as the variable name and your API key as the variable value.
6. Click "OK" to save the changes.

## Known Issues

* **Complex Initial Drafts:** The writer may struggle with complex initial status updates and could go into indefinite loops if it cannot make the initial draft concise enough to write content within the character limit.
* **Personal Content:** The quality of generated status updates for personal content tends to be poor, and the workflow may take a long time to complete.
* **Incorrect Timer:** The timer that tracks the total workflow time from initial draft submission to editor approval is currently inaccurate and does not reflect the actual time taken.

## Feature Roadmap

* **Fact Checker Node:** Add a fact-checking node that compares the writer's draft with the initial user-provided draft to ensure factual accuracy.
* **Improved Personal Content Generation:** Investigate and address the issues related to generating high-quality personal status updates, potentially by analyzing the specific challenges and exploring different prompting strategies.
* **Reintroduce Researcher Node:** Reintroduce the `researcher` node to incorporate external research and insights into the status update generation process.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.

## License

This project is licensed under the Apache 2.0 License.
