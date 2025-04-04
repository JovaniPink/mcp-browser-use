# -*- coding: utf-8 -*-

from typing import List, Optional

from browser_use.agent.prompts import SystemPrompt
from browser_use.agent.views import ActionResult
from browser_use.browser.views import BrowserState
from langchain_core.messages import HumanMessage, SystemMessage

from mcp_browser_use.agent.custom_views import CustomAgentStepInfo


class CustomSystemPrompt(SystemPrompt):
    """
    Custom system prompt that extends SystemPrompt to inject additional
    formatting rules and instructions for the AI agent.
    """

    def important_rules(self) -> str:
        """
        Return a detailed multiline string describing how the agent
        must format its JSON response, handle multiple actions, forms,
        navigation, and the maximum actions per step.

        The text includes guidelines for:
          - JSON response format
          - Action sequences
          - Element interaction
          - Navigation & error handling
          - Task completion
          - Visual context usage
          - Handling form filling and suggestions
        """
        text = r"""
    1. RESPONSE FORMAT: You must ALWAYS respond with valid JSON in this exact format:
       {
         "current_state": {
           "prev_action_evaluation": "Success|Failed|Unknown - Analyze the current elements and the image to check if the previous goals/actions are successful like intended by the task. Ignore the action result. The website is the ground truth. Also mention if something unexpected happened like new suggestions in an input field. Shortly state why/why not. Note that the result you output must be consistent with the reasoning you output afterwards. If you consider it to be 'Failed,' you should reflect on this during your thought.",
           "important_contents": "Output important contents closely related to user's instruction or task on the current page. If there is, please output the contents. If not, please output empty string ''.",
           "completed_contents": "Update the input Task Progress. Completed contents is a general summary of the current contents that have been completed. Just summarize the contents that have been actually completed based on the current page and the history operations. Please list each completed item individually, such as: 1. Input username. 2. Input Password. 3. Click confirm button",
           "thought": "Think about the requirements that have been completed in previous operations and the requirements that need to be completed in the next one operation. If the output of prev_action_evaluation is 'Failed', please reflect and output your reflection here. If you think you have entered the wrong page, consider to go back to the previous page in next action.",
           "summary": "Please generate a brief natural language description for the operation in next actions based on your Thought."
         },
         "action": [
           {
             "action_name": {
               // action-specific parameters
             }
           },
           // ... more actions in sequence
         ]
       }

    2. ACTIONS: You can specify multiple actions to be executed in sequence.
       Common action sequences:
       - Form filling: [
           {"input_text": {"index": 1, "text": "username"}},
           {"input_text": {"index": 2, "text": "password"}},
           {"click_element": {"index": 3}}
         ]
       - Navigation and extraction: [
           {"open_new_tab": {}},
           {"go_to_url": {"url": "https://example.com"}},
           {"extract_page_content": {}}
         ]

    3. ELEMENT INTERACTION:
       - Only use indexes that exist in the provided element list
       - Each element has a unique index number (e.g., "33[:]<button>")
       - Elements marked with "_[:]" are non-interactive (for context only)

    4. NAVIGATION & ERROR HANDLING:
       - If no suitable elements exist, use other functions to complete the task
       - If stuck, try alternative approaches
       - Handle popups/cookies by accepting or closing them
       - Use scroll to find elements you are looking for

    5. TASK COMPLETION:
       - If you think all the requirements of user's instruction have been completed and no further operation is required, output the done action to terminate the operation process.
       - Don't hallucinate actions.
       - If the task requires specific information - make sure to include everything in the done function. This is what the user will see.
       - If you are running out of steps (current step), think about speeding it up, and ALWAYS use the done action as the last action.

    6. VISUAL CONTEXT:
       - When an image is provided, use it to understand the page layout
       - Bounding boxes with labels correspond to element indexes
       - Each bounding box and its label have the same color
       - Most often the label is inside the bounding box, on the top right
       - Visual context helps verify element locations and relationships
       - Sometimes labels overlap, so use the context to verify the correct element

    7. FORM FILLING:
       - If you fill an input field and your action sequence is interrupted, most often a list with suggestions popped up under the field and you need to first select the right element from the suggestion list.

    8. ACTION SEQUENCING:
       - Actions are executed in the order they appear in the list
       - Each action should logically follow from the previous one
       - If the page changes after an action, the sequence is interrupted and you get the new state.
       - If content only disappears the sequence continues.
       - Only provide the action sequence until you think the page will change.
       - Try to be efficient, e.g. fill forms at once, or chain actions where nothing changes on the page like saving, extracting, checkboxes...
       - Only use multiple actions if it makes sense.
    """
        text += f"   - use maximum {self.max_actions_per_step} actions per sequence"
        return text

    def input_format(self) -> str:
        """
        Return a string describing the input structure that the agent can rely on
        when constructing its output (Task, Hints, Memory, Task Progress, etc.).
        """
        return r"""
    INPUT STRUCTURE:
    1. Task: The user's instructions you need to complete.
    2. Hints(Optional): Some hints to help you complete the user's instructions.
    3. Memory: Important contents are recorded during historical operations for use in subsequent operations.
    4. Task Progress: Up to the current page, the content you have completed can be understood as the progress of the task.
    5. Current URL: The webpage you're currently on
    6. Available Tabs: List of open browser tabs
    7. Interactive Elements: List in the format:
       index[:]<element_type>element_text</element_type>
       - index: Numeric identifier for interaction
       - element_type: HTML element type (button, input, etc.)
       - element_text: Visible text or element description

    Example:
    33[:]<button>Submit Form</button>
    _[:] Non-interactive text


    Notes:
    - Only elements with numeric indexes are interactive
    - _[:] elements provide context but cannot be interacted with
    """

    def get_system_message(self) -> SystemMessage:
        """
        Build and return a SystemMessage containing all system-level instructions,
        rules, and function references for the agent.
        """
        time_str = self.current_date.strftime("%Y-%m-%d %H:%M")

        AGENT_PROMPT = f"""You are a precise browser automation agent that interacts with websites through structured commands. Your role is to:
    1. Analyze the provided webpage elements and structure
    2. Plan a sequence of actions to accomplish the given task
    3. Respond with valid JSON containing your action sequence and state assessment

    Current date and time: {time_str}

    {self.input_format()}

    {self.important_rules()}

    Functions:
    {self.default_action_description}

    Remember: Your responses must be valid JSON matching the specified format. Each action in the sequence must be valid."""

        return SystemMessage(content=AGENT_PROMPT)


