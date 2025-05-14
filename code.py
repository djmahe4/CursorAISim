import streamlit as st
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict
import io
import zipfile
import datetime

# --- Pydantic Models ---
class CodeSnippet(BaseModel):
    id: str = Field(default_factory=lambda: f"code_{datetime.datetime.now().timestamp()}")
    filename: str = "script.py"
    language: str = "python"
    content: str
    description: Optional[str] = None # Brief explanation of this snippet

class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    parts: List[str] # Gemini API uses 'parts' which is a list of texts

class AppState(BaseModel):
    api_key_configured: bool = False
    chat_history: List[ChatMessage] = []
    generated_codes: List[CodeSnippet] = []
    current_explanation: Optional[str] = None
    selected_code_ids_for_download: Dict[str, bool] = {}

# --- API Key and Client Initialization ---
@st.cache_resource # Cache the resource (Gemini model client)
def initialize_gemini_client(api_key: str):
    """Initializes the Gemini generative model with the provided API key."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro') # Or other appropriate model
        return model
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        return None

def get_gemini_client():
    """Gets the Gemini client, prompting for API key if not configured."""
    if "api_key" not in st.session_state or not st.session_state.api_key:
        api_key_input = st.sidebar.text_input("Enter your Google Gemini API Key:", type="password", key="api_key_input_widget")
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.session_state.app_state.api_key_configured = True
            st.rerun() # Rerun to reflect key input and initialize client
        else:
            st.sidebar.warning("Please enter your Gemini API Key to proceed.")
            return None
    
    if "gemini_model_client" not in st.session_state or st.session_state.gemini_model_client is None:
         if "api_key" in st.session_state and st.session_state.api_key:
            model = initialize_gemini_client(st.session_state.api_key)
            if model:
                st.session_state.gemini_model_client = model
                st.session_state.app_state.api_key_configured = True
            else:
                st.session_state.app_state.api_key_configured = False # Failed to init
                if "api_key" in st.session_state: # Clear invalid key to allow re-entry
                    del st.session_state.api_key 
                return None
         else:
             return None


    return st.session_state.gemini_model_client

# --- Gemini Interaction Functions ---
def send_gemini_message(prompt: str, model_client, chat_history: Optional[List[Dict[str, str]]] = None):
    """Sends a message to Gemini and returns the text response."""
    if not model_client:
        st.error("Gemini client not initialized. Please check your API key.")
        return None
    try:
        if chat_history:
            # For ongoing chat
            chat = model_client.start_chat(history=[{"role": msg.role, "parts": msg.parts} for msg in chat_history])
            response = chat.send_message(prompt)
        else:
            # For single turn
            response = model_client.generate_content(prompt)
        
        # Ensure response.text or parts exist
        if hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'parts') and response.parts:
            return "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else:
            # Log the full response if the expected text attributes are missing
            st.warning(f"Unexpected Gemini response structure: {response}")
            # Try to find text in candidates if available (common for some error/block responses)
            if hasattr(response, 'candidates') and response.candidates:
                candidate_texts = [("".join(part.text for part in c.content.parts if hasattr(part, 'text'))) for c in response.candidates if hasattr(c, 'content') and hasattr(c.content, 'parts')]
                if any(candidate_texts):
                    return "\n".join(ct for ct in candidate_texts if ct) # Join non-empty candidate texts
            return "Sorry, I couldn't process that. The response format was unexpected."

    except Exception as e:
        st.error(f"Error communicating with Gemini: {e}")
        return None

# --- Helper Functions ---
def create_zip_file(code_snippets: List[CodeSnippet]) -> io.BytesIO:
    """Creates a zip file in memory from a list of code snippets."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for snippet in code_snippets:
            zip_file.writestr(snippet.filename, snippet.content)
    zip_buffer.seek(0)
    return zip_buffer

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Gemini AI Code Assistant")

# Initialize session state for AppState if not already present
if "app_state" not in st.session_state:
    st.session_state.app_state = AppState()

# Sidebar for API Key and global actions
st.sidebar.title("Configuration & Actions")
gemini_model = get_gemini_client() # Handles API key input and client init

# Main application layout
col1, col2 = st.columns([2, 1]) # Main content and Chat/Explanation area

