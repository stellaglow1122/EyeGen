# import gradio as gr
# import asyncio
# import time
# from services.GenReport import GenReport
# from services.EvalCitation import EvalCitation
# from services.EvalMetrics import EvalMetrics

# async def async_generate_report(dialogue, gen_model, user_type):
#     if not dialogue.strip():
#         yield "❗ Please paste dialogue text in the input box.", ""
#         return
#     try:
#         start = time.time()
#         yield "⏳ Generating report... Please wait.", ""

#         reporter = GenReport()
#         indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
#         report_content = await reporter.summary_report(indexed_dialogue, gen_model, user_type)
#         elapsed = time.time() - start
#         report_with_timer = f"{report_content}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"

#         yield report_with_timer, report_with_timer

#     except Exception as e:
#         yield f"❗ Error: {e}", ""

# async def async_evaluation_report(report_content, dialogue, eval_model):
#     if not report_content or not report_content.strip():
#         yield (
#             "❗ Please generate a report before evaluating.",
#             "❗ No report available.",
#             "❗ No report available."
#         )
#         return
#     try:
#         start = time.time()
#         yield "⏳ Evaluating report... Please wait.", "⏳", "⏳"

#         report_content = report_content.partition('---')[0].strip()
#         indexed_dialogue = GenReport().add_index_to_indexed_dialogue(dialogue)
#         citation_result = await EvalCitation().evaluate(report_content, indexed_dialogue, eval_model)
#         metrics = await EvalMetrics().compute(citation_result)

#         elapsed = time.time() - start
#         citation_result_with_timer = f"{citation_result}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"

#         yield citation_result_with_timer, metrics["citation_recall"], metrics["citation_precision"]

#     except Exception as e:
#         yield f"❗ Error: {e}", "", ""

# def copy_report(report_text):
#     if not report_text.strip():
#         return "", gr.update(visible=True, value="❗ No report to copy. Please generate a report first.")
#     return "", gr.update(visible=True, value="✅ Copy Report Successful!")

# def report_generator_page():
#     gr.Markdown("# LLM-Driven Summarization of Ophthalmology Dialogues")
#     gr.Image(value="./assets/GenReportWorkflow.png", elem_classes="esponsive-image img")

#     with gr.Row():
#         with gr.Column(scale=3):
#             gr.Markdown("## 💬 Dialogue")
#             dialogue_input = gr.Textbox(lines=20, label="", placeholder="Paste Dialogue text here...")

#             gen_model_dropdown = gr.Dropdown(
#                 choices=[
#                     "Llama3-TAIDE-LX-70B-Chat",
#                     "Llama-3.1-8B-Instruct",
#                     "Llama-3.1-Nemotron-70B-Instruct",
#                     "Llama-3.3-70B-Instruct",
#                     "Ministral-8B-Instruct-2410",
#                     "Mistral-Small-24B-Instruct-2501",
#                     "gpt-4o-mini"
#                 ],
#                 value="Llama-3.1-Nemotron-70B-Instruct",
#                 label="Select LLM to Generate Report"
#             )

#             user_dropdown = gr.Dropdown(
#                 choices=["Doctor", "Patient"],
#                 value="Doctor",
#                 label="Select User Type"
#             )

#             generate_button = gr.Button("Generating Report")
        
#         with gr.Column(scale=3):
#             gr.Markdown("## 📝 Report")
#             report_md = gr.Markdown(
#                 value="⬅️ Paste Dialogue text and click Generating Report\n\n" + "\n".join(["\u00a0" for _ in range(20)]),
#                 elem_id="output-md",
#                 elem_classes="scrollable report-content",
#                 show_label=False,
#                 container=False
#             )
#             report_text_state = gr.State("")

#             copy_status = gr.Markdown("", visible=False, elem_id="copy-status")
#             copy_button = gr.Button("Copy Report")

#             gr.Markdown("## 📊 Evaluation")

#             eval_model_dropdown = gr.Dropdown(
#                 choices=[
#                     "Llama3-TAIDE-LX-70B-Chat",
#                     "Llama-3.1-8B-Instruct",
#                     "Llama-3.1-Nemotron-70B-Instruct",
#                     "Llama-3.3-70B-Instruct",
#                     "Ministral-8B-Instruct-2410",
#                     "Mistral-Small-24B-Instruct-2501",
#                     "gpt-4o-mini"
#                 ],
#                 value="Ministral-8B-Instruct-2410",
#                 label="Select LLM to Evaluate Citation"
#             )

#             evaluate_button = gr.Button("Evaluating Report")

#             citation_recall = gr.Textbox(label="Citation Recall", interactive=False)
#             citation_precision = gr.Textbox(label="Citation Precision", interactive=False)
#             citation_result = gr.Textbox(lines=20, label="Citation Detail", placeholder="Show the evaluation citation detail", interactive=False)

#         # === Click Events ===
#         generate_button.click(
#             fn=async_generate_report,
#             inputs=[dialogue_input, gen_model_dropdown, user_dropdown],
#             outputs=[report_md, report_text_state]
#         )

#         copy_button.click(
#             fn=copy_report,
#             inputs=[report_text_state],
#             outputs=[report_md, copy_status]
#         )

#         evaluate_button.click(
#             fn=async_evaluation_report,
#             inputs=[report_text_state, dialogue_input, eval_model_dropdown],
#             outputs=[citation_result, citation_recall, citation_precision]
#         )

import gradio as gr
import time
from services.GenReport import GenReport
from services.EvalCitation import EvalCitation
from services.EvalMetrics import EvalMetrics

