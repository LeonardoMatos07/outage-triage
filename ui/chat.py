from typing import Any

import streamlit as st

from app.texts import load_texts
from ui.client import ApiUnavailableError, post_triage
from ui.view import UI_TEXTS, build_details, outcome_label

TEXTS = load_texts(UI_TEXTS)
CHAT_TEXTS = TEXTS["chat"]


def reset_conversation() -> None:
    st.session_state.messages = [
        {"role": "assistant", "content": CHAT_TEXTS["welcome"], "details": None}
    ]
    st.session_state.session_id = None


def render_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["details"]:
            with st.expander(CHAT_TEXTS["details_label"]):
                st.caption(message["outcome"])
                st.json(message["details"])


def handle_prompt(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt, "details": None})
    try:
        response = post_triage(prompt, st.session_state.session_id)
    except ApiUnavailableError:
        st.session_state.messages.append(
            {"role": "assistant", "content": CHAT_TEXTS["api_error"], "details": None}
        )
        return
    st.session_state.session_id = response.session_id
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.reply,
            "details": build_details(response),
            "outcome": outcome_label(response),
        }
    )


def main() -> None:
    st.set_page_config(page_title=CHAT_TEXTS["page_title"])
    st.title(CHAT_TEXTS["title"])
    st.warning(TEXTS["notice"])
    if "messages" not in st.session_state:
        reset_conversation()
    if st.button(CHAT_TEXTS["new_conversation"]):
        reset_conversation()
    prompt = st.chat_input(CHAT_TEXTS["input_placeholder"])
    if prompt:
        handle_prompt(prompt)
    for message in st.session_state.messages:
        render_message(message)


main()
