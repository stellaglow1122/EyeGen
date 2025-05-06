import gradio as gr
import time
from services.GenReport import GenReport
from services.EvalCitation import EvalCitation
from services.EvalMetrics import EvalMetrics

# --- Async Function: Generate Report ---
async def async_generate_report(dialogue, gen_model, object_type):
    if not dialogue or not isinstance(dialogue, str) or not dialogue.strip():
        yield "", "", ""
        return
    try:
        start = time.time()
        yield "⏳ Generating report... Please wait.", "⏳ Generating report... Please wait.", ""

        reporter = GenReport()
        indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
        report_content = await reporter.summary_report(indexed_dialogue, gen_model, object_type)
        elapsed = time.time() - start
        report_with_timer = f"{report_content}\n\n---\n⏱️ Elapsed time: {elapsed:.2f} seconds"
        yield indexed_dialogue, report_with_timer, report_content

    except Exception as e:
        yield f"❗ Error: {e}", "", ""

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

        # 最上方：Dialogue 區塊
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 💬 Dialogue")
                dialogue_input = gr.Textbox(
                    lines=10,
                    label="",
                    placeholder="Paste Dialogue text here first, then click Generating Report",
                    elem_classes="scrollable"
                )
                gen_model_dropdown = gr.Dropdown(
                    choices=[
                        "Llama3-TAIDE-LX-70B-Chat", "Llama-3.1-8B-Instruct", "Llama-3.1-Nemotron-70B-Instruct",
                        "Llama-3.3-70B-Instruct", "Ministral-8B-Instruct-2410",
                        "Mistral-Small-24B-Instruct-2501", "gpt-4o-mini"
                    ],
                    value="Llama-3.1-Nemotron-70B-Instruct",
                    label="Select LLM to Generate Report"
                )
                user_dropdown = gr.Dropdown(
                    choices=["Doctor", "Patient"],
                    value="Doctor",
                    label="User Type"
                )
                generate_button = gr.Button("Generating Report")

        # 中間：Indexed Dialogue 和 Report 區塊（左右分欄）
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("## 📃 Indexed Dialogue")
                indexed_dialogue_md = gr.Markdown(
                    "",
                    elem_id="indexed_dialogue_md",
                    elem_classes="scrollable",
                    show_label=False
                )
                copy_dialogue_button = gr.Button("Copy Dialogue")
            with gr.Column(scale=3):
                gr.Markdown("## 📝 Report")
                report_md = gr.Markdown(
                    "",
                    elem_id="output-md",
                    elem_classes="scrollable",
                    show_label=False
                )
                report_text_state = gr.State("")
                copy_report_button = gr.Button("Copy Report")

        # 最下方：Evaluation 區塊
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📊 Evaluation")
                eval_model_dropdown = gr.Dropdown(
                    choices=[
                        "Llama3-TAIDE-LX-70B-Chat", "Llama-3.1-8B-Instruct", "Llama-3.1-Nemotron-70B-Instruct",
                        "Llama-3.3-70B-Instruct", "Ministral-8B-Instruct-2410",
                        "Mistral-Small-24B-Instruct-2501", "gpt-4o-mini"
                    ],
                    value="Ministral-8B-Instruct-2410",
                    label="Select LLM to Evaluate Citation"
                )
                evaluate_button = gr.Button("Evaluating Report")
                citation_recall = gr.Textbox(label="Citation Recall", placeholder="Citation recall here...", interactive=False)
                citation_precision = gr.Textbox(label="Citation Precision", placeholder="Citation precision here...", interactive=False)
                citation_result = gr.Textbox(lines=10, label="Citation Detail", placeholder="Citation information here...", interactive=False)

        # ==== Button with JS Pop ====
        generate_button.click(
            fn=async_generate_report,
            inputs=[dialogue_input, gen_model_dropdown, user_dropdown],
            outputs=[indexed_dialogue_md, report_md, report_text_state],
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

        copy_dialogue_button.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                const content = document.getElementById('indexed_dialogue_md')?.innerText.trim();
                if (!content) {
                    alert("❗ No indexed dialogue to copy. Please generate a report first.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Indexed Dialogue copied successfully!");
            }
            """
        )


        copy_report_button.click(
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
            inputs=[report_md, dialogue_input, eval_model_dropdown],
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