# --- Async Function: Generate Report ---
async def async_generate_report(dialogue, gen_model, user_type):
    if not dialogue or not isinstance(dialogue, str) or not dialogue.strip():
        yield "", ""
        return
    try:
        start = time.time()
        yield "⏳ Generating report... Please wait.", ""

        reporter = GenReport()
        indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
        report_content = await reporter.summary_report(indexed_dialogue, gen_model, user_type)
        elapsed = time.time() - start
        report_with_timer = f"{report_content}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"
        yield report_with_timer, report_content

    except Exception as e:
        yield f"❗ Error: {e}", ""

# --- Async Function: Evaluate Report ---
async def async_evaluation_report(report_content, dialogue, eval_model):
    if not dialogue or not dialogue.strip() or not report_content or not report_content.strip():
        yield "", "", ""
        return

    try:
        start = time.time()
        yield "⏳ Evaluating report... Please wait.", "⏳", "⏳"

        report_content = report_content.partition('---')[0].strip()


        indexed_dialogue = GenReport().add_index_to_indexed_dialogue(dialogue)
        citation_result = await EvalCitation().evaluate(report_content, indexed_dialogue, eval_model)

        if not isinstance(citation_result, list) or not citation_result or not isinstance(citation_result[0], dict):
            raise ValueError("Invalid input: expected a non-empty list of dictionaries.")

        metrics = await EvalMetrics().compute(citation_result)

        elapsed = time.time() - start
        citation_result_with_timer = f"{citation_result}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"

        yield citation_result_with_timer, metrics["citation_recall"], metrics["citation_precision"]

    except Exception as e:
        print(f"[Eval Error] {e}")
        yield f"❗ Error: {e}", "", ""

# --- Page UI ---
def report_generator_page():
    with gr.Blocks(css="""
        .scrollable { max-height: 450px; overflow-y: auto; }
    """) as demo:

        gr.Markdown("# LLM-Driven Summarization of Ophthalmology Dialogues")
        gr.Image(value="./assets/GenReportWorkflow.png", elem_classes="esponsive-image img")

        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("## 💬 Dialogue")
                dialogue_input = gr.Textbox(lines=20, label="", placeholder="Paste Dialogue text here first, then click Generating Report")

                gen_model_dropdown = gr.Dropdown(
                    choices=["Llama3-TAIDE-LX-70B-Chat", "Llama-3.1-8B-Instruct", "Llama-3.1-Nemotron-70B-Instruct",
                             "Llama-3.3-70B-Instruct", "Ministral-8B-Instruct-2410",
                             "Mistral-Small-24B-Instruct-2501", "gpt-4o-mini"],
                    value="Llama-3.1-Nemotron-70B-Instruct",
                    label="Select LLM to Generate Report"
                )

                user_dropdown = gr.Dropdown(choices=["Doctor", "Patient"], value="Doctor", label="User Type")
                generate_button = gr.Button("Generating Report")

            with gr.Column(scale=3):
                gr.Markdown("## 📝 Report")
                report_md = gr.Markdown("", elem_id="output-md", elem_classes="scrollable", show_label=False)
                report_text_state = gr.State("")

                copy_button = gr.Button("Copy Report")

                gr.Markdown("## 📊 Evaluation")
                eval_model_dropdown = gr.Dropdown(
                    choices=["Llama3-TAIDE-LX-70B-Chat", "Llama-3.1-8B-Instruct", "Llama-3.1-Nemotron-70B-Instruct",
                             "Llama-3.3-70B-Instruct", "Ministral-8B-Instruct-2410",
                             "Mistral-Small-24B-Instruct-2501", "gpt-4o-mini"],
                    value="Ministral-8B-Instruct-2410",
                    label="Select LLM to Evaluate Citation"
                )

                evaluate_button = gr.Button("Evaluating Report")
                citation_recall = gr.Textbox(label="Citation Recall", interactive=False)
                citation_precision = gr.Textbox(label="Citation Precision", interactive=False)
                citation_result = gr.Textbox(lines=20, label="Citation Detail", interactive=False)

        # ==== Button with JS Pop ====
        generate_button.click(
            fn=async_generate_report,
            inputs=[dialogue_input, gen_model_dropdown, user_dropdown],
            outputs=[report_md, report_text_state],
            preprocess=False,
            js="""
            (dialogue, model, user) => {
                if (!dialogue || dialogue.trim() === "") {
                    alert("❗ Please paste dialogue text in the input box.");
                    return [null, null, null];
                }
                return [dialogue, model, user];
            }
            """
        )


        copy_button.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                const content = document.getElementById('output-md')?.innerText.trim();
                if (!content) {
                    alert("❗ No report to copy. Please generate a report first.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Report copied successfully!");
            }
            """
        )
        
        evaluate_button.click(
            fn=async_evaluation_report,
            inputs=[report_md, dialogue_input, eval_model_dropdown],  # 用 report_md 直接當輸入
            outputs=[citation_result, citation_recall, citation_precision],
            preprocess=False,
            js="""
            (report, dialogue, model) => {
                const reportVal = report?.trim();
                const dialogueVal = dialogue?.trim();
                const modelVal = model?.trim();

                const isReportEmpty = !reportVal || reportVal === "";
                const isDialogueEmpty = !dialogueVal || dialogueVal === "";

                if (isReportEmpty && isDialogueEmpty) {
                    alert("❗ Missing dialogue content and report content for evaluation.");
                    return [null, null, null];
                }
                if (isReportEmpty) {
                    alert("❗ Missing report content for evaluation.");
                    return [null, null, null];
                }
                if (isDialogueEmpty) {
                    alert("❗ Missing dialogue content for evaluation.");
                    return [null, null, null];
                }
                return [reportVal, dialogueVal, modelVal];
            }
            """
        )







