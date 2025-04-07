import gradio as gr
from database.db_utils_report import init_db
from utils import custom_css
from pages.home import home_page
from pages.report_comment import report_comment_page
from pages.dialogue_comment import dialogue_comment_page
from pages.report_generator import report_generator_page

init_db()

with gr.Blocks(css=custom_css) as app:
    with gr.Tabs(selected=0) as tabs:
        with gr.TabItem("Home", id=0):
            home_page()
        with gr.TabItem("Dialogue Comment", id=1):
            dialogue_components = dialogue_comment_page()
        with gr.TabItem("Report Comment", id=2):
            report_components = report_comment_page()
            for event in report_components["events"]:
                event
        with gr.TabItem("Report Generator", id=3):
            report_generator = report_generator_page()


app.launch(server_name="0.0.0.0", server_port=7860, debug=True)