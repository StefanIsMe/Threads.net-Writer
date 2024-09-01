from typing import Annotated, TypedDict, List
import operator
import time
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import re
import os
import google.generativeai as genai
import json
from ratelimit import limits, RateLimitDecorator, RateLimitException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure Gemini Flash globally
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",  # Default mime type is now JSON
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b-exp-0827",
    generation_config=generation_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
)

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
    relevance_score: int
    relevance_feedback: str
    content_type: str # New field for content type


def increment_and_check_iterations(state: StatusUpdateState) -> StatusUpdateState:
    """Increments the iteration count and checks if the maximum limit is reached."""
    state["iteration_count"] += 1
    if state["iteration_count"] > 300:
        print("Maximum overall iterations reached. Forcing completion.")
        return {"status": "approved"}
    return {}


def user(state: StatusUpdateState) -> StatusUpdateState:
    """Handles user interaction for providing the initial draft and final approval."""
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
        print("User has submitted the initial draft. Sending it to the Content Classifier.\n")

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


@RateLimitDecorator(calls=15, period=60)
def make_api_call(prompt):
    """Makes an API call to Google Gemini with rate limiting."""
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    return response.text


def extract_key_points(text):
    """Extracts key points from a text using a simple heuristic (first 3 sentences)."""
    sentences = text.split(". ")
    return ". ".join(sentences[:3]) + "."


def content_classifier(state: StatusUpdateState) -> StatusUpdateState:
    """Classifies the content as industry/general news or personal using a LLM API call."""
    state.update(increment_and_check_iterations(state))
    print("The Content Classifier is analyzing the draft using a LLM...\n")

    initial_draft = state["draft"]

    prompt = f"""
    You are a content classifier tasked with determining whether a given text is more likely to be "industry_news" or "personal" in nature.

    Text:
    {initial_draft}

    Instructions:

    1. Analyze the provided text for thematic and stylistic cues.
    2. Consider the following characteristics:
       - Industry/General News: Typically focuses on topics related to technology, business, politics, or current events. Often uses formal language and avoids personal opinions or anecdotes.
       - Personal: Expresses personal opinions, experiences, thoughts, or feelings. May use informal language, humor, or personal anecdotes.
    3. Choose the category that best describes the overall nature of the text.
    4. Provide your response in JSON format with the following structure:

       ```json
       {{
         "content_type": "your_chosen_category" 
       }}
       ``` 
    """

    try:
        response = make_api_call(prompt)
        content_type_data = json.loads(response)
        content_type = content_type_data["content_type"]
    except RateLimitException:
        print("Rate limit exceeded. Waiting...")
        time.sleep(60)
        response = make_api_call(prompt)
        content_type_data = json.loads(response)
        content_type = content_type_data["content_type"]
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Returning to user for draft resubmission.")
        return {"status": "initial", "editor_feedback": "Error decoding JSON response. Please resubmit your draft."}

    state["content_type"] = content_type
    print(f"Content classified as: {content_type}\n")

    return {"status": "ready_for_writer"}


