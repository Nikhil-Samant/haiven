# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import gradio as gr
from llms.chats import ChatManager
from knowledge_manager import KnowledgeManager
from llms.image_description_service import ImageDescriptionService
from ui.event_handler import EventHandler
from ui.navigation import NavigationManager
from prompts.prompts_factory import PromptsFactory
from ui.ui import UIBaseComponents
from ui.tab_brainstorming.ui import enable_brainstorming
from ui.tab_diagram_chat.ui import enable_image_chat
from ui.tab_knowledge_chat.ui import enable_knowledge_chat
from ui.tab_plain_chat.ui import enable_plain_chat
from ui.tab_prompt_chat.ui import enable_chat
from ui.user_context import user_context
from datetime import datetime


class UIFactory:
    def __init__(
        self,
        ui_base_components: UIBaseComponents,
        prompts_factory: PromptsFactory,
        navigation_manager: NavigationManager,
        event_handler: EventHandler,
        prompts_parent_dir: str,
        knowledge_manager: KnowledgeManager,
        chat_manager: ChatManager,
        image_service: ImageDescriptionService,
    ):
        self.ui_base_components: UIBaseComponents = ui_base_components
        self.prompts_factory: PromptsFactory = prompts_factory
        self.navigation_manager: NavigationManager = navigation_manager
        self.event_handler: EventHandler = event_handler
        self.prompts_parent_dir: str = prompts_parent_dir
        self.knowledge_manager: KnowledgeManager = knowledge_manager
        self.chat_manager: ChatManager = chat_manager
        self.image_service: ImageDescriptionService = image_service

        self.__client_config = None
        self.__copyright_text = f"© {str(datetime.now().year)} Thoughtworks, Inc."

    def _model_changed(self, model_select, request: gr.Request):
        self.__client_config.change_model(model_select)
        user_context.set_value(request, "llm_model", model_select, app_level=True)

    def _tone_changed(self, tone_select, request: gr.Request):
        self.__client_config.change_temperature(tone_select)
        user_context.set_value(request, "llm_tone", tone_select, app_level=True)

    def is_empty(self, value) -> bool:
        return value is None or value == "" or len(value) == 0

    def __knowledge_context_select_changed(
        self, knowledge_context_select, request: gr.Request
    ):
        knowledge_context = self.knowledge_manager.on_context_selected(
            knowledge_context_select
        )
        user_context.set_value(
            request,
            "active_knowledge_context",
            knowledge_context,
            app_level=True,
        )

    def create_ui(self, ui_type):
        match ui_type:
            case "coding":
                return self.create_ui_coding()
            case "testing":
                return self.create_ui_testing()
            case "analysts":
                return self.create_ui_analysts()
            case "knowledge":
                return self.create_ui_knowledge()
            case "about":
                return self.create_ui_about()
            case "plain_chat":
                return self.create_plain_chat()

    def create_ui_coding(self):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="Haiven")
        with blocks:
            navigation, category_metadata = (
                self.navigation_manager.get_coding_navigation()
            )
            self.ui_base_components.ui_header(navigation=navigation)
            user_identifier_state = gr.State()
            with gr.Group(elem_classes="haiven-content"):
                with gr.Group(elem_classes=["haiven-group", "haiven-settings"]):
                    with gr.Accordion("Settings"):
                        with gr.Row():
                            knowledge_context_select = self.ui_base_components.create_knowledge_context_selector_ui(
                                self.knowledge_manager.knowledge_pack_definition
                            )
                            knowledge_context_select.change(
                                fn=self.__knowledge_context_select_changed,
                                inputs=knowledge_context_select,
                            )

                            model_select, tone_select, self.__client_config = (
                                self.ui_base_components.create_llm_settings_ui()
                            )
                            model_select.change(
                                fn=self._model_changed, inputs=model_select
                            )
                            tone_select.change(
                                fn=self._tone_changed, inputs=tone_select
                            )

                with gr.Row(elem_classes="haiven-tabs-container"):
                    with gr.Tabs() as all_tabs:
                        category_filter = ["coding", "architecture"]
                        self.ui_base_components.create_about_tab_for_task_area(
                            category_filter,
                            category_metadata,
                            self.prompts_factory.create_all_prompts_for_user_choice(
                                self.knowledge_manager.knowledge_base_markdown
                            ),
                        )
                        enable_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )
                        enable_brainstorming(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                        )
                        enable_image_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            self.image_service,
                            knowledge_context_select,
                        )
                        enable_knowledge_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )

                with gr.Row():
                    gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

                blocks.load(
                    self.event_handler.on_load_ui,
                    [
                        model_select,
                        tone_select,
                        knowledge_context_select,
                    ],
                    [
                        all_tabs,
                        model_select,
                        tone_select,
                        knowledge_context_select,
                        user_identifier_state,
                    ],
                )
                ##add a label

                blocks.queue()

        return blocks

    def create_ui_testing(self):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="Haiven")
        with blocks:
            navigation, category_metadata = (
                self.navigation_manager.get_testing_navigation()
            )
            self.ui_base_components.ui_header(navigation=navigation)
            with gr.Group(elem_classes="haiven-content"):
                with gr.Group(elem_classes=["haiven-group", "haiven-settings"]):
                    with gr.Accordion("Settings"):
                        with gr.Row():
                            knowledge_context_select = self.ui_base_components.create_knowledge_context_selector_ui(
                                self.knowledge_manager.knowledge_pack_definition
                            )
                            knowledge_context_select.change(
                                fn=self.__knowledge_context_select_changed,
                                inputs=knowledge_context_select,
                            )

                            model_select, tone_select, self.__client_config = (
                                self.ui_base_components.create_llm_settings_ui()
                            )
                            model_select.change(
                                fn=self._model_changed, inputs=model_select
                            )
                            tone_select.change(
                                fn=self._tone_changed, inputs=tone_select
                            )
                with gr.Row(elem_classes="haiven-tabs-container"):
                    category_filter = ["testing"]

                    with gr.Tabs() as all_tabs:
                        user_identifier_state = gr.State()
                        self.ui_base_components.create_about_tab_for_task_area(
                            category_filter,
                            category_metadata,
                            self.prompts_factory.create_all_prompts_for_user_choice(
                                self.knowledge_manager.knowledge_base_markdown,
                            ),
                        )
                        enable_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )
                        enable_brainstorming(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                        )
                        enable_image_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            self.image_service,
                            knowledge_context_select,
                        )
                        enable_knowledge_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )

                with gr.Row():
                    gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

                blocks.load(
                    self.event_handler.on_load_ui,
                    [model_select, tone_select, knowledge_context_select],
                    [
                        all_tabs,
                        model_select,
                        tone_select,
                        knowledge_context_select,
                        user_identifier_state,
                    ],
                )
                blocks.queue()

        return blocks

    def create_ui_analysts(
        self,
    ):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="Haiven")
        with blocks:
            navigation, category_metadata = (
                self.navigation_manager.get_analysis_navigation()
            )
            self.ui_base_components.ui_header(navigation=navigation)
            with gr.Group(elem_classes="haiven-content"):
                with gr.Group(elem_classes=["haiven-group", "haiven-settings"]):
                    with gr.Accordion("Settings"):
                        with gr.Row():
                            knowledge_context_select = self.ui_base_components.create_knowledge_context_selector_ui(
                                self.knowledge_manager.knowledge_pack_definition
                            )
                            knowledge_context_select.change(
                                fn=self.__knowledge_context_select_changed,
                                inputs=knowledge_context_select,
                            )

                            model_select, tone_select, self.__client_config = (
                                self.ui_base_components.create_llm_settings_ui()
                            )
                            model_select.change(
                                fn=self._model_changed, inputs=model_select
                            )
                            tone_select.change(
                                fn=self._tone_changed, inputs=tone_select
                            )
                with gr.Row(elem_classes="haiven-tabs-container"):
                    category_filter = ["analysis"]
                    with gr.Tabs() as all_tabs:
                        user_identifier_state = gr.State()
                        self.ui_base_components.create_about_tab_for_task_area(
                            category_filter,
                            category_metadata,
                            self.prompts_factory.create_all_prompts_for_user_choice(
                                self.knowledge_manager.knowledge_base_markdown
                            ),
                        )
                        enable_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )
                        enable_brainstorming(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                        )
                        enable_image_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.prompts_factory,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            self.image_service,
                            knowledge_context_select,
                        )
                        enable_knowledge_chat(
                            self.knowledge_manager,
                            self.chat_manager,
                            self.__client_config,
                            user_identifier_state,
                            category_filter,
                            knowledge_context_select,
                        )

                with gr.Row():
                    gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

                blocks.load(
                    self.event_handler.on_load_ui,
                    [model_select, tone_select, knowledge_context_select],
                    [
                        all_tabs,
                        model_select,
                        tone_select,
                        knowledge_context_select,
                        user_identifier_state,
                    ],
                )
                blocks.queue()

        return blocks

    def create_ui_knowledge(self):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="Haiven")
        with blocks:
            navigation, category_metadata = (
                self.navigation_manager.get_knowledge_navigation()
            )
            self.ui_base_components.ui_header(navigation=navigation)

            with gr.Group(elem_classes="haiven-content"):
                with gr.Group(elem_classes=["haiven-group", "haiven-settings"]):
                    with gr.Accordion("Settings"):
                        with gr.Row():
                            knowledge_context_select = self.ui_base_components.create_knowledge_context_selector_ui(
                                self.knowledge_manager.knowledge_pack_definition
                            )
                            knowledge_context_select.change(
                                fn=self.__knowledge_context_select_changed,
                                inputs=knowledge_context_select,
                            )

                            model_select, tone_select, self.__client_config = (
                                self.ui_base_components.create_llm_settings_ui()
                            )
                            model_select.change(
                                fn=self._model_changed, inputs=model_select
                            )
                            tone_select.change(
                                fn=self._tone_changed, inputs=tone_select
                            )

                with gr.Row(elem_classes="haiven-tabs-container"):
                    with gr.Tabs() as all_tabs:
                        user_identifier_state = gr.State()
                        with gr.Tab("Knowledge"):
                            self.ui_base_components.ui_show_knowledge(
                                self.knowledge_manager
                            )

                with gr.Row():
                    gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

                blocks.load(
                    self.event_handler.on_load_ui,
                    [model_select, tone_select, knowledge_context_select],
                    [
                        all_tabs,
                        model_select,
                        tone_select,
                        knowledge_context_select,
                        user_identifier_state,
                    ],
                )
                blocks.queue()

        return blocks

    def create_ui_about(self):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="About Haiven")
        with blocks:
            navigation, category_metadata = (
                self.navigation_manager.get_about_navigation()
            )
            self.ui_base_components.ui_header(navigation=navigation)

            with gr.Tab("About"):
                self.ui_base_components.ui_show_about()
            with gr.Tab("Data processing"):
                self.ui_base_components.ui_show_data_processing()

            with gr.Row():
                gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

        return blocks

    def create_plain_chat(self):
        theme, css = self.ui_base_components.styling()
        blocks = gr.Blocks(theme=theme, css=css, title="Haiven")

        with blocks:
            self.ui_base_components.ui_header()
            user_identifier_state = gr.State()

            with gr.Row():
                with gr.Tabs():
                    enable_plain_chat(
                        self.chat_manager,
                        user_identifier_state,
                        self.ui_base_components,
                    )

            with gr.Row():
                gr.HTML(self.__copyright_text, elem_classes=["copyright_text"])

            blocks.load(
                self.event_handler.on_load_plain_chat_ui,
                None,
                outputs=[user_identifier_state],
            )

        blocks.queue()
        return blocks
