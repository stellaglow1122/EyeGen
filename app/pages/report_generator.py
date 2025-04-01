import gradio as gr

def report_generator_page():
    with gr.Column():
        gr.Markdown("# Expected content")
        gr.Markdown("- Generate reports and citation recall and precision based on dialogue data")
    return None