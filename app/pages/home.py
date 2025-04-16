# pages/home.py
import gradio as gr
from pymongo import MongoClient
from pages.line_comment import line_comment_page
from pages.report_generator import report_generator_page
from pages.dialogue_comment import dialogue_comment_page
from pages.report_comment import report_comment_page

client = MongoClient("mongodb://ophthalmology_db_container:27017/")
db = client["ophthalmology_db"]
users_collection = db["users"]

def login(username, password):
    # print(f"Attempting login for user_name: {username}, password: {password}")
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        print(f"Login successful for username: {username}")
        return username, "Login successful!", True
    print(f"Login failed: No user found for username: {username}")
    return None, "Invalid username or password.", False

def logout(username):
    print(f"Logging out for username: {username}")
    return None, "Logged out successfully!", False

def home_page():
    with gr.Blocks() as home:
        username_state = gr.State(None)
        logged_in_state = gr.State(False)
        username_hidden = gr.Textbox(value="", visible=False)

        gr.Markdown("# LLM-Driven Generation and Summarization of Ophthalmology Dialogues")

        with gr.Row():
            user_display = gr.Markdown("**Current User:** Not logged in")

        with gr.Tab("Login"):
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
            login_message = gr.Textbox(label="Message", interactive=False)
            login_logout_button = gr.Button("Login")
            gr.Markdown("### Project: Streamline Ophthalmology Clinic Patient QA and Pre-Surgical Inquiry By Agentive LLMs")
            gr.Markdown("- Cataract is a common condition, yet limited consultation time often leaves patients without sufficient education about surgery and IOL options. This platform assists in improving patient understanding and decision-making with the help of AI-powered LLMs, reducing physician workload.")
            gr.Image("./assets/SchematicFlowDiagram.png", label="Cataract Overview", elem_classes="responsive-image img")
            gr.Markdown("### Powered by\n - Director : SJ, Chen | Vice Dean : TF, Chen | Resident : KJ, Chang | PGY : WC, Fang | Fellow : SC, Chi | MSc : KR, Liu | MSc : YJ, Meng | MSc : MK, Chen")

        with gr.Tab("App Tabs", visible=False) as app_tabs:
            with gr.TabItem("Line Comment", id=1):
                line_comment_page(username_state)
            with gr.TabItem("Report Generator", id=2):
                report_generator_page()
            with gr.TabItem("Dialogue Comment", id=3):
                dialogue_comment_page()
            with gr.TabItem("Report Comment", id=4):
                report_components = report_comment_page()
                for event in report_components["events"]:
                    event

        def handle_login_logout(username, logged_in, new_username, password):
            # print(f"handle_login_logout: username={username}, logged_in={logged_in}, new_username={new_username}")
            if logged_in:
                new_username, message, new_logged_in = logout(username)
                username_hidden_value = ""
            else:
                new_username, message, new_logged_in = login(new_username, password)
                username_hidden_value = new_username if new_username else ""
            # print(f"handle_login_logout: new_user_name={new_username}, logged_in={new_logged_in}")
            return (
                new_username,
                message,
                new_logged_in,
                gr.update(value=f"**Current User:** {new_username if new_username else 'Not logged in'}"),
                gr.update(value="Logout" if new_logged_in else "Login"),
                gr.update(visible=new_logged_in),
                username_hidden_value
            )

        login_logout_button.click(
            handle_login_logout,
            inputs=[username_state, logged_in_state, username_input, password_input],
            outputs=[username_state, login_message, logged_in_state, user_display, login_logout_button, app_tabs, username_hidden],
            queue=False
        )

    return home