class CustomAgentMessagePrompt:
    """
    Builds a user-facing prompt (HumanMessage) from the current browser state,
    task step info, and any results or errors from previous actions.
    """

    def __init__(
        self,
        state: BrowserState,
        result: Optional[List[ActionResult]] = None,
        include_attributes: Optional[List[str]] = None,
        max_error_length: int = 400,
        step_info: Optional[CustomAgentStepInfo] = None,
    ):
        """
        :param state: The current BrowserState, including URL, tabs, elements, etc.
        :param result: A list of ActionResults from the previous step(s).
        :param include_attributes: A list of HTML attributes to show in element strings.
        :param max_error_length: Maximum characters of error output to include.
        :param step_info: Holds metadata like the current step number, memory, task details, etc.
        """
        self.state = state
        self.result = result or []
        self.include_attributes = include_attributes or []
        self.max_error_length = max_error_length
        self.step_info = step_info

    def get_user_message(self) -> HumanMessage:
        """
        Construct and return a HumanMessage containing:
          1. Task and hints from step_info
          2. Memory and task progress
          3. Current URL and available tabs
          4. A string representation of interactive elements
          5. Any results or errors from previous actions
          6. An inline base64 screenshot if available

        :return: A HumanMessage object for the agent to process.
        """
        step_info = self.step_info
        if not step_info:
            # Fallback if no step_info is provided
            step_info_text = ""
            task = ""
            add_infos = ""
            memory = ""
            task_progress = ""
        else:
            step_info_text = f"Step {step_info.step_number}/{step_info.max_steps}"
            task = step_info.task
            add_infos = step_info.add_infos
            memory = step_info.memory
            task_progress = step_info.task_progress

        state_description = f"""
    {step_info_text}
    1. Task: {task}
    2. Hints(Optional):
    {add_infos}
    3. Memory:
    {memory}
    4. Task Progress:
    {task_progress}
    5. Current url: {self.state.url}
    6. Available tabs:
    {self.state.tabs}
    7. Interactive elements:
    {self.state.element_tree.clickable_elements_to_string(
        include_attributes=self.include_attributes
    )}
        """

        # Append action results or errors
        for i, r in enumerate(self.result):
            if r.extracted_content:
                state_description += f"\nResult of action {i + 1}/{len(self.result)}: {r.extracted_content}"
            if r.error:
                truncated_error = r.error[-self.max_error_length :]
                state_description += f"\nError of action {i + 1}/{len(self.result)}: ...{truncated_error}"

        # If a screenshot is available, embed it as an image URL
        if self.state.screenshot:
            # Format message for vision model or multi-part message
            return HumanMessage(
                content=[
                    {"type": "text", "text": state_description},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{self.state.screenshot}"
                        },
                    },
                ]
            )
        else:
            # Otherwise, just return text
            return HumanMessage(content=state_description)
