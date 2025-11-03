import json
import streamlit as st
import uuid
import re
import io

def generate_conversation_markdown(conversation, query=""):
    mapping = conversation.get("mapping", {})
    markdown = f"# {conversation.get('title', 'Untitled')}\n\n"
    for msg_id, msg in mapping.items():
        message = msg.get("message")
        if message and isinstance(message, dict):
            author = message.get("author", {})
            role = author.get("role", "").lower()
            content = message.get("content", {})
            parts = content.get("parts", [])
            for segment in parts:
                if isinstance(segment, str) and segment.strip():
                    if query.lower() in segment.lower() or not query:
                        prefix = "**You:**" if role == "user" else "**ChatGPT:**"
                        markdown += f"{prefix}\n\n{segment.strip()}\n\n---\n\n"
    return markdown


def display_message(role_label, contentText, query=""):
    parts = contentText.get("parts")
    if isinstance(parts, list):
        shown_header = False
        for segment in parts:
            if isinstance(segment, str) and segment.strip():
                if query.lower() in segment.lower() or not query:
                    # Highlight keyword
                    if query:
                        import re
                        keyword_regex = re.escape(query)
                        segment = re.sub(fr"(?i)({keyword_regex})", r"<mark>\1</mark>", segment)

                    # Alignment style
                    alignment = "right" if role_label == "You" else "left"
                    margin = "margin: 10px 0;" if role_label == "You" else ""
                    background_color = "background-color: #474747" if role_label == "You" else ""
                    padding = "padding: 10px 15px; border-radius: 10px; max-width: 80%;" if role_label == "You" else ""
                    html = f"""
                    <div style='text-align: {alignment}; {margin}'>
                        <div style='display: inline-block; {background_color}; {padding}'>
                            <strong>{role_label}:</strong><br>{segment}
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)


st.title("ChatGPT Viewer - My Past Conversations")

# JSON file upload
uploaded_file = st.file_uploader("Choose your exported ChatGPT file (JSON)", type="json")

if uploaded_file:
    try:
        data = json.load(uploaded_file)
    except json.JSONDecodeError:
        st.error("Error reading JSON. Please check the file.")
        st.stop()

    # Show JSON structure
    st.subheader("📄 JSON Structure")
    st.write(f"Root object type: {type(data).__name__}")
    
    if isinstance(data, list):
        st.write(f"Number of conversations: {len(data)}")
    
    st.markdown("---")

    conversations = data  # we know it's a list

    # List of IDs or titles for display
    conversation_display = [
        f"{conv.get('title','Untitled')} ({conv.get('create_time','?')})"
        for conv in conversations
    ]
    selected_conversation = st.selectbox("Select a conversation", conversation_display)

    # Identify which conversation was selected
    idx = conversation_display.index(selected_conversation)
    conv = conversations[idx]

    # Keyword search
    query = st.text_input("Search by keyword (optional)")

    st.subheader(f"Conversation messages: {conv.get('title','Untitled')}")
    mapping = conv.get("mapping", {})
    if not mapping:
        st.info("This conversation has no messages.")
    else:
        for msg_id, msg in mapping.items():
            message = msg.get("message")
            content = ""
            if message and isinstance(message, dict):
                author = message.get("author")
                if author and isinstance(author, dict):
                    role = author.get("role")
                    if role and role.lower() == "user":
                        display_message("You", message.get("content"), query)
                    elif role and role.lower() == "assistant":
                        display_message("ChatGPT", message.get("content"), query)
    markdown_content = generate_conversation_markdown(conv, query)
    buffer = io.BytesIO(markdown_content.encode("utf-8"))
    st.download_button(
        label="📥 Export conversation to Markdown",
        data=buffer,
        file_name=f"{conv.get('title','conversation')}.md",
        mime="text/markdown"
    )