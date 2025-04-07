import gradio as gr
import asyncio
import time
from services.GenReport import GenReport

# Initialize the report generator tool
gen_report_tool = GenReport()

def run_async(func):
    """Utility wrapper to run async function in sync context."""
    return asyncio.run(func)

def generate_report(dialogue, model_name, user_type):
    try:
        start = time.time()
        placeholder = "⏳ Generating report... Please wait."
        yield placeholder
        report = run_async(gen_report_tool.summary_report(dialogue, model_name, user_type))
        elapsed = time.time() - start
        final_output = f"{report}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"
        yield final_output
    except Exception as e:
        yield f"❌ Error: {str(e)}"

def report_generator_page():
    with gr.Row():
        # === Column 1: Dialogue Input ===
        with gr.Column(scale=3):
            gr.Markdown("### 💬 Dialogue Input")
            dialogue_input = gr.Textbox(lines=20, label="Dialogue Content", placeholder="Paste dialogue text here...")

        # === Column 2: Controls ===
        with gr.Column(scale=2):
            gr.Markdown("### ⚙️ Configuration")
            model_dropdown = gr.Dropdown(
                choices=[
                    "Llama3-TAIDE-LX-70B-Chat",
                    "Llama-3.1-8B-Instruct",
                    "Llama-3.1-Nemotron-70B-Instruct",
                    "Llama-3.3-70B-Instruct",
                    "Ministral-8B-Instruct-2410",
                    "Mistral-Small-24B-Instruct-2501",
                    "gpt-4o-mini"
                ],
                value="Llama-3.1-8B-Instruct",
                label="Select LLM to Generate Report"
            )

            user_dropdown = gr.Dropdown(
                choices=["doctor", "patient"],
                value="doctor",
                label="Select Report Format"
            )

            eval_model_dropdown = gr.Dropdown(
                choices=[
                    "Llama3-TAIDE-LX-70B-Chat",
                    "Llama-3.1-8B-Instruct",
                    "gpt-4o-mini"
                ],
                value="gpt-4o-mini",
                label="LLM for Evaluation (Coming Soon)",
                interactive=False
            )

            generate_button = gr.Button("Generate Report", interactive=False)

            # Enable/disable button based on input
            dialogue_input.change(
                lambda text: gr.update(interactive=bool(text.strip())),
                inputs=dialogue_input,
                outputs=generate_button
            )

        # === Column 3: Report Output ===
        with gr.Column(scale=5):
            gr.Markdown("### 📝 Summary Report")
            output_md = gr.Markdown(
                value="⬅️ Paste conversation text and click Generate Report\n\n" + "\n".join(["\u00a0" for _ in range(20)]),
                label="Report Content",
                elem_id="output-md",
                elem_classes="scrollable report-content",
                show_label=False,
                container=False
            )

            copy_status = gr.Markdown("", visible=False, elem_id="copy-status")
            copy_button = gr.Button("📋 Copy Report", interactive=False)

            gr.Markdown("### 📊 Evaluation Result")
            citation_recall = gr.Textbox(label="Citation Recall", interactive=False)
            citation_precision = gr.Textbox(label="Citation Precision", interactive=False)

            gr.Button("Add Report to Database (Coming Soon)", interactive=False)

        # === Click Action ===
        generate_button.click(
            fn=generate_report,
            inputs=[dialogue_input, model_dropdown, user_dropdown],
            outputs=output_md
        ).then(
            lambda val: gr.update(interactive=bool(val.strip())),
            inputs=output_md,
            outputs=copy_button
        )

        copy_button.click(
            fn=None,
            inputs=[],
            outputs=[],
            js="""
            () => {
                const md = document.getElementById('output-md');
                if (md) {
                    navigator.clipboard.writeText(md.innerText);
                }
                const status = document.getElementById('copy-status');
                if (status) {
                    status.style.display = "block";
                    status.innerText = "✅ Copy Report Successful!";
                    setTimeout(() => {
                        status.style.display = "none";
                    }, 2000);
                }
            }
            """
        )
