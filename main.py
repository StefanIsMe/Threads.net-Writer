from typing import Annotated, TypedDict, List
import operator
import time
from datetime import datetime # Import the datetime library
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from openai import OpenAI
import re

# Set up the OpenAI client and define the LLM model globally
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
LLM_MODEL = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"  # Global variable for the LLM model

# User Persona (Global Variable)
USER_PERSONA = {
    "name": "John Doe",
    "age_range": 30,
    "birthdate": "01/01/1993",
    "gender": "Male",
    "birth_location": "Anytown, USA",
    "residence": "New York City, USA",
    "occupation": "Software Engineer",
    "marital_status": "Single",
    "political_affiliations": "Moderate",
    "education": "Bachelor's degree in Computer Science",
    "threads_usage_reason": "Networking, tech news, sharing opinions",
    "topics_of_interest": {
        "tech": ["Software development", "web3", "cybersecurity", "new gadgets"],
        "news_business": ["Technology news", "business trends", "startups"],
        "politics": ["US politics", "international relations"],
        "other": ["Travel", "music", "cooking"]
    },
    "writing_style": "Casual and informative, occasionally uses humor, enjoys debates.",
    "typical_audience": "Tech professionals, software developers, entrepreneurs",
    "content_preferences": {
        "posts_about": ["New tech gadgets", "coding tips", "software trends", "travel experiences"],
        "strong_opinions": ["Open-source software", "the importance of data privacy"],
        "avoids": ["Controversial political topics", "celebrity gossip", "personal drama"]
    },
    "threads_goals": "Stay connected with the tech community, share knowledge, learn from others",
    "favorite_accounts": "Tech influencers, software companies, news outlets",
    "standout_qualities": "Technical knowledge, insightful opinions, engaging writing style"
}

class StatusUpdateState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage | SystemMessage], operator.add]
    draft: str
    character_count: int
    status: str
    versions: List[str]
    editor_feedback: str
    iteration_count: int
    editor_history: List[str]
    start_time: float

def increment_and_check_iterations(state: StatusUpdateState) -> StatusUpdateState:
    state["iteration_count"] += 1
    if state["iteration_count"] > 300:
        print("Maximum overall iterations reached. Forcing completion.")
        return {"status": "approved"}
    return {}

def user(state: StatusUpdateState) -> StatusUpdateState:
    state.update(increment_and_check_iterations(state))
    print(f"User node: Current status - {state['status']}")

    def get_multiline_input(prompt):
        print(prompt)
        print("Enter your text below. You can use multiple lines.")
        print("When you're done, enter '//done' on a new line.")
        lines = []
        while True:
            line = input()
            if line.strip().lower() == '//done':
                break
            lines.append(line)
        return "\n".join(lines)

    if state["status"] == "initial":
        initial_draft = get_multiline_input("Please enter your initial draft for the status update:")
        print("User has submitted the initial draft. Sending it to the Writer.\n") 

        # Record the start time using datetime
        state["start_time"] = datetime.now() 
        print(f"Start time recorded: {state['start_time'].strftime('%H:%M:%S')}") 

        return {"draft": initial_draft, "status": "draft_submitted"}

    elif state["status"] == "user_approval":
        print("\nThe status update is ready for final approval. Asking the user the following:\n")
        print("\nFinal draft for approval:")
        print(state["draft"])
        while True:
            approval = input("Do you approve this draft? (yes/no): ").lower()
            if approval in ['yes', 'no']:
                break
            print("Please enter 'yes' or 'no'.")

        if approval == 'yes':
            print("User approved the final draft\n")
            return {"status": "approved"}
        else:
            feedback = get_multiline_input("Please provide feedback for revision:")
            print(f"User requested revision: {feedback}\n")
            return {"editor_feedback": feedback, "status": "needs_revision"}

    return {}