with col1:
    st.header("Code Generation & Management")

    if gemini_model:
        action_mode = st.radio(
            "Select Action:",
            ["Generate Code", "Explain Code", "Correct Code (via Chat)"],
            key="action_mode_radio",
            horizontal=True
        )

        if action_mode == "Generate Code":
            with st.form("code_gen_form"):
                prompt_gen = st.text_area("Enter your code generation prompt (e.g., 'Python function for quicksort'):", height=100)
                filename_gen = st.text_input("Desired filename (e.g., quicksort.py):", "generated_script.py")
                language_gen = st.text_input("Language:", "python")
                submit_gen = st.form_submit_button("Generate Code")

            if submit_gen and prompt_gen:
                with st.spinner("Generating code..."):
                    full_prompt = f"Generate a code snippet for the following task. Provide only the code, no explanations before or after the code block. Language: {language_gen}\nTask: {prompt_gen}"
                    generated_content = send_gemini_message(full_prompt, gemini_model)
                    if generated_content:
                        # Basic extraction of code from markdown if present
                        if "```" in generated_content:
                            code_block_content = generated_content.split("```")[1]
                            # Remove language hint if present on the first line of the block
                            if '\n' in code_block_content:
                                first_line, _, rest_of_code = code_block_content.partition('\n')
                                if first_line.strip().isalpha() and not first_line.strip().startswith(('#', '//', '/*')): # simple check for language hint
                                    code_to_store = rest_of_code
                                else:
                                    code_to_store = code_block_content
                            else: # single line code block
                                code_to_store = code_block_content
                            code_to_store = code_to_store.strip()
                        else:
                            code_to_store = generated_content.strip()

                        snippet = CodeSnippet(
                            filename=filename_gen,
                            language=language_gen,
                            content=code_to_store,
                            description=f"Generated from prompt: {prompt_gen[:50]}..."
                        )
                        st.session_state.app_state.generated_codes.append(snippet)
                        st.success("Code generated!")
                        st.session_state.app_state.selected_code_ids_for_download[snippet.id] = True # Auto-select new
                    else:
                        st.error("Failed to generate code.")

        elif action_mode == "Explain Code":
            with st.form("code_explain_form"):
                code_to_explain = st.text_area("Paste the code you want to explain:", height=150)
                submit_explain = st.form_submit_button("Explain Code")
            
            if submit_explain and code_to_explain:
                with st.spinner("Generating explanation..."):
                    prompt_explain = f"Explain the following code snippet. Be concise and clear:\n\n```\n{code_to_explain}\n```"
                    explanation = send_gemini_message(prompt_explain, gemini_model)
                    if explanation:
                        st.session_state.app_state.current_explanation = explanation
                        st.success("Explanation generated!")
                    else:
                        st.error("Failed to get explanation.")
        
        # Display Explanation (if any, used by "Explain Code" and potentially chat)
        if st.session_state.app_state.current_explanation:
            st.subheader("Code Explanation")
            st.markdown(st.session_state.app_state.current_explanation)
            st.session_state.app_state.current_explanation = None # Clear after showing


        st.subheader("Generated/Managed Code Snippets")
        if not st.session_state.app_state.generated_codes:
            st.info("No code snippets generated or managed yet.")
        else:
            temp_selections = {} # To handle checkbox state within this rerun
            for i, snippet in enumerate(st.session_state.app_state.generated_codes):
                with st.expander(f"{snippet.filename} ({snippet.language}) - {snippet.description or ''}", expanded=True):
                    st.code(snippet.content, language=snippet.language.lower())
                    
                    # Use snippet.id for checkbox key to ensure uniqueness
                    is_selected = st.checkbox(
                        "Select for download", 
                        value=st.session_state.app_state.selected_code_ids_for_download.get(snippet.id, False), 
                        key=f"cb_{snippet.id}"
                    )
                    temp_selections[snippet.id] = is_selected
            
            # Update session state after iterating through all checkboxes
            st.session_state.app_state.selected_code_ids_for_download.update(temp_selections)


            selected_to_download = [
                s for s in st.session_state.app_state.generated_codes 
                if st.session_state.app_state.selected_code_ids_for_download.get(s.id, False)
            ]

            if selected_to_download:
                zip_bytes = create_zip_file(selected_to_download)
                st.download_button(
                    label="Download Selected Code Snippets (.zip)",
                    data=zip_bytes,
                    file_name="code_snippets.zip",
                    mime="application/zip"
                )
            else:
                st.info("Select one or more code snippets to download.")
                
    else:
        st.info("Please configure your Gemini API key in the sidebar to enable code features.")


