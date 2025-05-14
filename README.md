# CursorAISim: Gemini-Powered AI Code Assistant

CursorAISim is a web application built with Streamlit that leverages the power of Google's Gemini API to provide an AI-assisted coding experience. It aims to simulate some functionalities found in tools like GitHub Copilot or Cursor, offering features like code generation, explanation, correction through a chat interface, and management of multiple code snippets.

## Core Features

*   **AI-Powered Code Generation:** Generate code snippets in various languages based on natural language prompts using the Gemini API.
*   **Code Explanation:** Get clear, concise explanations of provided code snippets.
*   **Interactive Chat for Code Refinement:** Use a chatbot interface to discuss code, ask for corrections, or get further clarifications. The AI attempts to provide corrected code based on the conversation.
*   **Manage Multiple Code Snippets:**
    *   Display multiple generated or corrected code snippets.
    *   Select specific snippets for download.
    *   Download selected snippets as a single `.zip` file.
*   **Structured Output:** Pydantic models are used to define and validate the structure of data, including code snippets and chat messages.
*   **Efficient Resource Management:**
    *   `st.session_state` for managing application state and chat history.
    *   `@st.cache_resource` for efficiently caching the Gemini API client.

## Technologies Used

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **AI Model:** [Google Gemini API](https://ai.google.dev/docs/gemini_api_overview) (specifically `gemini-2.0-flash` in the example, adaptable to other Gemini models)
*   **Data Validation & Structuring:** [Pydantic](https://docs.pydantic.dev/)
*   **Language:** Python 3.x

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8 or newer.
    *   `pip` for installing Python packages.

2.  **Clone the Repository (Optional):**
    If you have this project in a Git repository:
    ```bash
    git clone https://github.com/djmahe4/CursorAISim.git
    cd CursorAISim
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Google Gemini API Key:**
    *   Obtain an API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   The application will prompt you to enter this API key in the sidebar when you first run it.

## How to Run

**[Online Implementation](https://cursoraisimulator.streamlit.app/)**

**OR**

1.  Ensure you have completed the setup steps above.
2.  Navigate to the directory containing the application script .
3.  Run the Streamlit application from your terminal:
    ```bash
    streamlit code.py 
    ```
4.  The application will open in your default web browser.
5.  Enter your Google Gemini API Key in the sidebar to activate the AI features.

**Note: There is a provision to switch to ```Gemini 2.5 Flash Preview 04-17``` Just modify line 34 in code.py ```model = genai.GenerativeModel('gemini-2.0-flash')``` to ```model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')```**

## Application Structure & Functionality

The application is structured to provide a user-friendly interface for interacting with the Gemini API for coding tasks.

*   **`code.py` (Main Application File):**
    *   **Pydantic Models (`CodeSnippet`, `ChatMessage`, `AppState`):** Define the data structures for managing code, chat interactions, and the overall application state.
    *   **API Key and Client Initialization (`initialize_gemini_client`, `get_gemini_client`):** Handles secure input of the API key and initialization of the Gemini model client. The client is cached using `st.cache_resource`.
    *   **Gemini Interaction (`send_gemini_message`):** A core function to send prompts to the Gemini API and retrieve responses for generation, explanation, or chat.
    *   **Streamlit UI:**
        *   **Sidebar:** Contains the API key input and global action controls.
        *   **Main Layout (Two Columns):**
            *   **Left Column (Code Generation & Management):**
                *   Radio buttons to select actions: "Generate Code", "Explain Code", "Correct Code (via Chat)".
                *   Forms for submitting code generation prompts or code for explanation.
                *   Display area for generated/managed code snippets using `st.expander` and `st.code`.
                *   Checkboxes for selecting code snippets to download.
                *   Download button for a `.zip` file of selected snippets.
            *   **Right Column (Chat & Code Refinement):**
                *   Chat interface built with `st.chat_message` and `st.chat_input`.
                *   Displays conversation history.
                *   Allows users to ask questions, request code corrections, or discuss code snippets.
                *   Attempts to extract and add corrected code from chat responses back to the managed snippets list.
    *   **State Management (`st.session_state.app_state`):** All dynamic application data (chat history, generated codes, UI states) is stored here using the `AppState` Pydantic model.

## Key Features in Action

1.  **Generating Code:**
    *   Select "Generate Code".
    *   Enter a natural language prompt (e.g., "Python function to calculate factorial").
    *   Specify a filename and language.
    *   The generated code appears in the "Generated/Managed Code Snippets" section.

2.  **Explaining Code:**
    *   Select "Explain Code".
    *   Paste the code you want to understand into the text area.
    *   The explanation will appear below the form.

3.  **Correcting Code via Chat:**
    *   Select "Correct Code (via Chat)".
    *   If you have code snippets, you can refer to them implicitly (the app tries to use the latest or selected snippet as context) or paste code directly into the chat.
    *   Type your correction request (e.g., "This code gives an error, can you fix it?" or "How can I optimize this loop?").
    *   The AI's response, including any suggested code, will appear in the chat. Corrected code blocks from the AI may be automatically added to your managed snippets.

4.  **Downloading Code:**
    *   Check the "Select for download" box next to any code snippets you wish to save.
    *   Click the "Download Selected Code Snippets (.zip)" button.

## Future Enhancements (Potential Ideas)

- [ ]   **Streaming Responses:** Implement streaming for chat for a more interactive feel.
- [ ]   **Direct Code Editing:** Allow users to edit the displayed code snippets directly in the UI.
- [ ]   **Improved Context Management:** More sophisticated ways for the user to specify which code snippet the chat refers to.
- [ ]   **History Persistence:** Option to save/load chat history or generated code snippets across sessions (e.g., using local files or a simple database).
- [ ]   **Enhanced Error Handling:** More granular error messages and recovery options.
- [ ]   **Support for Code Execution (with extreme caution and sandboxing):** If ever considered, this would require significant security measures.

## Contributing

Contributions are always welcome! Please fork the repository and submit a pull request with your enhancements.