def writer(state: StatusUpdateState) -> StatusUpdateState:
    state.update(increment_and_check_iterations(state))
    print("The Writer is now assembling the status update...\n")
    editor_feedback = state.get('editor_feedback', 'No editor feedback yet') 

    # Build version history string, including character count rejections
    version_history_str = ""
    for i, version in enumerate(state["versions"]):
        if i == 0:  # Skip the initial empty draft
            continue
        rejection_reason = ""
        if i == len(state["versions"]) - 1:
            rejection_reason = state["editor_feedback"] 
        elif len(version) > 500:  # Check if rejected due to character count
            rejection_reason = f"Exceeded character limit ({len(version)} characters)."
        else:
            rejection_reason = state["editor_history"][i - 1]
        version_history_str += f"## Version {i}:\n{version}\n**Reason for Rejection:** {rejection_reason}\n\n"

    prompt = f"""
    You are a professional writer creating a text-only status update for Threads.net, specifically for **{USER_PERSONA['name']}**, whose persona is described below:
    Important: Your primary goal is to refine and improve the initial draft provided by the user, ensuring that the final status update remains closely aligned with the original topic and key points. Do not introduce unrelated information or deviate significantly from the original content. 

    User Persona:
    {USER_PERSONA}

    Original Draft: {state['draft']}
    **This is the initial draft of the Threads.net status update provided by the user. Your goal is to improve and refine this draft based on the guidelines, feedback, and insights provided, using your expertise as a professional writer to create a high-quality final version.** 

    Editor's feedback: {editor_feedback} 
    **The Editor has reviewed the most recent version of the status update and provided feedback on its strengths and weaknesses, along with a score. Carefully consider the Editor's suggestions and address any issues raised to improve the quality of your current draft.**

    Previous Versions and Rejection Reasons:
    {version_history_str}
    **This section contains previous versions of the status update that you attempted to write, along with the reasons why each version was rejected by the Editor or due to exceeding the character limit. Carefully analyze each version and its rejection reason to understand the mistakes that were made and avoid repeating them in your current draft.**

    Instructions:
    1. If the editor has provided feedback, carefully consider their suggestions and make appropriate revisions.
    2. Carefully review the previous versions and the reasons they were rejected. Avoid repeating the same mistakes.
    3. **Content Adherence Check: Before submitting your draft, carefully compare it to the initial draft. Ensure that your draft remains closely aligned with the original topic and key points, and that you have not introduced unrelated information or deviated significantly from the original content.**

    Guidelines for the Perfect Status Update Structure (Tailored for {USER_PERSONA['name']}):
    1. Hook (10% of content, aim for 5-10 words):  
        * Purpose: Capture the reader's attention right away.
        * Consider {USER_PERSONA['name']}'s {USER_PERSONA['writing_style']} and preference for posts about {', '.join(USER_PERSONA['content_preferences']['posts_about'])}.
        * Techniques:
            - Present a startling or unexpected statistic related to the topic.
            - Make a bold statement or assertion to stimulate interest.
            - Use vivid imagery or a metaphor to grab attention.

    2. Introduction (15% of content, aim for 8-15 words):
        * Purpose: Briefly set the stage for the main topic.
        * Keep {USER_PERSONA['name']}'s {USER_PERSONA['writing_style']} in mind.
        * Techniques:
            - Concisely summarize the core idea or event you'll be discussing.
            - Offer some brief background information to provide context for the reader.

    3. Main Content (50% of content, aim for 25-40 words):
        * Purpose: Dive deeper into the topic, providing details, insights, and analysis.
        * Remember {USER_PERSONA['name']}'s interest in {', '.join(USER_PERSONA['topics_of_interest']['tech'])} and {USER_PERSONA['name']}'s {USER_PERSONA['writing_style']}.
        * Techniques:
            - Expand on the key point from the introduction, offering supporting evidence or data.
            - Present a unique angle or viewpoint on the topic, showcasing your expertise.
            - Use vivid language and dynamic sentence structure to keep the reader engaged.

    4. Value Proposition (20% of content, aim for 10-20 words):
        * Purpose: Demonstrate why this topic matters to the reader.
        * Consider {USER_PERSONA['name']}'s audience of {USER_PERSONA['typical_audience']}.
        * Techniques:
            - Explain the potential benefits or drawbacks of the information presented.
            - Highlight the real-world implications or consequences of the topic.
            - Connect the topic to the reader's interests or concerns.

    5. Call to Action (5% of content, aim for 8 words or less):
        * Purpose: Encourage interaction and discussion around the topic.
        * Use a {USER_PERSONA['writing_style']} tone.
        * Techniques:
            - **Craft a call to action that directly relates to the status update's main topic or argument, making it clear why the reader should engage.**
            - **Use a concise and engaging phrase that prompts a response from the audience. You can use a question or a statement that encourages interaction.**

    IMPORTANT RULE: The status update can contain a maximum of two questions. Status updates with more than two questions will be automatically rejected.

    Additional Guidelines:
    - **Ensure the update is between 450 and 500 characters.**
    - Only produce text content. No images or non-text elements.
    - **Hashtags are strictly forbidden in Threads.net status updates. Do NOT include any hashtags in your draft.** 
    - Do NOT use links, or URLs.
    - Do NOT mention or imply additional information beyond what's in the status update.
    - Be opinionated and take a clear stance on the topic.
    - Focus on using abbreviations, compared to long technical jargon.
    - Do not write a title or heading.
    - Write in 1 paragraph only. This means NO new lines, NO multiple paragraphs, just a single block of text.
    - Do not include any subheadings.
    - Avoid using language that sounds promotional, salesy, or like a PR piece.  
    - Focus on being informative, engaging, and providing value to the reader.
    - Use concise language. Avoid unnecessarily long names, phrases, or technical terms. 
    - If a shorter word or phrase conveys the same meaning, use it.
    - Prioritize clarity and impact over wordiness.
    * **Grammar and Mechanics:** Is the draft completely free of grammatical errors, spelling mistakes, and punctuation issues? Ensure that sentences are well-structured, words are spelled correctly, and punctuation is used appropriately.
        - **If you find any grammatical errors, spelling mistakes, or punctuation issues, automatically give the draft a score of 0.** 

    To ensure conciseness, consider these techniques:
    - Use strong verbs and active voice.
    - Eliminate unnecessary words and phrases. 
    - Replace long phrases with shorter equivalents.
    - Prioritize the most impactful information.
    - Focus on the core message and key details.

    Please provide your text-only, opinionated status update following these instructions, incorporating insights from the researcher, addressing editor feedback, and ensuring factual accuracy. Remember to create a status update that is tailored to {USER_PERSONA['name']}'s persona and preferences. 

    Enclose your status update within triple backticks (```). For example:
    ```This is an example of a status update enclosed in triple backticks.```
    """

    completion = client.chat.completions.create(
        model=LLM_MODEL, # Using the global LLM_MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        seed=42,
        max_tokens=185
    )
    new_draft = completion.choices[0].message.content

   # Extract text within triple backticks (if present)
    match = re.search(r'```(.*?)```', new_draft, re.DOTALL)
    if match:
        new_draft = match.group(1).strip()
    else:
        print("Warning: No triple backticks found in the LLM's response. Asking the LLM to regenerate the draft.")
        
        # Ask the LLM to regenerate the draft with triple backticks
        regeneration_prompt = f"""
        Your previous response did not include the generated status update within triple backticks. 
        Please regenerate the status update and ensure you enclose it within triple backticks (```). 

        Here is the original prompt:
        {prompt} 
        """
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": regeneration_prompt}],
            temperature=0.7,
        )
        new_draft = completion.choices[0].message.content

        # Try extracting the draft again (using triple backticks)
        match = re.search(r'```(.*?)```', new_draft, re.DOTALL)
        if match:
            new_draft = match.group(1).strip()
        else:
            print("Error: The LLM failed to generate the draft within triple backticks again. Using the full response.")
            # Use the full response as a fallback
            new_draft = completion.choices[0].message.content