def writer(state: StatusUpdateState) -> StatusUpdateState:
    """Generates a draft of the status update using Google Gemini."""
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

    # Choose prompt based on content type
    if state["content_type"] == "personal":
        prompt = f"""
        Edit the following into a Threads.net status update: 

        {state['draft']}

        Please avoid using overly enthusiastic or promotional language.
        Ensure the update is between 450 and 500 characters.
        """
    else:  # industry_news
        prompt = f"""
        You are a professional writer crafting a text-only status update for Threads.net, specifically for **{USER_PERSONA['name']}**, whose persona is described below.

        **Your Goal:** Craft a compelling and engaging Threads status update that will resonate with {USER_PERSONA['typical_audience']} and spark discussion about the initial draft provided. **Your primary objective is to refine and enhance the existing draft while preserving its original story, context, and key points.** Avoid introducing new information or significantly altering the narrative. 

        **Concise User Persona Summary:**
        * **Name:** {USER_PERSONA['name']}
        * **Writing Style:** {USER_PERSONA['writing_style']}
        * **Topics of Interest:** {', '.join(USER_PERSONA['topics_of_interest']['tech'])}
        * **Content Preferences:** Posts about {', '.join(USER_PERSONA['content_preferences']['posts_about'])}

        **Original Draft:** {state['draft']}
        **Carefully analyze the original draft to identify its core themes, narrative, and intended message. Use this understanding to guide your revisions, ensuring that you remain faithful to the user's original ideas and intent.**

        **Editor's Feedback:** {editor_feedback}
        **The Editor has reviewed the most recent version of the status update and provided feedback on its strengths and weaknesses. Consider the Editor's suggestions, but prioritize preserving the original story and context.**

        **Previous Versions and Rejection Reasons:**
        {version_history_str}
        **This section contains previous versions of the status update that you attempted to write, along with the reasons why each version was rejected by the Editor or due to exceeding the character limit. Analyze each version and its rejection reason to understand the mistakes that were made and avoid repeating them in your current draft.**

        **Instructions:**

        1. **Identify Core Themes and Narrative:** Before making any changes, carefully read the original draft to identify its central themes, narrative flow, and key arguments.
        2. **Incorporate Editor Feedback:** Consider the Editor's feedback, but prioritize maintaining the original story, context, and user intent. 
        3. **Avoid Past Mistakes:** Review previous versions and rejection reasons to avoid repeating the same errors.
        4. **Content Adherence Check:** Before submitting your draft, compare it to the initial draft. Ensure your draft closely aligns with the original topic and key points, and you have not deviated significantly from the original content.

        **Guidelines for the Perfect Status Update Structure (Tailored for {USER_PERSONA['name']}):

        1. Hook (10% of content, aim for 5-10 words):
            * **Purpose:** Capture the reader's attention immediately. Consider using a surprising statistic, a bold statement, or vivid imagery.
            * **Example:** Instead of saying "AI is changing the world," try "AI is rewriting the rules of business. Are you ready?"
            * **Remember {USER_PERSONA['name']}'s interests:** Align the hook with {USER_PERSONA['name']}'s interest in {', '.join(USER_PERSONA['topics_of_interest']['tech'])}.

        2. Introduction (15% of content, aim for 8-15 words):
            * **Purpose:** Briefly set the stage for the main topic. Concisely summarize the core idea or event.
            * **Example:** If the topic is AI in healthcare, you might say, "AI is revolutionizing healthcare. Here's how."
            * **Maintain {USER_PERSONA['name']}'s writing style:** Keep the introduction professional yet casual, reflecting {USER_PERSONA['name']}'s preferred style.

        3. Main Content (50% of content, aim for 25-40 words):
            * **Purpose:** Dive deeper, providing details, insights, and analysis. Expand on the key point from the introduction.
            * **Example:** You could provide a specific example of AI in healthcare, like "AI-powered diagnostics are improving accuracy and speed."
            * **Showcase Expertise:** Present a unique angle or viewpoint that reflects {USER_PERSONA['name']}'s knowledge of {', '.join(USER_PERSONA['topics_of_interest']['tech'])}.

        4. Value Proposition (20% of content, aim for 10-20 words):
            * **Purpose:** Demonstrate why this topic matters to the reader. Connect it to their interests or concerns.
            * **Example:** Highlight the potential impact of AI in healthcare: "Faster diagnoses mean quicker treatment and better outcomes."
            * **Target the Audience:** Consider what resonates with {USER_PERSONA['typical_audience']}.

        5. Call to Action (5% of content, aim for 8 words or less):
            * **Purpose:** Encourage interaction and discussion. Use a question or a statement that prompts a response.
            * **Example:** "What are your thoughts on AI in healthcare? Share your opinions below!"
            * **Engage the Audience:** Use {USER_PERSONA['writing_style']} to create a casual and engaging call to action.

        **IMPORTANT RULE:** The status update can contain a maximum of **one** question. The question should be placed at the end of the status update and should aim to generate conversation by prompting the reader to think about the content discussed in the status update. 

        **Additional Guidelines:**

        * **Character Limit:** Ensure the update is between 450 and 500 characters.
        * **Content Type:** Text-only; no images or extraneous elements.
        * **No External References:** Do NOT include hashtags, links, or URLs.
        * **Conciseness:** Use abbreviations where appropriate and avoid jargon.
        * **Opinionated Stance:** Be opinionated and take a clear stance on the topic, reflecting {USER_PERSONA['name']}'s typical style.
        * **Structure:** Write in a single paragraph without subheadings or titles.
        * **Avoid Promotional Language:** Focus on being informative, engaging, and providing value to the reader. **Specifically, avoid overly enthusiastic or promotional language, such as "game-changer," "revolutionary," or "groundbreaking."**
        * **Grammar and Mechanics:** Ensure the draft is completely free of grammatical errors, spelling mistakes, and punctuation issues.
        * **Avoid Puns:** Please refrain from using puns in the status update. 

        **IMPORTANT:** Please provide your response in JSON format with the following structure:

        ```json
        {{
          "draft": "your generated status update here"
        }}
        ```
        """

    try:
        response = make_api_call(prompt)
        new_draft_data = json.loads(response)
        new_draft = new_draft_data["draft"]
    except RateLimitException:
        print("Rate limit exceeded. Waiting...")
        time.sleep(60)
        response = make_api_call(prompt)
        new_draft_data = json.loads(response)
        new_draft = new_draft_data["draft"]
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Returning to writer for revision.")
        return {"status": "needs_revision", "editor_feedback": "Error decoding JSON response. Please try again."}

    # --- Post-processing to remove double spaces after full stops ---
    new_draft = new_draft.replace(".  ", ". ")
    new_draft = new_draft.replace(",  ", ", ")
    new_draft = new_draft.replace("?  ", "? ")

    # Conditional check for question marks (with error handling)
    try:
        question_mark_count = new_draft.count('?')
        if question_mark_count > 1:  # Changed limit to 1
            print(f"The Writer is making further revisions. The draft contains {question_mark_count} question marks, exceeding the limit of 1.\n")

            # Extract and highlight questions
            sentences = re.split(r'[.?!]', new_draft)
            question_sentences = [sentence.strip() for sentence in sentences if "?" in sentence]
            highlighted_questions = "\n".join([f"- **{sentence}**" for sentence in question_sentences])

            excess_questions = question_mark_count - 1  # Adjusted excess calculation
            state["editor_feedback"] += f"""
            The draft contains too many question marks ({question_mark_count}). You have exceeded the limit of 1 questions by {excess_questions} question(s).

            The following sentences contain questions:

            {highlighted_questions}

            Remember, a Threads status update should ideally have a maximum of one questions. 
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
        else:  # char_count > 500
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



def relevance_assessor(state: StatusUpdateState) -> StatusUpdateState:
    """Assesses the relevance of the current draft to the initial draft using Google Gemini."""
    state.update(increment_and_check_iterations(state))
    print("The Relevance Assessor is evaluating the draft's relevance to the initial draft...\n")

    initial_draft = state["versions"][0]
    current_draft = state["draft"]

    prompt = f"""
    You are a relevance assessor tasked with evaluating how well a revised text aligns with the core themes and narrative of an initial text.

    **Initial Draft:**
    {initial_draft}

    **Revised Draft:**
    {current_draft}

    **Instructions:**

    1. **Identify Core Themes:** Carefully analyze the initial draft to identify its central themes, main arguments, and overall narrative.
    2. **Assess Alignment:**  Determine how well the revised draft aligns with the core themes and narrative identified in the initial draft.  Consider whether the revised draft:
        * Maintains the same focus and central topic.
        * Presents the same key arguments and information.
        * Avoids introducing significant new information or arguments that were not present in the initial draft.
    3. **Provide a Relevance Score:** Assign a relevance score from 1 to 5, where:
        * **1 - Not Relevant:** The revised draft significantly deviates from the initial draft's core themes and narrative.
        * **2 - Somewhat Relevant:** The revised draft partially aligns with the initial draft but introduces new information or arguments that shift the focus.
        * **3 - Moderately Relevant:** The revised draft generally aligns with the initial draft but may lack depth or clarity in some areas.
        * **4 - Very Relevant:** The revised draft closely aligns with the initial draft, maintaining the core themes and narrative while providing additional details or insights.
        * **5 - Highly Relevant:** The revised draft is an excellent refinement of the initial draft, fully preserving the core themes and narrative while enhancing clarity, conciseness, and engagement. 
    4. **Provide Feedback (Optional):**  If the relevance score is below 4, provide specific feedback explaining the areas where the revised draft deviates from the initial draft.  This feedback should help the writer understand how to better align the draft with the original story.

    **IMPORTANT:** Please provide your response in JSON format with the following structure:

    ```json
    {{
      "relevance_score": your_numerical_score,
      "relevance_feedback": "Your feedback here (optional)" 
    }}
    ``` 
    """

    try:
        response = make_api_call(prompt)
        relevance_data = json.loads(response)
        relevance_score = int(relevance_data["relevance_score"])  # Convert score to integer
        relevance_feedback = relevance_data.get("relevance_feedback", "")
    except RateLimitException:
        print("Rate limit exceeded. Waiting...")
        time.sleep(60)
        response = make_api_call(prompt)
        relevance_data = json.loads(response)
        relevance_score = int(relevance_data["relevance_score"])
        relevance_feedback = relevance_data.get("relevance_feedback", "")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Returning to writer for revision.")
        return {"status": "needs_revision",
                "editor_feedback": "Error decoding JSON response from Relevance Assessor. Please try again."}

    state["relevance_score"] = relevance_score
    state["relevance_feedback"] = relevance_feedback

    print(f"Relevance Score: {relevance_score}")
    print(f"Relevance Feedback: {relevance_feedback}")

    print("The Relevance Assessor has finished. Sending the draft to the Editor.\n")
    return {"status": "ready_for_editor"}


def editor(state: StatusUpdateState) -> StatusUpdateState:
    """Reviews the draft and provides feedback using Google Gemini."""
    state.update(increment_and_check_iterations(state))
    print("The Editor is reviewing the draft...\n")

    key_points = extract_key_points(state['versions'][0])  # Extract key points dynamically

    prompt = f"""
