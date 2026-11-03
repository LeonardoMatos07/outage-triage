from typing import Any

import streamlit as st

from app.settings import is_mock_mode
from app.texts import load_texts
from ui.chat_view import (
    details_html,
    header_html,
    label_html,
    mock_banner_html,
    notice_html,
    reply_html,
)
from ui.client import ApiUnavailableError, post_triage
from ui.theme import inject_theme
from ui.view import UI_TEXTS, build_details, outcome_kind, outcome_label

TEXTS = load_texts(UI_TEXTS)
CHAT_TEXTS = TEXTS["chat"]
PENDING_PROMPT_KEY = "pending_prompt"


def welcome_message() -> dict[str, Any]:
    return {"role": "assistant", "content": CHAT_TEXTS["welcome"], "kind": None}


def reset_conversation() -> None:
    st.session_state.messages = [welcome_message()]
    st.session_state.session_id = None


def queue_example(text: str) -> None:
    st.session_state[PENDING_PROMPT_KEY] = text


def render_message(message: dict[str, Any]) -> None:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
        return
    with st.chat_message("assistant", avatar=CHAT_TEXTS["assistant_avatar"]):
        st.markdown(
            reply_html(
                message["content"],
                message["kind"],
                message.get("label"),
                message.get("protocol"),
            ),
            unsafe_allow_html=True,
        )
        if message.get("details"):
            with st.expander(CHAT_TEXTS["details_label"]):
                st.markdown(details_html(message["details"]), unsafe_allow_html=True)


def render_examples() -> None:
    with st.container(horizontal=True, wrap=True, key="examples"):
        for index, example in enumerate(CHAT_TEXTS["examples"]):
            st.button(example, key=f"example_{index}", on_click=queue_example, args=(example,))


def render_example_area() -> None:
    if len(st.session_state.messages) == 1:
        st.markdown(label_html(CHAT_TEXTS["examples_label"]), unsafe_allow_html=True)
        render_examples()
        return
    with st.expander(CHAT_TEXTS["examples_collapsed_label"]):
        render_examples()


def handle_prompt(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        with st.spinner(CHAT_TEXTS["thinking"]):
            response = post_triage(prompt, st.session_state.session_id)
    except ApiUnavailableError:
        st.session_state.messages.append(
            {"role": "assistant", "content": CHAT_TEXTS["api_error"], "kind": None}
        )
        return
    st.session_state.session_id = response.session_id
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.reply,
            "kind": outcome_kind(response),
            "label": outcome_label(response),
            "protocol": response.protocol,
            "details": build_details(response),
        }
    )


def render_header() -> None:
    left, right = st.columns([5, 1], vertical_alignment="center")
    left.markdown(header_html(), unsafe_allow_html=True)
    right.button(
        CHAT_TEXTS["new_conversation"],
        key="new_conversation",
        on_click=reset_conversation,
        type="tertiary",
        icon=":material/restart_alt:",
    )


def render_notices() -> None:
    st.markdown(notice_html(), unsafe_allow_html=True)
    if is_mock_mode():
        st.markdown(mock_banner_html(), unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title=CHAT_TEXTS["page_title"], page_icon=TEXTS["page_icon"])
    inject_theme(wide=False)
    if "messages" not in st.session_state:
        reset_conversation()
    render_header()
    render_notices()
    prompt = st.chat_input(CHAT_TEXTS["input_placeholder"])
    pending = st.session_state.pop(PENDING_PROMPT_KEY, None)
    if prompt or pending:
        handle_prompt(prompt or pending)
    for message in st.session_state.messages:
        render_message(message)
    render_example_area()


main()