with col2:
    st.header("Chat & Code Refinement")

    if not gemini_model:
        st.warning("Chat features require a configured Gemini API Key.")
    else:
        # Display chat messages from history
        for message_data in st.session_state.app_state.chat_history:
            with st.chat_message(message_data.role):
                st.markdown("\n".join(message_data.parts)) # Display all parts

        # Chat input
        user_prompt = st.chat_input("Ask about code, request corrections, or general chat...")

        if user_prompt:
            # Add user message to chat history
            st.session_state.app_state.chat_history.append(ChatMessage(role="user", parts=[user_prompt]))
            
            with st.chat_message("user"):
                st.markdown(user_prompt)

            # Prepare context for Gemini (current code being discussed, if any)
            contextual_prompt = user_prompt
            if st.session_state.app_state.generated_codes and action_mode == "Correct Code (via Chat)":
                # If there's code and the mode is correct, find the latest selected or simply latest code.
                # For simplicity, let's assume user refers to the latest generated code or selected one.
                # A more robust solution would involve explicit selection or parsing user intent better.
                latest_code_to_discuss = None
                selected_for_chat_correction = [s for s_id, is_sel in st.session_state.app_state.selected_code_ids_for_download.items() if is_sel]
                if selected_for_chat_correction:
                    latest_code_to_discuss = next((s for s in st.session_state.app_state.generated_codes if s.id == selected_for_chat_correction[-1]), None)
                elif st.session_state.app_state.generated_codes:
                     latest_code_to_discuss = st.session_state.app_state.generated_codes[-1]
                
                if latest_code_to_discuss:
                    contextual_prompt = (
                        f"Regarding the following {latest_code_to_discuss.language} code snippet (filename: {latest_code_to_discuss.filename}):\n"
                        f"```\n{latest_code_to_discuss.content}\n```\n\n"
                        f"User request: {user_prompt}\n\n"
                        "Please provide a corrected version if needed, and an explanation of the changes or your thoughts."
                        " If providing corrected code, ensure it's in a markdown code block."
                    )
                else:
                    contextual_prompt = f"User request: {user_prompt}. (No specific code snippet context provided by the app)."


            # Get AI response
            with st.spinner("Thinking..."):
                # Pass chat history for context
                gemini_history_for_api = [{"role": msg.role, "parts": [{"text": part} for part in msg.parts]} for msg in st.session_state.app_state.chat_history]

                ai_response_text = send_gemini_message(contextual_prompt, gemini_model, chat_history=None) # Simplified: send last user prompt with context

                if ai_response_text:
                    st.session_state.app_state.chat_history.append(ChatMessage(role="model", parts=[ai_response_text]))
                    with st.chat_message("model"):
                        st.markdown(ai_response_text)

                    # Try to extract and add corrected code if relevant (basic check)
                    if "```" in ai_response_text and action_mode == "Correct Code (via Chat)":
                        try:
                            # More careful extraction for corrected code
                            potential_code_blocks = ai_response_text.split("```")
                            extracted_code_content = None
                            extracted_language = "python" # default

                            for i in range(1, len(potential_code_blocks), 2): # Iterate over content between ```
                                block_content_with_lang = potential_code_blocks[i]
                                if '\n' in block_content_with_lang:
                                    lang_hint, _, code_block = block_content_with_lang.partition('\n')
                                    lang_hint = lang_hint.strip().lower()
                                    # Rudimentary check if lang_hint is actually a language
                                    if lang_hint and not any(char in lang_hint for char in [' ', ':', ';', '{', '(', '#']):
                                        extracted_language = lang_hint
                                        extracted_code_content = code_block.strip()
                                    else: # Assume no language hint or it's part of the code
                                        extracted_code_content = block_content_with_lang.strip()
                                else: # Single line code block
                                    extracted_code_content = block_content_with_lang.strip()
                                
                                if extracted_code_content: # Use the first valid code block found
                                    break
                            
                            if extracted_code_content:
                                corrected_snippet = CodeSnippet(
                                    filename=f"corrected_{datetime.datetime.now().strftime('%H%M%S')}.{extracted_language.split() if extracted_language else 'txt'}", # take first word if multiple e.g. "python console"
                                    language=extracted_language or "unknown",
                                    content=extracted_code_content,
                                    description="Corrected/refined via chat"
                                )
                                st.session_state.app_state.generated_codes.append(corrected_snippet)
                                st.session_state.app_state.selected_code_ids_for_download[corrected_snippet.id] = True
                                st.toast(f"Corrected code snippet '{corrected_snippet.filename}' added to list.", icon="✨")
                                # No rerun needed here as the display logic will pick it up next draw.
                        except Exception as e:
                            st.warning(f"Could not automatically parse corrected code from chat: {e}")
                else:
                    st.session_state.app_state.chat_history.append(ChatMessage(role="model", parts=["Sorry, I encountered an issue."]))
                    with st.chat_message("model"):
                        st.markdown("Sorry, I encountered an issue trying to respond.")
            # No explicit rerun; Streamlit handles re-rendering on input/state changes.
            # If chat history becomes too long, you might need to add pagination or summarization.

# --- Final check for API key status ---
if not st.session_state.app_state.api_key_configured and "api_key" not in st.session_state:
    st.sidebar.error("Gemini API Key is not configured. Please enter it above.")
elif st.session_state.app_state.api_key_configured and not gemini_model:
     st.sidebar.error("Gemini client initialization failed. Check your API key or console for errors.")