You are a professional editor reviewing a text-only status update for Threads.net, specifically for **{USER_PERSONA['name']}**, whose persona is described below.

**Your Goal:** Collaborate with the writer to improve the draft and ensure it aligns with {USER_PERSONA['name']}'s persona, preferences, and target audience, **while preserving the original story, context, and key points of the initial draft.** Your feedback should focus on refining and enhancing the existing narrative rather than suggesting major rewrites or changes in direction.

**Concise User Persona Summary:**
* **Name:** {USER_PERSONA['name']}
* **Writing Style:** {USER_PERSONA['writing_style']}
* **Topics of Interest:** {', '.join(USER_PERSONA['topics_of_interest']['tech'])}
* **Content Preferences:** Posts about {', '.join(USER_PERSONA['content_preferences']['posts_about'])}
* **Target Audience:** {USER_PERSONA['typical_audience']}

**Draft:** {state['draft']}

**Initial Draft:** {state['versions'][0]} 
**Review the current draft in comparison to the initial draft to ensure that the writer has not strayed too far from the original story, context, and key points. If you detect significant deviations, advise the writer to realign the draft with the user's initial intent.**

**Key Points from Initial Draft:**
{key_points}
**Ensure that the current draft accurately reflects these key points and does not introduce significant new information or arguments that were not present in the initial draft.**

