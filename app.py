import streamlit as st
from transformers import pipeline
from huggingface_hub import login
import os

# Disable Streamlit's file watcher 
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

# 🔹 Manually set your Hugging Face token here
huggingface_token = " enter your token "

# 🔹 Authenticate with Hugging Face using the token
try:
    login(huggingface_token)
except Exception as e:
    st.error(f"⚠️ Authentication failed: {e}")
    st.stop()

# 🔹 Load DistilGPT-2 Model 
@st.cache_resource
def load_model():
    return pipeline(
        "text-generation", 
        model="distilgpt2", 
        max_length=150, 
        do_sample=True, 
        temperature=0.7,
        top_k=50,
        truncation=True  # Explicitly enable truncation
    )

model = load_model()

# 🔹 Initialize Session State
if 'conversation_state' not in st.session_state:
    st.session_state.conversation_state = {"step": "greeting", "details": {}}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if "input_key" not in st.session_state:
    st.session_state["input_key"] = 0  # Unique key for input field

# 🔹 Generate Technical Questions Using DistilGPT-2 with a Prompt
def generate_technical_questions(tech_stack):
    prompt = f"""
You are a technical interviewer. Generate exactly 3 clear and well-structured technical interview questions that are relevant to a candidate skilled in {', '.join(tech_stack)}.
Each question must be on its own line and begin with its number followed by a period and a space (e.g., "1. ").
Do not include any additional text or explanation. Only return the 3 questions.
"""
    response = model(prompt, truncation=True)
    generated_text = response[0]["generated_text"].strip()

    # Post-process: extract lines that start with a digit followed by ". "
    lines = [line.strip() for line in generated_text.split("\n") 
             if line and line[0].isdigit() and line[1:3] == ". "]
    if len(lines) >= 3:
        questions = "\n".join(lines[:3])
    else:
        questions = generated_text  # Fallback if not enough lines found
    
    return f"Here are some technical questions based on your skills:\n\n{questions}"

# 🔹 Process User Messages and Conversation Flow
def process_message(user_message):
    state = st.session_state.conversation_state
    user_message = user_message.strip()

    # Handle exit keywords
    if user_message.lower() in ["exit", "quit", "bye"]:
        st.session_state.chat_history.append(
            ("bot", "Thank you for your time! We'll be in touch with the next steps.")
        )
        st.session_state.conversation_state = {"step": "greeting", "details": {}}
        return

    # Conversation flow
    if state["step"] == "greeting":
        state["step"] = "collect_info"
        st.session_state.chat_history.append(
            ("bot", "👋 Hello! I'm TalentScout, your hiring assistant. Let's start with your details. What's your full name?")
        )
    elif state["step"] == "collect_info":
        details = state["details"]
        if "name" not in details:
            details["name"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Nice to meet you, {details['name']}! What's your email address?")
            )
        elif "email" not in details:
            details["email"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Got it, {details['name']}. What's your phone number?")
            )
        elif "phone" not in details:
            details["phone"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Thanks, {details['name']}! How many years of experience do you have?")
            )
        elif "experience" not in details:
            details["experience"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Noted! What position are you applying for, {details['name']}?")
            )
        elif "position" not in details:
            details["position"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Great choice, {details['name']}! Where are you currently located?")
            )
        elif "location" not in details:
            details["location"] = user_message
            st.session_state.chat_history.append(
                ("bot", f"Awesome! Finally, please list your tech stack (e.g., Python, Django, React).")
            )
        elif "tech_stack" not in details:
            details["tech_stack"] = [tech.strip() for tech in user_message.split(",")]
            state["step"] = "generate_questions"
            response_text = generate_technical_questions(details["tech_stack"])
            st.session_state.chat_history.append(("bot", response_text))
    else:
        st.session_state.chat_history.append(
            ("bot", "I'm sorry, I didn't understand that. Could you rephrase?")
        )

# --- Streamlit Chat UI ---
st.title("💬 TalentScout AI Chatbot")
st.markdown("### 🚀 Interact with the chatbot below:")

# Ensure chatbot starts conversation if history is empty
if not st.session_state.chat_history:
    st.session_state.chat_history.append(
        ("bot", "👋 Hello! I'm TalentScout, your hiring assistant. Let's get started with your details. What's your full name?")
    )
    st.session_state.conversation_state["step"] = "collect_info"

# Display Chat History
for sender, message in st.session_state.chat_history:
    if sender == "bot":
        st.markdown(f"**🤖 TalentScout AI:** {message}")
    else:
        st.markdown(f"**🧑 You:** {message}")

# Set the button label based on the conversation step.
button_label = "Send" if st.session_state.conversation_state["step"] == "generate_questions" else "Update Answer"

# --- User Input Section ---
with st.form(key="chat_form"):
    user_input = st.text_input("Your Message:", key=f"input_field_{st.session_state['input_key']}")
    submit_button = st.form_submit_button(button_label)

if submit_button and user_input:
    st.session_state.chat_history.append(("user", user_input))
    process_message(user_input)
    # Clear input field by updating its key 
    st.session_state["input_key"] += 1
    st.rerun()  # Refresh UI
