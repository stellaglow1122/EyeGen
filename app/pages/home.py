# pages/home.py
import gradio as gr
from pymongo import MongoClient
from pages.line_comment import line_comment_page
from pages.report_generator import report_generator_page
from pages.dialogue_comment import dialogue_comment_page
from pages.report_comment import report_comment_page

# 連接到 MongoDB
client = MongoClient("mongodb://ophthalmology_db_container:27017/")
db = client["ophthalmology_db"]
users_collection = db["users"]

# 登入驗證函數
def login(username, password):
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        return username, "Login successful!", True
    return None, "Invalid username or password.", False

# 登出函數
def logout():
    return None, "Logged out successfully!", False

# 主頁面
def home_page():
    with gr.Blocks() as home:
        # 儲存登入狀態
        username_state = gr.State(None)
        logged_in_state = gr.State(False)

        gr.Markdown("# LLM-Driven Generation and Summarization of Ophthalmology Dialogues")

        # 顯示當前使用者名稱和登入/登出選項
        with gr.Row():
            user_display = gr.Markdown("**Current User:** Not logged in")
            
        # 登入頁面
        with gr.Tab("Login"):
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
            login_message = gr.Textbox(label="Message", interactive=False)
            login_logout_button = gr.Button("Login")
            gr.Markdown("### Project: Streamline Ophthalmology Clinic Patient QA and Pre-Surgical Inquiry By Agentive LLMs")
            gr.Markdown("- Cataract is a common condition, yet limited consultation time often leaves patients without sufficient education about surgery and IOL options. This platform assists in improving patient understanding and decision-making with the help of AI-powered LLMs, reducing physician workload.")
            gr.Image("./assets/SchematicFlowDiagram.png", label="Cataract Overview", elem_classes="esponsive-image img")
            gr.Markdown("### Powered by\n - Director : SJ, Chen | Vice Dean : TF, Chen | Resident : KJ, Chang | PGY : WC, Fang | Fellow : SC, Chi | MSc : KR, Liu | MSc : YJ, Meng | MSc : MK, Chen")

        # 其他頁面（初始不可見）
        with gr.Tab("App Tabs", visible=False) as app_tabs:
            with gr.TabItem("Line Comment", id=1):
                line_comment_page()
            with gr.TabItem("Report Generator", id=2):
                report_generator_page()
            with gr.TabItem("Dialogue Comment", id=3):
                dialogue_comment_page()
            with gr.TabItem("Report Comment", id=4):
                report_components = report_comment_page()
                for event in report_components["events"]:
                    event

        # 登入邏輯
        def handle_login_logout(username, logged_in, new_username, password):
            if logged_in:  # 如果已登入，執行登出
                new_username, message, new_logged_in = logout()
            else:  # 如果未登入，執行登入
                new_username, message, new_logged_in = login(new_username, password)
            return (
                new_username,
                message,
                new_logged_in,
                gr.update(value=f"**Current User:** {new_username if new_username else 'Not logged in'}"),
                gr.update(value="Logout" if new_logged_in else "Login"),
                gr.update(visible=new_logged_in)
            )

        login_logout_button.click(
            handle_login_logout,
            inputs=[username_state, logged_in_state, username_input, password_input],
            outputs=[username_state, login_message, logged_in_state, user_display, login_logout_button, app_tabs]
        )

    return home

# 啟動應用（假設在 app.py 中調用）
if __name__ == "__main__":
    home_page().launch(server_name="0.0.0.0", server_port=7860, debug=True)


import gradio as gr
from pymongo import MongoClient
from pages.line_comment import line_comment_page
from pages.report_generator import report_generator_page
from pages.dialogue_comment import dialogue_comment_page
from pages.report_comment import report_comment_page

# 連接到 MongoDB
client = MongoClient("mongodb://ophthalmology_db_container:27017/")
db = client["ophthalmology_db"]
users_collection = db["users"]

# 登入驗證函數
def login(username, password):
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        return username, "Login successful!", True
    return None, "Invalid username or password.", False

# 登出函數
def logout():
    return None, "Logged out successfully!", False

# 主頁面
def home_page():
    with gr.Blocks() as home:
        # 儲存登入狀態
        username_state = gr.State(None)
        logged_in_state = gr.State(False)

        gr.Markdown("# LLM-Driven Generation and Summarization of Ophthalmology Dialogues")

        # 顯示當前使用者名稱和登入/登出選項
        with gr.Row():
            user_display = gr.Markdown("**Current User:** Not logged in")
            
        # 登入頁面
        with gr.Tab("Login"):
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
            login_message = gr.Textbox(label="Message", interactive=False)
            login_logout_button = gr.Button("Login")
            gr.Markdown("### Project: Streamline Ophthalmology Clinic Patient QA and Pre-Surgical Inquiry By Agentive LLMs")
            gr.Markdown("- Cataract is a common condition, yet limited consultation time often leaves patients without sufficient education about surgery and IOL options. This platform assists in improving patient understanding and decision-making with the help of AI-powered LLMs, reducing physician workload.")
            gr.Image("./assets/SchematicFlowDiagram.png", label="Cataract Overview", elem_classes="esponsive-image img")
            gr.Markdown("### Powered by\n - Director : SJ, Chen | Vice Dean : TF, Chen | Resident : KJ, Chang | PGY : WC, Fang | Fellow : SC, Chi | MSc : KR, Liu | MSc : YJ, Meng | MSc : MK, Chen")


        # 其他頁面（初始不可見）
        with gr.Tab("App Tabs", visible=False) as app_tabs:
            with gr.TabItem("Line Comment", id=1):
                # 傳遞 username_state 給 line_comment_page
                line_comment_page(username_state)
                # line_comment_page()
            with gr.TabItem("Report Generator", id=2):
                report_generator_page()
            with gr.TabItem("Dialogue Comment", id=3):
                dialogue_comment_page()
            with gr.TabItem("Report Comment", id=4):
                report_components = report_comment_page()
                for event in report_components["events"]:
                    event

        # 登入/登出邏輯
        def handle_login_logout(username, logged_in, new_username, password):
            if logged_in:  # 如果已登入，執行登出
                new_username, message, new_logged_in = logout()
            else:  # 如果未登入，執行登入
                new_username, message, new_logged_in = login(new_username, password)
            return (
                new_username,
                message,
                new_logged_in,
                gr.update(value=f"**Current User:** {new_username if new_username else 'Not logged in'}"),
                gr.update(value="Logout" if new_logged_in else "Login"),
                gr.update(visible=new_logged_in)
            )

        login_logout_button.click(
            handle_login_logout,
            inputs=[username_state, logged_in_state, username_input, password_input],
            outputs=[username_state, login_message, logged_in_state, user_display, login_logout_button, app_tabs]
        )

    return home