**Review the draft based on the following criteria and provide a score from 1 to 5, where 1 indicates "Needs Significant Improvement" and 5 indicates "Excellent."**

**Scoring Guide:**

* **1 - Needs Significant Improvement:** The draft has major issues that need to be addressed before it can be considered for posting.
* **2 - Needs Improvement:** The draft has several areas that need improvement, but it shows potential.
* **3 - Good with Room for Improvement:** The draft is generally good, but there are still some areas that could be improved.
* **4 - Very Good:** The draft is well-written and engaging, with only minor areas for improvement.
* **5 - Excellent:** The draft is outstanding and meets all the criteria exceptionally well.

**Review Criteria:**

* **Hook:** Does it capture attention with a compelling fact, statistic, or thought-provoking question? Is it relevant to {USER_PERSONA['name']}'s interests?
* **Introduction:** Does it briefly summarize the key point of the topic? Is it in line with {USER_PERSONA['name']}'s preferred writing style?
* **Main Content:** Does it expand on the introduction with details, insights, or analysis? Does it reflect {USER_PERSONA['name']}'s knowledge and opinions on the topic?
* **Value Proposition:** Does it highlight the significance or impact of the topic? Does it resonate with {USER_PERSONA['name']}'s target audience?
* **Call to Action:** Does it effectively encourage discussion and engagement? Does it avoid sounding promotional or salesy? Does it align with {USER_PERSONA['name']}'s casual and engaging writing style?
* **Tone:** Is the tone neutral, informative, and engaging? Does it avoid being overly promotional, salesy, or PR-like? Is it consistent with {USER_PERSONA['name']}'s typically {USER_PERSONA['writing_style']} style? **Specifically, ensure it avoids overly enthusiastic or promotional language, such as "game-changer," "revolutionary," or "groundbreaking."**
* **Grammar and Mechanics:** Is the draft completely free of grammatical errors, spelling mistakes, and punctuation issues? Ensure that sentences are well-structured, words are spelled correctly, and punctuation is used appropriately.
* **Questions:** Does the draft contain no more than **one** question? Is the question placed at the end of the status update?  Does the question effectively encourage thoughtful responses related to the topic?
* **Content Relevance:** Does the draft accurately reflect the core themes and narrative of the initial draft? Does it avoid introducing significant new information or arguments that were not present in the initial draft?

