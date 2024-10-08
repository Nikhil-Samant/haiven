# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import gradio as gr
from knowledge_manager import KnowledgeManager
from prompts.prompts import PromptList
from llms.clients import ChatClientConfig
from prompts.prompts_factory import PromptsFactory
from llms.chats import ChatOptions, ChatManager
from ui.chat_context import ChatContext
from user_feedback import UserFeedback
from ui.user_context import user_context


def enable_brainstorming(
    knowledge_manager: KnowledgeManager,
    chat_manager: ChatManager,
    prompts_factory: PromptsFactory,
    client_config: ChatClientConfig,
    user_identifier_state: gr.State,
    prompt_categories=None,
):
    tab_id = "brainstorming"
    prompt_list = prompts_factory.create_brainstorming_prompt_list(
        knowledge_manager.knowledge_base_markdown
    )
    interaction_pattern_name = prompt_list.interaction_pattern_name

    chat_context = ChatContext(
        tab_id=tab_id,
        interaction_pattern=prompt_categories[0],
        model="",
        temperature=0.2,
        prompt="",
        message="",
    )

    prompt_list.filter(prompt_categories)

    def __render_prompt_with_warnings(
        prompt_list: PromptList,
        active_knowledge_context: str,
        prompt_choice: str,
        user_input: str,
        additional_vars: dict = {},
        show_warning: bool = True,
    ):
        if not prompt_choice:
            return ""

        warnings = []
        rendered_prompt, _ = prompt_list.render_prompt(
            active_knowledge_context,
            prompt_choice,
            user_input,
            additional_vars=additional_vars,
            warnings=warnings,
        )

        if show_warning and len(warnings) > 0:
            warnings = "\n".join(warnings)
            gr.Info(f"{warnings}")

        return rendered_prompt

    def on_change_user_input(ui_prompt_dropdown, ui_user_input, request: gr.Request):
        active_knowledge_context = user_context.get_value(
            request, "active_knowledge_context", app_level=True
        )

        ui_prompt = __render_prompt_with_warnings(
            prompt_list,
            active_knowledge_context,
            ui_prompt_dropdown,
            ui_user_input,
            show_warning=False,
        )
        return ui_prompt

    def on_change_prompt_choice(
        prompt_choice: str, user_input: str, request: gr.Request
    ) -> dict:
        context_selected = user_context.get_value(
            request, "active_knowledge_context", app_level=True
        )

        if prompt_choice:
            user_context.set_value(
                request, "brainstorming_prompt_choice", prompt_choice
            )
            chat_context.prompt = prompt_list.get(prompt_choice).metadata.get(
                "title", "Unnamed use case"
            )
            help, knowledge = prompt_list.render_help_markdown(
                prompt_choice, context_selected
            )

            rendered_prompt = __render_prompt_with_warnings(
                prompt_list, context_selected, prompt_choice, user_input
            )

            knowledge_reference_exists = knowledge is not None and knowledge != ""

            return [
                prompt_choice,
                rendered_prompt,
                help,
                gr.Markdown(knowledge, visible=knowledge_reference_exists),
            ]
        else:
            return [None, "", "", ""]

    with gr.Tab(interaction_pattern_name, id=tab_id) as tab_brainstorming:
        with gr.Row():
            gr.Markdown(
                "This 'question and answer' pattern currently does not work with all models yet. The GPTs should work."
            )

        with gr.Row():
            with gr.Column(scale=3):
                with gr.Group(elem_classes=["prompt-choice", "haiven-group"]):
                    gr.Markdown(
                        "## 1. What do you want to do?",
                        elem_classes="haiven-group-title",
                    )
                    ui_prompt_dropdown = gr.Dropdown(
                        prompt_list.get_title_id_tuples(),
                        label="Choose a task",
                        elem_id="brainstorming_prompt_choice",
                    )
                    ui_help = gr.Markdown(
                        elem_classes="prompt-help", elem_id="brainstorming_help"
                    )
                    ui_help_knowledge = gr.Markdown(
                        elem_classes=["prompt-help", "knowledge"],
                        elem_id="brainstorming_help_knowledge",
                        visible=False,
                    )
                    ui_user_input = gr.Textbox(label="User input", lines=5)

                with gr.Group(elem_classes="haiven-group"):
                    gr.Markdown(
                        "## 2. Start the chat", elem_classes="haiven-group-title"
                    )
                    ui_start_btn = gr.Button("Start >>", variant="primary")
                    with gr.Accordion(label="View or change the prompt", open=False):
                        ui_prompt = gr.Textbox(
                            label="Prompt",
                            lines=10,
                            info="Will be composed from your inputs above",
                        )

            with gr.Column(scale=5):
                with gr.Group(elem_classes="haiven-group"):
                    gr.Markdown("## 3. Chat", elem_classes="haiven-group-title")
                    ui_chatbot = gr.Chatbot(
                        label="Assistant",
                        height=600,
                        show_copy_button=True,
                        show_label=False,
                        likeable=True,
                    )
                    ui_message = gr.Textbox(label="Message (hit Enter to send)")

        ui_prompt_dropdown.change(
            fn=on_change_prompt_choice,
            inputs=[ui_prompt_dropdown, ui_user_input],
            outputs=[ui_prompt_dropdown, ui_prompt, ui_help, ui_help_knowledge],
        )
        ui_user_input.change(
            fn=on_change_user_input,
            inputs=[ui_prompt_dropdown, ui_user_input],
            outputs=ui_prompt,
        )

        def start(
            prompt_choice: str,
            prompt_text: str,
            user_identifier_state: str,
            request: gr.Request,
        ):
            if prompt_choice:
                system_message = prompt_list.get(prompt_choice).metadata["system"]

                llm_model_from_session = user_context.get_value(
                    request, "llm_model", app_level=True
                )
                temperature_from_session = user_context.get_value(
                    request, "llm_tone", app_level=True
                )
                if llm_model_from_session:
                    client_config.change_model(llm_model_from_session)
                if temperature_from_session:
                    client_config.change_temperature(temperature_from_session)

                chat_session_key_value, chat_session = chat_manager.q_a_chat(
                    client_config=client_config,
                    session_id=None,
                    options=ChatOptions(
                        category="brainstorming", user_identifier=user_identifier_state
                    ),
                )

                response = chat_session.start_with_prompt(prompt_text)
                chat_history = [[system_message + "\n" + prompt_text, response]]

                return {
                    ui_message: "",
                    ui_chatbot: chat_history,
                    state_chat_session_key: chat_session_key_value,
                }
            else:
                gr.Warning("Please choose a task first")
                return {ui_message: "", ui_chatbot: [], state_chat_session_key: None}

        def chat(message_value: str, chat_history, chat_session_key_value: str):
            chat_session = chat_manager.get_session(chat_session_key_value)

            response = chat_session.next(message_value)
            chat_history.append((message_value, response))

            return {ui_message: "", ui_chatbot: chat_history}

        state_chat_session_key = gr.State()

        ui_start_btn.click(
            start,
            [ui_prompt_dropdown, ui_prompt, user_identifier_state],
            [ui_message, ui_chatbot, state_chat_session_key],
            scroll_to_output=True,
        )
        ui_message.submit(
            chat,
            [ui_message, ui_chatbot, state_chat_session_key],
            [ui_message, ui_chatbot],
            scroll_to_output=True,
        )

        def on_vote(vote: gr.LikeData):
            chat_context.model = client_config.service_name
            chat_context.temperature = client_config.temperature
            chat_context.message = vote.value

            UserFeedback.on_message_voted(
                "liked" if vote.liked else "disliked",
                chat_context.to_dict(),
            )

        ui_chatbot.like(on_vote, None, None)

        def on_tab_selected(request: gr.Request):
            user_context.set_value(request, "selected_tab", tab_id)

        tab_brainstorming.select(on_tab_selected)
