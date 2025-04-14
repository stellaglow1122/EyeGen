import gradio as gr
from pages.home import home_page

if __name__ == "__main__":
    # start gradio app
    home_page().launch(server_name="0.0.0.0", server_port=7860, debug=True)