# Conditional check for question marks (with error handling)
    try:
        question_mark_count = new_draft.count('?')
        if question_mark_count > 2:  # Changed limit to 2
            print(f"The Writer is making further revisions. The draft contains {question_mark_count} question marks, exceeding the limit of 2.\n")
            
            # Extract and highlight questions
            sentences = re.split(r'[.?!]', new_draft)
            question_sentences = [sentence.strip() for sentence in sentences if "?" in sentence]
            highlighted_questions = "\n".join([f"- **{sentence}**" for sentence in question_sentences])
            
            excess_questions = question_mark_count - 2  # Adjusted excess calculation
            state["editor_feedback"] += f"""
            The draft contains too many question marks ({question_mark_count}). You have exceeded the limit of 2 questions by {excess_questions} question(s).
            
            The following sentences contain questions:
            
            {highlighted_questions}
            
            Remember, a Threads status update should ideally have a maximum of two questions. 
            To help you revise: Consider removing or combining these questions, or rephrasing some as statements.
            """
            return {"status": "editing", "current_draft": new_draft}

    except AttributeError as e:
        print(f"Error: An AttributeError occurred during the question mark check: {e}")
        print("This might indicate an issue with the generated draft. Returning to editing.")
        state["editor_feedback"] += "\nAn error occurred during processing. Please try generating the draft again."
        return {"status": "editing", "current_draft": new_draft}

    char_count = len(new_draft) 
    print(f"Writer's Draft: {new_draft}")

    # Character count check 
    if 450 <= char_count <= 500: 
        state["versions"].append(new_draft)
        print("The Writer has finished and is sending the draft to the Editor.\n")
        return {"draft": new_draft, "current_draft": new_draft, "character_count": char_count, "status": "ready_for_editor"}

    else:
        if char_count < 450:
            missing_chars = 450 - char_count
            print(f"The Writer is making further revisions to meet the character limit. The draft is {missing_chars} characters too short.\n")
            state["editor_feedback"] += f"""
            The draft is {missing_chars} characters too short. The current character count is {char_count}. Aim for a length between 450 and 500 characters.

            To help you revise: Consider elaborating on these areas:
            - Provide more context or background information about the topic.
            - Add details or examples to support your main points.
            - Expand the call to action to make it more engaging. 
            """
        else: # char_count > 500
            excess_chars = char_count - 500
            print(f"The Writer is making further revisions to meet the character limit. The draft is {excess_chars} characters too long.\n")
            state["editor_feedback"] += f"""
            The draft is {excess_chars} characters too long. The current character count is {char_count}. Aim for a length between 450 and 500 characters.

            To help you revise: Consider condensing these areas:
            - Shorten phrases or use abbreviations where appropriate.
            - Remove unnecessary words or redundant information. 
            - Focus on the most critical points and streamline the message. 
            """

        return {"status": "editing", "current_draft": new_draft}

