import gradio as gr
from database.db_utils_report import init_db
from utils import custom_css
from pages.home import home_page
from pages.dialogue_comment import dialogue_comment_page
from pages.report_comment import report_comment_page
from pages.report_generator import report_generator_page
from pages.line_comment import line_comment_page

init_db()

with gr.Blocks(css=custom_css, ) as app:
    with gr.Tabs(selected=0) as tabs:
        with gr.TabItem("Home", id=0):
            home_page()
        with gr.TabItem("Dialogue Comment", id=1):
            dialogue_comment_page()
        with gr.TabItem("Report Comment", id=2):
            report_components = report_comment_page()
            for event in report_components["events"]:
                event
        with gr.TabItem("Report Generator", id=3):
            report_generator_page()
        with gr.TabItem("Line Comment", id=4):
            line_comment_page()


app.launch(server_name="0.0.0.0", server_port=7860, debug=True)

# import gradio as gr
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from database.db_utils_report import init_db
# from utils import custom_css
# from pages.home import home_page
# from pages.dialogue_comment import dialogue_comment_page
# from pages.report_comment import report_comment_page
# from pages.report_generator import report_generator_page
# from pages.line_comment import line_comment_page
# import uvicorn
# import traceback

# try:
#     print("Initializing database...")
#     init_db()
#     print("Database initialized successfully.")

#     app = FastAPI()
#     app.mount("/static", StaticFiles(directory="/app/static"), name="static")

#     with gr.Blocks(css=custom_css) as demo:
#         with gr.Tabs(selected=0) as tabs:
#             with gr.TabItem("Home", id=0):
#                 home_page()
#             with gr.TabItem("Dialogue Comment", id=1):
#                 dialogue_comment_page()
#             with gr.TabItem("Report Comment", id=2):
#                 report_components = report_comment_page()
#                 for event in report_components["events"]:
#                     event
#             with gr.TabItem("Report Generator", id=3):
#                 report_generator_page()
#             with gr.TabItem("Line Comment", id=4):
#                 line_comment_page()

#     app = gr.mount_gradio_app(app, demo, path="/")
#     print("Gradio app mounted successfully.")

# except Exception as e:
#     print(f"Error during initialization: {e}")
#     traceback.print_exc()

# if __name__ == "__main__":
#     print("Starting Uvicorn server...")
#     uvicorn.run(app, host="0.0.0.0", port=7860)


# import gradio as gr
# from fastapi import FastAPI, Response
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import RedirectResponse
# from database.db_utils_report import init_db
# from utils import custom_css
# from pages.home import home_page
# from pages.dialogue_comment import dialogue_comment_page
# from pages.report_comment import report_comment_page
# from pages.report_generator import report_generator_page
# from pages.line_comment import line_comment_page
# import uvicorn
# import traceback

# try:
#     print("Initializing database...")
#     init_db()
#     print("Database initialized successfully.")

#     app = FastAPI()
#     app.mount("/static", StaticFiles(directory="/app/static"), name="static")

#     @app.get("/manifest.json")
#     async def redirect_manifest():
#         return RedirectResponse(url="/static/manifest.json")

#     with gr.Blocks(css=custom_css) as demo:
#         with gr.Tabs(selected=0) as tabs:
#             with gr.TabItem("Home", id=0):
#                 home_page()
#             with gr.TabItem("Dialogue Comment", id=1):
#                 dialogue_comment_page()
#             with gr.TabItem("Report Comment", id=2):
#                 report_components = report_comment_page()
#                 for event in report_components["events"]:
#                     event
#             with gr.TabItem("Report Generator", id=3):
#                 report_generator_page()
#             with gr.TabItem("Line Comment", id=4):
#                 line_comment_page()

#     app = gr.mount_gradio_app(app, demo, path="/")
#     print("Gradio app mounted successfully.")

# except Exception as e:
#     print(f"Error during initialization: {e}")
#     traceback.print_exc()

# if __name__ == "__main__":
#     print("Starting Uvicorn server...")
#     uvicorn.run(app, host="0.0.0.0", port=7860)