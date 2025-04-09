import gradio as gr
import asyncio
import time
from services.GenReport import GenReport

async def async_generate_report(dialogue, gen_model, user_type):
    try:
        start = time.time()
        yield "⏳ Generating report... Please wait."

        reporter = GenReport()
        formatted_report = await reporter.summary_report(dialogue, gen_model, user_type)
        elapsed = time.time() - start
        report_with_timer = f"{formatted_report}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"

        yield report_with_timer

    except Exception as e:
        yield f"❌ Error: {e}"



def report_generator_page():
    gr.Markdown("# LLM-Driven Summarization of Ophthalmology Dialogues")
    gr.Image(value="./assets/GenReportWorkflow.png", elem_classes="esponsive-image img")

    with gr.Row():
        # === Column 1: Dialogue Input ===
        with gr.Column(scale=3):
            gr.Markdown("## 💬 Dialogue")
            dialogue_input = gr.Textbox(lines=20, label="", placeholder="Paste dialogue text here...")

            gen_model_dropdown = gr.Dropdown(
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
                choices=["Doctor", "Patient"],
                value="Doctor",
                label="Select User Type"
            )

            generate_button = gr.Button("Generate Report", interactive=False)

            # Enable/disable button based on input
            dialogue_input.change(
                lambda text: gr.update(interactive=bool(text.strip())),
                inputs=dialogue_input,
                outputs=generate_button
            )

        # === Column 2: Report Output ===
        with gr.Column(scale=3):
            gr.Markdown("## 📝 Report")
            output_md = gr.Markdown(
                value="⬅️ Paste dialogue text and click Generate Report\n\n" + "\n".join(["\u00a0" for _ in range(20)]),
                label="Report Content",
                elem_id="output-md",
                elem_classes="scrollable report-content",
                show_label=False,
                container=False
            )

            copy_status = gr.Markdown("", visible=False, elem_id="copy-status")
            copy_button = gr.Button("Copy Report", interactive=False)


            gr.Markdown("## 📊 Evaluation (Coming Soon)")
            
            eval_model_dropdown = gr.Dropdown(
                choices=[
                    "gpt-4o-mini"
                ],
                value="gpt-4o-mini",
                label="Select LLM to Evaluate Citation (Coming Soon)"
            )
            
            evaluate_button = gr.Button("Evaluate Report (Coming Soon)", interactive=False)
            citation_recall = gr.Textbox(label="Citation Recall", interactive=False)
            citation_precision = gr.Textbox(label="Citation Precision", interactive=False)


        # === Click Action ===
        generate_button.click(
            fn=async_generate_report,
            inputs=[dialogue_input, gen_model_dropdown, user_dropdown],
            outputs=[output_md]
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