def editor(state: StatusUpdateState) -> StatusUpdateState:
    state.update(increment_and_check_iterations(state))
    print("The Editor is reviewing the draft...\n")
    prompt = f"""
    You are a professional editor reviewing a text-only status update for Threads.net, specifically for **{USER_PERSONA['name']}**, whose persona is described below: 

    User Persona:
    {USER_PERSONA}


    Your goal is to collaboratively work with the writer to produce a high-quality status update. Provide constructive feedback to improve the draft while ensuring it adheres to the following guidelines:

    Draft: {state['draft']}

    Review the draft based on the following criteria and provide a score from 0 to 10, where 0 is the *lowest possible score* and 10 is the *highest possible score*. 

    A score of 6 or lower indicates significant issues that need to be addressed. 
    A score of 7-8 indicates a good draft with some areas for improvement.
    A score of 9-10 indicates an excellent draft that meets all the criteria. 

    Review Criteria:
    * **Hook:** Does it capture attention with a compelling fact, statistic, or provocative question? Is it relevant to {USER_PERSONA['name']}'s interests?
    * **Introduction:** Does it briefly summarize the key point of the news? Is it in line with {USER_PERSONA['name']}'s preferred writing style?
    * **Main Content:** Does it expand on the introduction with details, insights, or analysis? Does it reflect {USER_PERSONA['name']}'s knowledge and opinions on the topic?
    * **Value Proposition:** Does it highlight the significance or impact of the news? Does it resonate with {USER_PERSONA['name']}'s target audience?
    * **Call to Action:** Does it effectively encourage discussion and engagement? Does it avoid sounding promotional or salesy? Does it align with {USER_PERSONA['name']}'s casual and engaging writing style?
    * **Tone:** Is the tone neutral, informative, and engaging? Does it avoid being overly promotional, salesy, or PR-like? Is it consistent with {USER_PERSONA['name']}'s typically {USER_PERSONA['writing_style']} style?
    * **Grammar and Mechanics:** Is the draft completely free of grammatical errors, spelling mistakes, and punctuation issues? Ensure that sentences are well-structured, words are spelled correctly, and punctuation is used appropriately. 
    * **Questions:**  Does the draft contain no more than two questions? 

    Additional Guidelines:
    - Content Type: Is it text-only, without images or extraneous elements?
    - No External References: Does it avoid using hashtags, links, or URLs?
    - Conciseness: Is the language clear and concise, avoiding jargon?
    - Opinion: Does it express a clear and opinionated stance, as is characteristic of {USER_PERSONA['name']}'s writing?
    - Structure: Is it written in a single paragraph without subheadings or titles? 

    Feedback Instructions:
    * Provide specific suggestions for improvement, including examples or rephrasing ideas.
    * Highlight both the strengths and weaknesses of the draft.
    * Deliver your feedback in a professional and respectful tone.
    * Clearly state the score you assigned to the draft.
    * Do not suggest adding hashtags. 
    * **Never propose a potential version of the status update. Your role is strictly to analyze and provide feedback, not to write or suggest revisions.**

    Example:
    Score: 7
    Feedback: The draft is well-written and engaging, but the hook could be stronger. Consider starting with a more surprising statistic or a thought-provoking question that aligns with {USER_PERSONA['name']}'s interests in {', '.join(USER_PERSONA['topics_of_interest']['tech'])}.

    Ensure the status update is tailored to {USER_PERSONA['name']}'s persona, preferences, and target audience. Consider their interests in {', '.join(USER_PERSONA['topics_of_interest']['tech'])} and their {USER_PERSONA['writing_style']}.
    """
    completion = client.chat.completions.create(
        model=LLM_MODEL, # Using the global LLM_MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    feedback = completion.choices[0].message.content
    print(f"Editor Feedback: {feedback}")

    # Extract the score from the feedback
    score = extract_score(feedback) 
    print(f"Editor Score: {score}")

    # Append feedback to editor_history
    state["editor_history"].append(feedback)

    if score > 7:
        end_time = datetime.now()
        print(f"Editor approval time: {end_time.strftime('%H:%M:%S')}")

        # Convert start_time to datetime object if it's a float
        if isinstance(state["start_time"], float):
            state["start_time"] = datetime.fromtimestamp(state["start_time"])

        # Calculate duration using datetime
        duration = end_time - state["start_time"]
        duration_minutes = int(duration.total_seconds() // 60)
        remaining_seconds = duration.total_seconds() % 60

        print(f"Time from initial draft to editor approval: {duration_minutes} minutes and {remaining_seconds:.2f} seconds")

        print("The Editor has approved the draft. Sending it to the User for final approval.\n")
        return {"status": "user_approval", "editor_feedback": feedback}
    else:
        print("The Editor has requested revisions. Sending the draft back to the Writer.\n")
        return {"status": "needs_revision", "editor_feedback": feedback}

# Helper Function to Extract Score:
def extract_score(feedback: str) -> int:
    """Extracts the score from the editor's feedback."""

    # Try different patterns to find the score
    patterns = [
        r"Score:\s*(\d+)",              # "Score: 8"
        r"Score\s*is\s*(\d+)",          # "Score is 8"
        r"Score\s*-\s*(\d+)",          # "Score - 8"
        r"\*\*Score:\*\*\s*(\d+)",     # "**Score:** 8"
        r"Score\s*:\s*\*\*(\d+)\*\*",  # "Score: **8**"
        r"Rated\s*(\d+)\s*\/\s*10",    # "Rated 8 / 10"
        r"(\d+)\s*out\s*of\s*10",     # "8 out of 10"
        r"\*\*Score:\s*(\d+)\/10\*\*",  # "**Score: 9/10**"
        # Add more patterns as needed based on observed LLM responses
    ]

    for pattern in patterns:
        match = re.search(pattern, feedback, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # If no score is found, return 0 and print a warning
    print("Warning: No score found in editor feedback. Assuming needs revision.")
    return 0

def should_continue(state: StatusUpdateState) -> str:
    print(f"Deciding next step. Current status: {state['status']}")
    if state["iteration_count"] > 30:
        return END
    if state["status"] == "approved":
        return END
    elif state["status"] == "draft_submitted":
        return "writer" # Updated flow
    elif state["status"] == "needs_revision":
        return "writer"  
    elif state["status"] == "ready_for_editor":
        return "editor"
    elif state["status"] == "user_approval":
        return "user"
    elif state["status"] == "editing":
        return "writer"
    else:
        print(f"Error: Unhandled status '{state['status']}' in should_continue function.")
        return END

# Create the graph
workflow = StateGraph(StatusUpdateState)

# Add nodes
workflow.add_node("user", user)
workflow.add_node("writer", writer)
workflow.add_node("editor", editor)

# Set up the flow
workflow.set_entry_point("user")
workflow.add_conditional_edges("user", should_continue)
workflow.add_conditional_edges("writer", should_continue)
workflow.add_conditional_edges("editor", should_continue)

# Compile the graph
app = workflow.compile()

def main():
    # Initialize the state with an empty initial draft.
    # The user will be prompted for the draft within the 'user' node function.
    initial_draft = ""

    # Initialize the state
    initial_state = {
        "messages": [SystemMessage(content="You are helping create a status update.")],
        "draft": initial_draft,
        "current_draft": "",
        "character_count": len(initial_draft),
        "status": "initial",
        "versions": [initial_draft],
        "editor_feedback": "",
        "iteration_count": 0,  
        "editor_history": [],
        "start_time": 0.0
    }

    # Run the graph with increased recursion limit
    app_with_config = app.with_config({"recursion_limit": 500})
    result = app_with_config.invoke(initial_state)

    # Print the final result
    print("\nFinal State:")
    print(f"Approved Draft: {result['draft']}")
    print(f"Character Count: {result['character_count']}")
    print(f"Final Status: {result['status']}")
    print(f"Total Iterations: {result['iteration_count']}")
    print("\nVersion History:")
    for i, version in enumerate(result['versions'], 1):
        print(f"Version {i}: {version[:50]}...")  # Print first 50 characters of each version
    print("\nFinal Editor Feedback:")
    print(result.get('editor_feedback', 'No editor feedback available'))
    print("\nMessages:")
    for message in result['messages']:
        print(f"- {message.content}")

if __name__ == "__main__":
    main()
