# pages/summary_report_page.py
import gradio as gr

def summary_report_page():
    with gr.Column():
        gr.Markdown("# Displays a Table Containing Line System Dialogues and Summary Reports (Coming Soon)")
        gr.Markdown("Medical staff can use this page to review the dialogues and summary report, quickly understand the patient's main complaint and the recommended medical unit to go to.")
    return None