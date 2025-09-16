# -*- coding: utf-8 -*-

import json
import logging
import traceback
from typing import Any, List, Optional, Type

import base64
import io
import os
from PIL import Image, ImageDraw, ImageFont

from browser_use.agent.prompts import SystemPrompt
from browser_use.agent.service import Agent
from browser_use.agent.views import (
    ActionResult,
    AgentHistoryList,
    AgentOutput,
    AgentHistory,
)
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserStateHistory
from browser_use.controller.service import Controller
from browser_use.telemetry.views import AgentEndTelemetryEvent, AgentRunTelemetryEvent
from browser_use.utils import time_execution_async
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.base import _convert_message_to_dict

from mcp_browser_use.utils.agent_state import AgentState
from mcp_browser_use.agent.custom_massage_manager import CustomMassageManager
from mcp_browser_use.agent.custom_views import CustomAgentOutput, CustomAgentStepInfo

logger = logging.getLogger(__name__)


class CustomAgent(Agent):
    """
    An AI-driven Agent that uses a language model to determine browser actions,
    interacts with a BrowserContext, and manages conversation history and state.
    """

    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        add_infos: str = "",
        browser: Optional[Browser] = None,
        browser_context: Optional[BrowserContext] = None,
        controller: Optional[Controller] = None,
        use_vision: bool = True,
        save_conversation_path: Optional[str] = None,
        max_failures: int = 5,
        retry_delay: int = 10,
        system_prompt_class: Type[SystemPrompt] = SystemPrompt,
        max_input_tokens: int = 13000,
        validate_output: bool = False,
        include_attributes: tuple[str, str, str, str, str, str, str, str, str, str] = (
            "title",
            "type",
            "name",
            "role",
            "tabindex",
            "aria-label",
            "placeholder",
            "value",
            "alt",
            "aria-expanded",
        ),
        max_error_length: int = 400,
        max_actions_per_step: int = 10,
        tool_call_in_content: bool = True,
        agent_state: Optional[AgentState] = None,
    ):
        """
        :param task: Main instruction or goal for the agent.
        :param llm: The large language model (BaseChatModel) used for reasoning.
        :param add_infos: Additional information or context to pass to the agent.
        :param browser: Optional Browser instance.
        :param browser_context: Optional BrowserContext to share state.
        :param controller: Optional controller for handling multi-step actions. A new
            controller is created when not provided.
        :param use_vision: Whether to use vision-based element detection.
        :param save_conversation_path: File path to store conversation logs.
        :param max_failures: Max consecutive failures allowed before aborting.
        :param retry_delay: Delay between retries (not currently used).
        :param system_prompt_class: System prompt class for the agent.
        :param max_input_tokens: Token limit for model input.
        :param validate_output: Whether to validate final output at each step.
        :param include_attributes: HTML attributes to include in vision logic.
        :param max_error_length: Max length for error messages.
        :param max_actions_per_step: Limit the number of actions agent can perform per step.
        :param tool_call_in_content: Whether tool calls are in the raw model content.
        :param agent_state: Shared state to detect external stop signals, store last valid state, etc.
        """
        controller = controller or Controller()
        self.controller = controller

        super().__init__(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            use_vision=use_vision,
            save_conversation_path=save_conversation_path,
            max_failures=max_failures,
            retry_delay=retry_delay,
            system_prompt_class=system_prompt_class,
            max_input_tokens=max_input_tokens,
            validate_output=validate_output,
            include_attributes=include_attributes,
            max_error_length=max_error_length,
            max_actions_per_step=max_actions_per_step,
            tool_call_in_content=tool_call_in_content,
        )
        self.add_infos = add_infos
        self.agent_state = agent_state

        # Custom message manager
        self.message_manager = CustomMassageManager(
            llm=self.llm,
            task=self.task,
            action_descriptions=self.controller.registry.get_prompt_description(),
            system_prompt_class=self.system_prompt_class,
            max_input_tokens=self.max_input_tokens,
            include_attributes=self.include_attributes,
            max_error_length=self.max_error_length,
            max_actions_per_step=self.max_actions_per_step,
            tool_call_in_content=tool_call_in_content,
        )

    def _setup_action_models(self) -> None:
        """
        Setup dynamic action models from the controller's registry.
        This ensures the agent's output schema matches all possible actions.
        """
        # Get the dynamic action model from controller's registry
        self.ActionModel = self.controller.registry.create_action_model()
        # Create output model with the dynamic actions
        self.AgentOutput = CustomAgentOutput.type_with_custom_actions(self.ActionModel)

    def _log_response(self, response: CustomAgentOutput) -> None:
        """
        Log the model's response in a human-friendly way.
        Shows success/fail state, memory, thought, summary, etc.
        """
        evaluation = response.current_state.prev_action_evaluation or ""
        if "Success" in evaluation:
            emoji = "✅"
        elif "Failed" in evaluation:
            emoji = "❌"
        else:
            emoji = "🤷"

        logger.info(f"{emoji} Eval: {evaluation}")
        logger.info(f"🧠 New Memory: {response.current_state.important_contents}")
        logger.info(f"⏳ Task Progress: {response.current_state.completed_contents}")
        logger.info(f"🤔 Thought: {response.current_state.thought}")
        logger.info(f"🎯 Summary: {response.current_state.summary}")

        for i, action in enumerate(response.action):
            logger.info(
                f"🛠️  Action {i + 1}/{len(response.action)}: "
                f"{action.model_dump_json(exclude_unset=True)}"
            )

    def update_step_info(
        self,
        model_output: CustomAgentOutput,
        step_info: Optional[CustomAgentStepInfo] = None,
    ) -> None:
        """
        Update the current step with new memory and completed contents.

        :param model_output: Parsed output from the LLM.
        :param step_info: Step information object, if any.
        """
        if step_info is None:
            return

        step_info.step_number += 1
        important_contents = model_output.current_state.important_contents
        if (
            important_contents
            and "None" not in important_contents
            and important_contents not in step_info.memory
        ):
            step_info.memory += important_contents + "\n"

        completed_contents = model_output.current_state.completed_contents
        if completed_contents and "None" not in completed_contents:
            step_info.task_progress = completed_contents

    @time_execution_async("--get_next_action")
    async def get_next_action(self, input_messages: List[BaseMessage]) -> AgentOutput:
        """
        Get the next action from the LLM, attempting structured output parsing.
        Falls back to manual JSON parsing if structured parse fails.
        """
        logger.info("Getting next action from LLM")
        logger.debug(f"Input messages: {input_messages}")

        try:
            if isinstance(self.llm, ChatOpenAI):
                # For OpenAI, attempt structured parse with "instructor" first
                parsed_output = await self._handle_openai_structured_output(
                    input_messages
                )
            else:
                logger.info(f"Using non-OpenAI model: {type(self.llm).__name__}")
                parsed_output = await self._handle_non_openai_structured_output(
                    input_messages
                )

            self._truncate_and_log_actions(parsed_output)
            self.n_steps += 1
            return parsed_output

        except Exception as e:
            logger.warning(f"Error getting structured output: {str(e)}")
            logger.info("Attempting fallback to manual parsing")
            return await self._fallback_parse(input_messages)

    async def _handle_openai_structured_output(
        self, input_messages: List[BaseMessage]
    ) -> AgentOutput:
        """
        Attempt to get structured output from an OpenAI LLM
        using the 'instructor' library. If that fails, fallback
        to the default structured output approach.
        """
        logger.info("Using OpenAI chat model")
        # Usually safe to import here to avoid circular import issues
        from instructor import from_openai

        try:
            client = from_openai(self.llm.root_async_client)
            logger.debug(f"Using model: {self.llm.model_name}")
            messages = [_convert_message_to_dict(msg) for msg in input_messages]

            parsed_response = await client.chat.completions.create(
                messages=messages,
                model=self.llm.model_name,
                response_model=self.AgentOutput,
            )
            logger.debug(f"Raw OpenAI response: {parsed_response}")

            return parsed_response

        except Exception as e:
            # Attempt default structured output if instructor fails
            logger.error(f"Error with 'instructor' approach: {str(e)}")
            logger.info("Using default structured output approach.")

            structured_llm = self.llm.with_structured_output(
                self.AgentOutput, include_raw=True
            )
            response: dict[str, Any] = await structured_llm.ainvoke(input_messages)
            logger.debug(f"Raw LLM response (default approach): {response}")
            return response["parsed"]  # type: ignore

    async def _handle_non_openai_structured_output(
        self, input_messages: List[BaseMessage]
    ) -> AgentOutput:
        """
        For non-OpenAI models, we directly use the structured LLM approach.
        """
        structured_llm = self.llm.with_structured_output(
            self.AgentOutput, include_raw=True
        )
        response: dict[str, Any] = await structured_llm.ainvoke(input_messages)
        logger.debug(f"Raw LLM response: {response}")
        return response["parsed"]  # type: ignore

    async def _fallback_parse(self, input_messages: List[BaseMessage]) -> AgentOutput:
        """
        Manual JSON parsing fallback if structured parse fails.
        Tries to extract JSON from the raw text and parse into AgentOutput.
        """
        try:
            ret = await self.llm.ainvoke(input_messages)
            logger.debug(f"Raw fallback response: {ret}")

            content = ret.content
            if isinstance(content, list):
                # If content is a list, parse from the first element
                parsed_json = json.loads(
                    content[0].replace("```json", "").replace("```", "")
                )
            else:
                # Otherwise parse from the string
                parsed_json = json.loads(
                    content.replace("```json", "").replace("```", "")
                )

            parsed_output: AgentOutput = self.AgentOutput(**parsed_json)
            if parsed_output is None:
                raise ValueError("Could not parse fallback response.")

            self._truncate_and_log_actions(parsed_output)
            self.n_steps += 1
            logger.info(
                f"Successfully got next action via fallback. Step count: {self.n_steps}"
            )
            return parsed_output

        except Exception as parse_error:
            logger.error(f"Fallback parsing failed: {str(parse_error)}")
            raise

    def _truncate_and_log_actions(self, parsed_output: AgentOutput) -> None:
        """
        Enforce the max_actions_per_step limit and log the response.
        """
        original_action_count = len(parsed_output.action)
        parsed_output.action = parsed_output.action[: self.max_actions_per_step]
        if original_action_count > self.max_actions_per_step:
            logger.warning(
                f"Truncated actions from {original_action_count} to {self.max_actions_per_step}"
            )
        self._log_response(parsed_output)

    def summarize_messages(self) -> bool:
        """
        Summarize message history if it exceeds 5 messages.
        Returns True if summarization occurred, False otherwise.
        """
        stored_messages = self.message_manager.get_messages()
        message_count = len(stored_messages)

        if message_count <= 5:
            logger.debug("Message count <= 5, skipping summarization")
            return False

        logger.info(f"Summarizing {message_count} messages")
        try:
            summarization_prompt = ChatPromptTemplate.from_messages(
                [
                    MessagesPlaceholder(variable_name="chat_history"),
                    (
                        "user",
                        "Distill the above chat messages into a single summary message. "
                        "Include as many specific details as you can.",
                    ),
                ]
            )
            summarization_chain = summarization_prompt | self.llm

            summary_message = summarization_chain.invoke(
                {"chat_history": stored_messages}
            )
            logger.debug(f"Generated summary: {summary_message}")

            self.message_manager.reset_history()
            self.message_manager._add_message_with_tokens(summary_message)  # Consider creating a public method for this
            return True

        except Exception as e:
            logger.error(f"Error during message summarization: {str(e)}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return False

    @time_execution_async("--step")
    async def step(self, step_info: Optional[CustomAgentStepInfo] = None) -> None:
        """
        Execute one step of the task:
        1) Capture browser state
        2) Query LLM for next action
        3) Execute that action(s)
        4) Update logs/history
        """
        logger.info(f"\n📍 Step {self.n_steps}")
        logger.info(f"History token count: {self.message_manager.history.total_tokens}")

        # Optionally summarize to reduce token usage
        # self.summarize_messages()

        state = None
        model_output = None
        result: List[ActionResult] = []

        try:
            state = await self.browser_context.get_state(use_vision=self.use_vision)
            self.message_manager.add_state_message(state, self._last_result, step_info)
            input_messages = self.message_manager.get_messages()

            model_output = await self.get_next_action(input_messages)
            self.update_step_info(model_output, step_info)
            logger.info(f"🧠 All Memory: {getattr(step_info, 'memory', '')}")

            self._save_conversation(input_messages, model_output)
            # Remove the last state message from chat history to prevent bloat
            self.message_manager._remove_last_state_message()
            self.message_manager.add_model_output(model_output)

            # Execute the requested actions
            result = await self.controller.multi_act(
                model_output.action, self.browser_context
            )
            self._last_result = result

            # If the last action indicates "is_done", we can log the extracted content
            if len(result) > 0 and result[-1].is_done:
                logger.info(f"📄 Result: {result[-1].extracted_content}")

            self.consecutive_failures = 0

        except Exception as e:
            result = self._handle_step_error(e)
            self._last_result = result

        finally:
            if not result:
                return

            for r in result:
                logger.warning(f"🔧 Action result: {r}")

            if state:
                self._make_history_item(model_output, state, result)

    def create_history_gif(
        self,
        output_path: str = "agent_history.gif",
        duration: int = 3000,
        show_goals: bool = True,
        show_task: bool = True,
        show_logo: bool = False,
        font_size: int = 40,
        title_font_size: int = 56,
        goal_font_size: int = 44,
        margin: int = 40,
        line_spacing: float = 1.5,
    ) -> None:
        """
        Create a GIF from the agent's history using the captured screenshots.
        Overlays text for tasks/goals. Optionally includes a logo.
        """
        if not self.history.history:
            logger.warning("No history to create GIF from")
            return

        if not self.history.history[0].state.screenshot:
            logger.warning(
                "No screenshots in the first history item; cannot create GIF"
            )
            return

        images = []
        try:
            # Attempt to load some preferred fonts
            font_options = ["Helvetica", "Arial", "DejaVuSans", "Verdana"]
            regular_font, title_font, goal_font = None, None, None
            font_loaded = False

            for font_name in font_options:
                try:
                    import platform

                    if platform.system() == "Windows":
                        # On Windows, we may need absolute font paths
                        font_name = os.path.join(
                            os.getenv("WIN_FONT_DIR", "C:\\Windows\\Fonts"),
                            font_name + ".ttf",
                        )

                    regular_font = ImageFont.truetype(font_name, font_size)
                    title_font = ImageFont.truetype(font_name, title_font_size)
                    goal_font = ImageFont.truetype(font_name, goal_font_size)
                    font_loaded = True
                    break
                except OSError:
                    continue

            if not font_loaded:
                raise OSError("No preferred fonts found")

        except OSError:
            # Fallback to default
            regular_font = ImageFont.load_default()
            title_font = regular_font
            goal_font = regular_font

        logo = None
        if show_logo:
            try:
                logo = Image.open("./static/browser-use.png")
                # Resize logo
                logo_height = 150
                aspect_ratio = logo.width / logo.height
                logo_width = int(logo_height * aspect_ratio)
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")

        # If requested, create an initial frame with the entire task
        if show_task and self.task:
            task_frame = self._create_task_frame(
                self.task,
                self.history.history[0].state.screenshot,
                title_font,
                regular_font,
                logo,
                line_spacing,
            )
            images.append(task_frame)

        # Convert each step’s screenshot
        for i, item in enumerate(self.history.history, 1):
            if not item.state.screenshot:
                continue

            img_data = base64.b64decode(item.state.screenshot)
            image = Image.open(io.BytesIO(img_data))

            if show_goals and item.model_output:
                image = self._add_overlay_to_image(
                    image=image,
                    step_number=i,
                    goal_text=item.model_output.current_state.thought,
                    regular_font=regular_font,
                    title_font=title_font,
                    margin=margin,
                    logo=logo,
                    line_spacing=line_spacing,
                )

            images.append(image)

        if images:
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0,
                optimize=False,
            )
            logger.info(f"Created GIF at {output_path}")
        else:
            logger.warning("No images found in history to create GIF")

    def _create_task_frame(
        self,
        task_text: str,
        screenshot_b64: str,
        title_font: ImageFont.FreeTypeFont,
        regular_font: ImageFont.FreeTypeFont,
        logo: Image.Image | None,
        line_spacing: float,
    ) -> Image.Image:
        """Return an image with the task text overlaid on the screenshot."""

        margin = 40
        img = Image.open(io.BytesIO(base64.b64decode(screenshot_b64))).convert(
            "RGBA"
        )

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        max_width = img.width - margin * 2
        text_lines: list[str] = self._wrap_text_to_lines(draw, task_text, regular_font, max_width)

        y = margin
        title_bbox = draw.textbbox((margin, y), "Task", font=title_font)
        title_height = title_bbox[3] - title_bbox[1]
        total_height = title_height + int(margin * 0.5)
        for t in text_lines:
            bbox = draw.textbbox((margin, 0), t, font=regular_font)
            total_height += int((bbox[3] - bbox[1]) * line_spacing)

        if logo:
            total_height = max(total_height, logo.height + margin * 2)

        draw.rectangle(
            [(0, 0), (img.width, total_height)],
            fill=(0, 0, 0, 180),
        )

        draw.text((margin, y), "Task", font=title_font, fill="white")
        y += title_height + int(margin * 0.5)
        for t in text_lines:
            draw.text((margin, y), t, font=regular_font, fill="white")
            bbox = draw.textbbox((margin, y), t, font=regular_font)
            y += int((bbox[3] - bbox[1]) * line_spacing)

        if logo:
            overlay.paste(
                logo,
                (img.width - logo.width - margin, margin),
                logo if logo.mode == "RGBA" else None,
            )

        img.alpha_composite(overlay)
        return img.convert("RGB")

    def _wrap_text_to_lines(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> list[str]:
        """Split ``text`` into lines that fit within ``max_width`` pixels."""

        if not text:
            return []

        if max_width <= 0:
            return [text]

        wrapped_lines: list[str] = []

        lines = text.splitlines()
        if not lines:
            lines = [text]

        for raw_line in lines:
            words = raw_line.split()
            if not words:
                wrapped_lines.append("")
                continue

            current_line = words[0]
            for word in words[1:]:
                candidate = f"{current_line} {word}" if current_line else word
                if draw.textlength(candidate, font=font) <= max_width:
                    current_line = candidate
                else:
                    wrapped_lines.append(current_line)
                    current_line = word

            wrapped_lines.append(current_line)

        return wrapped_lines

    def _add_overlay_to_image(
        self,
        image: Image.Image,
        step_number: int,
        goal_text: str,
        regular_font: ImageFont.FreeTypeFont,
        title_font: ImageFont.FreeTypeFont,
        margin: int,
        logo: Image.Image | None,
        line_spacing: float,  # Added line_spacing parameter
    ) -> Image.Image:
        """Overlay the step number and goal text onto a screenshot image."""

        image = image.convert("RGBA")
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        step_text = f"Step {step_number}"
        max_width = image.width - margin * 2

        lines: list[str] = []
        words = goal_text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textlength(test, font=regular_font) <= max_width:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        y = margin
        step_bbox = draw.textbbox((margin, y), step_text, font=title_font)
        step_height = step_bbox[3] - step_bbox[1]
        total_height = step_height + int(margin * 0.5)
        for l in lines:
            bbox = draw.textbbox((margin, 0), l, font=regular_font)
            total_height += bbox[3] - bbox[1]

        if logo:
            total_height = max(total_height, logo.height + margin * 2)

        draw.rectangle(
            [(0, 0), (image.width, total_height)],
            fill=(0, 0, 0, 180),
        )

        draw.text((margin, y), step_text, font=title_font, fill="white")
        y += step_height + int(margin * 0.5)
        for l in lines:
            draw.text((margin, y), l, font=regular_font, fill="white")
            bbox = draw.textbbox((margin, y), l, font=regular_font)
            y += bbox[3] - bbox[1]

        if logo:
            overlay.paste(
                logo,
                (image.width - logo.width - margin, margin),
                logo if logo.mode == "RGBA" else None,
            )

        image.alpha_composite(overlay)
        return image.convert("RGB")

    async def run(self, max_steps: int = 100) -> AgentHistoryList:
        """
        Execute the entire task for up to max_steps or until 'done'.
        Checks for external stop signals, logs each step in self.history.
        """
        try:
            logger.info(f"🚀 Starting task: {self.task}")
            self.telemetry.capture(
                AgentRunTelemetryEvent(
                    agent_id=self.agent_id,
                    task=self.task,
                )
            )

            step_info = CustomAgentStepInfo(
                task=self.task,
                add_infos=self.add_infos,
                step_number=1,
                max_steps=max_steps,
                memory="",
                task_progress="",
            )

            for step in range(max_steps):
                # 1) Check if stop requested externally
                if self.agent_state and self.agent_state.is_stop_requested():
                    logger.info("🛑 Stop requested by user")
                    self._create_stop_history_item()
                    break

                # 2) Store last valid state
                if self.browser_context and self.agent_state:
                    state = await self.browser_context.get_state(
                        use_vision=self.use_vision
                    )
                    self.agent_state.set_last_valid_state(state)

                # 3) Check for too many failures
                if self._too_many_failures():
                    break

                # 4) Execute one step
                await self.step(step_info)

                if self.history.is_done():
                    if self.validate_output and step < max_steps - 1:
                        # Optionally validate final output
                        if not await self._validate_output():
                            continue
                    logger.info("✅ Task completed successfully")
                    break
            else:
                logger.info("❌ Failed to complete task within maximum steps")

            return self.history

        finally:
            self.telemetry.capture(
                AgentEndTelemetryEvent(
                    agent_id=self.agent_id,
                    task=self.task,
                    success=self.history.is_done(),
                    steps=len(self.history.history),
                )
            )
            # Close the browser context if we created it here (not injected)
            if not self.injected_browser_context and self.browser_context:
                await self.browser_context.close()

            # Close the browser instance if it wasn't injected
            if not self.injected_browser and self.browser:
                await self.browser.close()

            # Generate a GIF of the agent's run if enabled
            if self.generate_gif:
                self.create_history_gif()

    def _create_stop_history_item(self) -> None:
        """
        Create a final 'stop' history item indicating the agent has halted by request.
        """
        try:
            state = None
            if self.agent_state:
                last_state = self.agent_state.get_last_valid_state()
                if last_state:
                    state = self._convert_to_browser_state_history(last_state)
                else:
                    state = self._create_empty_state()
            else:
                state = self._create_empty_state()

            stop_history = AgentHistory(
                model_output=None,
                state=state,
                result=[ActionResult(extracted_content=None, error=None, is_done=True)],
            )
            self.history.history.append(stop_history)

        except Exception as e:
            logger.error(f"Error creating stop history item: {e}")
            state = self._create_empty_state()
            stop_history = AgentHistory(
                model_output=None,
                state=state,
                result=[ActionResult(extracted_content=None, error=None, is_done=True)],
            )
            self.history.history.append(stop_history)

    def _convert_to_browser_state_history(
        self, browser_state: Any
    ) -> BrowserStateHistory:
        """
        Convert a raw browser_state object into a BrowserStateHistory dataclass.
        """
        return BrowserStateHistory(
            url=getattr(browser_state, "url", ""),
            title=getattr(browser_state, "title", ""),
            tabs=getattr(browser_state, "tabs", []),
            interacted_element=[None],
            screenshot=getattr(browser_state, "screenshot", None),
        )

    def _create_empty_state(self) -> BrowserStateHistory:
        """
        Create a basic empty state for fallback or stop-history usage.
        """
        return BrowserStateHistory(
            url="", title="", tabs=[], interacted_element=[None], screenshot=None
        )
