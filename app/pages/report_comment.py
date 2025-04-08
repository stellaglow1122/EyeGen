import gradio as gr
import pandas as pd
from database.db_utils_report import get_report_list, get_report_by_id, submit_comment, get_next_uncommented_report, get_prev_uncommented_report
from datetime import datetime

def report_comment_page():
    def calc_comment_stats():
        report_data = get_report_list()
        df = pd.DataFrame(report_data)
        total_comments = df['comment_state'].eq('Y').sum()
        total_reports = len(df)
        percentage = (total_comments / total_reports * 100) if total_reports > 0 else 0
        return f"<h2>🚩 Comment Progress: {total_comments}/{total_reports} ({percentage:.1f}%)</h2>"

    def get_display_df(search_term=""):
        report_data = get_report_list()
        df = pd.DataFrame(report_data)
        required_columns = ["report_id", "gen_model", "upload_time", "citation_recall", "citation_precision", 
                            "comment_state", "comment_content", "comment_time", "comment_score"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = "" if col not in ["comment_score", "citation_recall", "citation_precision"] else 0
        df = df.fillna({"comment_content": "", "comment_state": "N", "comment_time": "", "comment_score": 0})
        display_columns = ["report_id", "gen_model", "upload_time", "citation_recall", "citation_precision", 
                           "comment_state", "comment_content", "comment_time", "comment_score"]
        filtered_df = df[display_columns]

        if search_term:
            # Convert all fields to strings and check if they contain the search term (ignore case)
            mask = filtered_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            filtered_df = filtered_df[mask]
        return filtered_df

    # Define the header and raw column mapping for display
    display_headers = ["Report ID", "Gen LLM", "Upload Time", "Recall", "Precision", 
                       "State", "Content", "Comment Time", "Score"]
    original_columns = ["report_id", "gen_model", "upload_time", "citation_recall", "citation_precision", 
                        "comment_state", "comment_content", "comment_time", "comment_score"]

    def get_display_df_with_headers(search_term=""):
        raw_df = get_display_df(search_term)
        if raw_df.empty:
            # If the data is empty, return an empty DataFrame with a custom header.
            return pd.DataFrame(columns=display_headers)
        else:
            # Mapping raw data to display headers
            display_df = raw_df.copy()
            display_df.columns = display_headers
            return display_df

    initial_df = get_display_df()
    print(f"Initial base_df shape: {initial_df.shape}, Comment state counts: {initial_df['comment_state'].value_counts().to_dict()}")
    print(f"Initial top 5 report_ids: {initial_df['report_id'].head().tolist()}")

    filtered_df_state = gr.State(initial_df.copy())
    search_term_state = gr.State("")

    gr.Markdown("# Report Rating System")

    with gr.Column():
       
        with gr.Row():
            search_input = gr.Textbox(label="🔍 Search Reports", placeholder="Enter any keyword to filter the table (press Enter)...")
            comment_stats = gr.HTML(value=calc_comment_stats, elem_classes="comment-stats")
        
        gr.Markdown("## 📂 Report List")
        report_table = gr.Dataframe(
            value=get_display_df_with_headers,
            interactive=False,
            label="Report List",
            show_label=False,
            wrap=False,
            elem_classes="table-scroll",
            row_count=10,
        )

        gr.Markdown("", elem_classes="spacer")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📝 Report")
                report_content = gr.Markdown("Click a report_id in the table to view its content.", elem_classes="scrollable report-content")
            with gr.Column(scale=1):
                gr.Markdown("## 📢 Comment")
                report_id_display = gr.Markdown("**Report ID:** Not Selected")
                comment_state_display = gr.Markdown("**Comment State:** Not Selected")
                comment_time = gr.Markdown("**Comment Time:** Not Commented")
                comment_input = gr.Textbox(label="Comment Content", lines=10, max_lines=50)
                comment_score = gr.Slider(0, 5, step=1, label="Comment Score", value=0)
                submit_btn = gr.Button("Submit Comment ✅")
                prev_btn = gr.Button("⬅️ Previous Unreviewed")
                next_btn = gr.Button("Next Unreviewed ➡️")
                selected_report_id = gr.State(value=None)

    def filter_reports(search_term, current_df):
        filtered_df = get_display_df(search_term)
        display_df = filtered_df.copy()
        display_df.columns = display_headers  # Make sure to display the header
        print(f"Filter applied - Search term: '{search_term}', Filtered shape: {filtered_df.shape}")
        print(f"Filter top 5 report_ids: {filtered_df['report_id'].head().tolist()}")
        return display_df, calc_comment_stats(), filtered_df, search_term

    def update_report_details(evt: gr.SelectData, table_data):
        if evt.index is None or table_data is None or len(table_data) == 0:
            return "<h2>No reports available or none selected.</h2>", "**Report ID:** Not Selected", "**Comment State:** Not Selected", "**Comment Time:** Not Commented", "", 0, None
        row_idx = evt.index[0] if isinstance(evt.index, (tuple, list)) else evt.index
        # Convert table_data back to original column names
        current_table_df = pd.DataFrame(table_data, columns=display_headers)
        current_table_df.columns = original_columns  # Mapping back to original column
        if row_idx >= len(current_table_df) or row_idx < 0:
            return "<h2>Invalid selection.</h2>", "**Report ID:** Not Selected", "**Comment State:** Not Selected", "**Comment Time:** Not Commented", "", 0, None
        report_id = current_table_df.iloc[row_idx]["report_id"]
        print(f"Selected - row_idx: {row_idx}, report_id: {report_id}, Table shape: {current_table_df.shape}")
        report = get_report_by_id(report_id)
        if report:
            return (
                f"{report.get('report_content', '')}",
                f"**Report ID:** {report['report_id']}",
                f"**Comment State:** {report.get('comment_state', 'N')}",
                f"**Comment Time:** {report.get('comment_time', 'Not Commented')}",
                report.get('comment_content', ''),
                report.get('comment_score', 0),
                report['report_id']
            )
        return f"<h2>Report not found.</h2>", f"**Report ID:** {report_id}", "**Comment State:** N", "**Comment Time:** Not Commented", "", 0, report_id

    def submit_comment_fn(comment_content, comment_score, current_report_id, df, search_term):
        if current_report_id is None or df.empty:
            empty_df = pd.DataFrame(columns=display_headers)
            return "<h2>No report selected.</h2>", "**Report ID:** Not Selected", "**Comment State:** Not Selected", "**Comment Time:** Not Commented", "", 0, empty_df, calc_comment_stats(), df, search_term
        new_state = "Y" if comment_content or comment_score > 0 else "N"
        new_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_state == "Y" else None
        submit_comment(current_report_id, comment_content, comment_score, new_state, new_time)
        print(f"Submitted - report_id: {current_report_id}, comment_content: '{comment_content}', comment_score: {comment_score}, comment_state: {new_state}, comment_time: {new_time}")
        filtered_df = get_display_df(search_term)
        display_df = filtered_df.copy()
        display_df.columns = display_headers
        print(f"Submit update top 5 report_ids: {filtered_df['report_id'].head().tolist()}")
        report = get_report_by_id(current_report_id)
        return (
            f"{report.get('report_content', '')}",
            f"**Report ID:** {current_report_id}",
            f"**Comment State:** {report.get('comment_state', 'N')}",
            f"**Comment Time:** {report.get('comment_time', 'Not Commented')}",
            report.get('comment_content', ''),
            report.get('comment_score', 0),
            display_df,
            calc_comment_stats(),
            filtered_df,
            search_term
        )

    def navigate_uncommented(direction, current_report_id, df):
        current_id = current_report_id if current_report_id else ""
        next_report = get_next_uncommented_report(current_id) if direction == "next" else get_prev_uncommented_report(current_id)
        if next_report:
            print(f"Navigated {direction} - report_id: {next_report['report_id']}")
            return (
                f"{next_report.get('report_content', '')}",
                f"**Report ID:** {next_report['report_id']}",
                f"**Comment State:** {next_report.get('comment_state', 'N')}",
                f"**Comment Time:** {next_report.get('comment_time', 'Not Commented')}",
                next_report.get('comment_content', ''),
                next_report.get('comment_score', 0),
                next_report['report_id']
            )
        return "<h2>No unreviewed reports available.</h2>", "**Report ID:** Not Selected", "**Comment State:** N", "**Comment Time:** Not Commented", "", 0, None

    return {
        "components": [search_input, comment_stats, report_table, report_content, report_id_display, comment_state_display, comment_time, comment_input, comment_score, submit_btn, prev_btn, next_btn, filtered_df_state, search_term_state, selected_report_id],
        "events": [
            search_input.change(filter_reports, inputs=[search_input, filtered_df_state], outputs=[report_table, comment_stats, filtered_df_state, search_term_state]),
            report_table.select(update_report_details, inputs=[report_table], outputs=[report_content, report_id_display, comment_state_display, comment_time, comment_input, comment_score, selected_report_id]),
            submit_btn.click(submit_comment_fn, inputs=[comment_input, comment_score, selected_report_id, filtered_df_state, search_term_state], outputs=[report_content, report_id_display, comment_state_display, comment_time, comment_input, comment_score, report_table, comment_stats, filtered_df_state, search_term_state]),
            next_btn.click(navigate_uncommented, inputs=[gr.State("next"), selected_report_id, filtered_df_state], outputs=[report_content, report_id_display, comment_state_display, comment_time, comment_input, comment_score, selected_report_id]),
            prev_btn.click(navigate_uncommented, inputs=[gr.State("prev"), selected_report_id, filtered_df_state], outputs=[report_content, report_id_display, comment_state_display, comment_time, comment_input, comment_score, selected_report_id])
        ]
    }