**Positive Feedback:**

* **What are the strengths of this draft? What aspects did the writer do well? Please be specific and provide examples.**

**Feedback Instructions:**

* **Constructive Criticism:** Instead of bullet points or lists, please provide your feedback in a conversational style, using complete sentences and paragraphs. Imagine you are speaking directly to the writer and offering suggestions in a friendly and helpful manner.  
* **Focus on Solutions:** Offer specific solutions or alternative approaches to address any weaknesses.
* **Balance Strengths and Weaknesses:** Highlight both the strengths and weaknesses of the draft to provide a balanced perspective.
* **Professional and Respectful Tone:** Deliver your feedback in a professional and respectful tone, encouraging the writer's growth and development.
* **Avoid Suggesting Hashtags:** Do not suggest adding hashtags.
* **Focus on Feedback, Not Rewriting:** Your role is to analyze and provide feedback, not to write or suggest specific revisions.

**Example (Conversational Feedback Style):**

"Overall, this draft is pretty good! The hook is engaging and the main content is informative. However, the call to action could be a bit more compelling. Maybe try asking a question that directly relates to the reader's experience with AI, something like 'Have you noticed the impact of AI in your daily life?' This might encourage more interaction."

**Ensure the status update is tailored to {USER_PERSONA['name']}'s persona, preferences, and target audience. Consider their interests in {', '.join(USER_PERSONA['topics_of_interest']['tech'])} and their {USER_PERSONA['writing_style']}.**

**IMPORTANT:** Please provide your response in JSON format with the following structure:

```json
{{
  "feedback": "Your feedback here",
  "overall_score": your_numerical_score
}}
```
  """

    try:
        response = make_api_call(prompt)
        feedback_data = json.loads(response)
        feedback = feedback_data["feedback"]
        score = int(feedback_data["overall_score"])  # Convert score to int
    except RateLimitException:
        print("Rate limit exceeded. Waiting...")
        time.sleep(60)  # Wait for 1 minute before retrying
        response = make_api_call(prompt)  # Retry the API call
        feedback_data = json.loads(response)
        feedback = feedback_data["feedback"]
        score = int(feedback_data["overall_score"])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Returning to writer for revision.")
        return {"status": "needs_revision", "editor_feedback": "Error decoding JSON response. Please try again."}

    print(f"Editor Feedback: {feedback}")
    print(f"Editor Score: {score}")

    # Append feedback to editor_history
    state["editor_history"].append(feedback)

    if score >= 4:
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


def should_continue(state: StatusUpdateState) -> str:
    """Determines the next step in the workflow based on the current state."""
    print(f"Deciding next step. Current status: {state['status']}")
    if state["iteration_count"] > 30:
        return END
    if state["status"] == "approved":
        return END
    elif state["status"] == "draft_submitted":
        return "content_classifier" #  New flow
    elif state["status"] == "ready_for_writer":
        return "writer"
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
workflow.add_node("content_classifier", content_classifier) # New node
workflow.add_node("writer", writer)
workflow.add_node("relevance_assessor", relevance_assessor)
workflow.add_node("editor", editor)

# Set up the flow
workflow.set_entry_point("user")
workflow.add_conditional_edges("user", should_continue)
workflow.add_conditional_edges("content_classifier", should_continue) # New edge
workflow.add_conditional_edges("writer", should_continue)
workflow.add_conditional_edges("relevance_assessor", should_continue)
workflow.add_conditional_edges("editor", should_continue)

# Compile the graph
app = workflow.compile()


def main():
    # Initialize the state with an empty initial draft.
    # The user will be prompted for the draft within the 'user' node function.
    initial_draft = ""

    # Initialize the state
    initial_state = {
        "messages": [SystemMessage(content="You are helping create a threads.net status update.")],
        "draft": initial_draft,
        "current_draft": "",
        "character_count": len(initial_draft),
        "status": "initial",
        "versions": [initial_draft],
        "editor_feedback": "",
        "iteration_count": 0,
        "editor_history": [],
        "start_time": 0.0,
        "relevance_score": 0,
        "relevance_feedback": "",
        "content_type": "" # Initialize content type
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
