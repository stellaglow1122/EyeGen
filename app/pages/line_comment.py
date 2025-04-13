from datetime import datetime
import pandas as pd
import pytz
import gradio as gr
import uuid
from database.LineComment2db import get_line_list, get_line_by_idx, submit_comment, lock_report, unlock_report

def line_comment_page():
    display_headers = ["IDX", "User", "Type", "Upload Time", "State", "Comment Time", "Score", "Comment"]
    original_columns = ["idx", "user_name", "user_type", "upload_time", "comment_state", "comment_time", "comment_score", "comment_content"]

    def calc_comment_stats():
        df = pd.DataFrame(get_line_list())
        total_comments = df['comment_state'].eq('Y').sum()
        total_reports = len(df)
        percentage = (total_comments / total_reports * 100) if total_reports > 0 else 0
        return f"<h2>🚩 Comment Progress: {total_comments}/{total_reports} ({percentage:.1f}%)</h2>"

    def get_display_df(search_term=""):
        # print("Starting get_display_df")
        data = get_line_list()
        # print(f"Retrieved {len(data)} rows from MongoDB")
        df = pd.DataFrame(data)

        for col in original_columns:
            if col not in df.columns:
                df[col] = "" if col != "comment_score" else 0

        df = df.fillna("")
        df = df.sort_values(by="upload_time", ascending=False)

        if search_term:
            mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            df = df[mask]

        filtered_df = df.head(50)  # 限制為前 50 行
        display_df = filtered_df[original_columns].copy()
        display_df.columns = display_headers
        # print(f"Returning display_df with {len(display_df)} rows")

        return display_df, calc_comment_stats(), filtered_df, search_term

    def update_details(evt: gr.SelectData, table_data, session_id):
        if evt.index is None:
            return ["", "", "", "", "Please select a row from the table to display the dialogue.", "Please select a row from the table to display the report.", "", 0, "", "N", None, True, True, session_id]

        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(table_data, columns=display_headers)
        current_table.columns = original_columns
        if idx >= len(current_table):
            return ["", "", "", "", "Out of range", "Out of range", "", 0, "", "N", None, True, True, session_id]

        selected_idx = current_table.iloc[idx]['idx']
        row = get_line_by_idx(selected_idx)  # 強制刷新
        # print(">>> dialogue_content:", row.get("dialogue_content"))
        # print(">>> report_content:", row.get("report_content"))

        # 嘗試鎖定該行
        locked = lock_report(selected_idx, session_id)
        # print(f"In update_details, lock check result for idx {selected_idx}: locked={locked}")

        if not locked:
            message = "⚠️ This report is locked by another user."
            return [
                row.get("idx", ""),
                row.get("user_name", ""),
                row.get("user_type", ""),
                row.get("upload_time", ""),
                row.get("dialogue_content", ""),
                row.get("report_content", ""),
                row.get("comment_time", ""),
                row.get("comment_score", 0),
                row.get("comment_content", ""),
                gr.update(value=row.get("comment_state", "N"), visible=True),
                gr.update(value=message, visible=True),
                selected_idx,
                gr.update(interactive=False),  # 禁用 comment_box
                gr.update(interactive=False),  # 禁用 comment_score
                session_id
            ]

        return [
            row.get("idx", ""),
            row.get("user_name", ""),
            row.get("user_type", ""),
            row.get("upload_time", ""),
            row.get("dialogue_content", ""),
            row.get("report_content", ""),
            row.get("comment_time", ""),
            row.get("comment_score", 0),
            row.get("comment_content", ""),
            gr.update(value=row.get("comment_state", "N"), visible=True),
            gr.update(value="", visible=False),
            selected_idx,
            gr.update(interactive=True),
            gr.update(interactive=True),
            session_id
        ]

    def refresh_table(search_term, selected_idx, session_id):
        # print("Starting refresh_table")
        # 刷新表格
        updated_display_df, stats_html, filtered_df, search_term = get_display_df(search_term)
        # print("Table data refreshed")

        # 如果有選擇的行，檢查鎖定狀態並更新欄位
        if not selected_idx or selected_idx.strip() == "":
            # print("No row selected during refresh")
            return (
                gr.update(value=updated_display_df, visible=True, interactive=True),
                gr.update(value=stats_html, visible=True),
                filtered_df,
                search_term,
                gr.update(value="Please select a row from the table to display the dialogue.", visible=True),
                gr.update(value="Please select a row from the table to display the report.", visible=True),
                gr.update(value="", visible=True, interactive=True),
                gr.update(value=0, visible=True, interactive=True),
                gr.update(value="", visible=False),
                session_id
            )

        row = get_line_by_idx(selected_idx)
        locked = lock_report(selected_idx, session_id)
        # print(f"In refresh_table, lock check result for idx {selected_idx}: locked={locked}")

        if not locked:
            message = "⚠️ This report is locked by another user."
            return (
                gr.update(value=updated_display_df, visible=True, interactive=True),
                gr.update(value=stats_html, visible=True),
                filtered_df,
                search_term,
                gr.update(value=row.get("dialogue", ""), visible=True),
                gr.update(value=row.get("report", ""), visible=True),
                gr.update(value=row.get("comment_content", ""), visible=True, interactive=False),
                gr.update(value=row.get("comment_score", 0), visible=True, interactive=False),
                gr.update(value=message, visible=True),
                session_id
            )

        return (
            gr.update(value=updated_display_df, visible=True, interactive=True),
            gr.update(value=stats_html, visible=True),
            filtered_df,
            search_term,
            gr.update(value=row.get("dialogue_content", ""), visible=True),
            gr.update(value=row.get("report_content", ""), visible=True),
            gr.update(value=row.get("comment_content", ""), visible=True, interactive=True),
            gr.update(value=row.get("comment_score", 0), visible=True, interactive=True),
            gr.update(value="", visible=False),
            session_id
        )

    def save_comment_fn(comment_content, comment_score, selected_idx, search_term, session_id):
        # print(f"Starting save_comment_fn for idx: {selected_idx}, session_id: {session_id}")
        try:
            if not selected_idx or selected_idx.strip() == "":
                # print("No idx selected")
                return (
                    gr.update(), gr.update(), gr.update(value="⚠️ No row selected.", visible=True),
                    gr.update(), gr.update(), gr.update(), gr.update(value=""), gr.update(value=0),
                    gr.update(visible=True), session_id
                )

            locked = lock_report(selected_idx, session_id)
            # print(f"Lock check result: locked={locked}")
            if not locked:
                # print("Submission failed due to lock")
                return (
                    gr.update(), gr.update(),
                    gr.update(), gr.update(),
                    gr.update(), gr.update(),
                    gr.update(value=""), gr.update(value=0),
                    gr.update(value="⚠️ Submission failed: This report is locked by another user.", visible=True),
                    session_id
                )

            # print(f"Submitting comment: {comment_content}, score: {comment_score}")
            is_empty = not comment_content.strip() and comment_score == 0
            new_state = "N" if is_empty else "Y"
            taipei_tz = pytz.timezone("Asia/Taipei")
            now = "" if is_empty else datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            submit_comment(selected_idx, comment_content.strip(), comment_score, new_state, now)
            # print("Comment submitted")

            # print("Refreshing table")
            updated_display_df, stats_html, filtered_df, search_term = get_display_df(search_term)
            row = get_line_by_idx(selected_idx)
            # print("Table refreshed")

            # print(f"Returning updated_display_df with {len(updated_display_df)} rows")
            # print(f"Returning stats_html: {stats_html}")
            # print(f"Returning comment_state: {row.get('comment_state', 'N')}")
            # print(f"Returning comment_time: {row.get('comment_time', '')}")

            return (
                gr.update(value=updated_display_df, visible=True, interactive=True),
                gr.update(value=stats_html, visible=True),
                gr.update(value=row.get("comment_state", "N"), visible=True, interactive=False),
                gr.update(value=row.get("comment_time", ""), visible=True, interactive=False),
                filtered_df,
                search_term,
                gr.update(value=comment_content, visible=True, interactive=True),  # 保持提交的內容
                gr.update(value=comment_score, visible=True, interactive=True),  # 保持提交的分數
                gr.update(value="", visible=False),
                session_id
            )
        except Exception as e:
            print(f"Error in save_comment_fn: {e}")
            unlock_report(selected_idx)  # 確保異常時解鎖
            return (
                gr.update(), gr.update(),
                gr.update(), gr.update(),
                gr.update(), gr.update(),
                gr.update(value=""), gr.update(value=0),
                gr.update(value=f"⚠️ Submission failed: {str(e)}", visible=True),
                session_id
            )

    with gr.Blocks() as demo:
        gr.Markdown("# Line Comment Page")

        filtered_df_state = gr.State()
        search_term_state = gr.State("")
        session_id_state = gr.State(str(uuid.uuid4()))
        selected_idx_hidden = gr.Textbox(visible=False)

        search_input = gr.Textbox(label="🔍 Search", placeholder="Enter keyword to filter table...")
        comment_stats = gr.HTML()

        gr.Markdown("## 📂 Report List")
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Table")
        table = gr.Dataframe(
            interactive=False,
            label="Report List",
            show_label=False,
            row_count=(1, "dynamic"),
            elem_classes="table-scroll"
        )
           
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 👤 Comment")
            idx_box = gr.Textbox(label="IDX", interactive=False)
            user_name = gr.Textbox(label="User Name", interactive=False)
            user_type = gr.Textbox(label="User Type", interactive=False)
            upload_time = gr.Textbox(label="Upload Time", interactive=False)

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 💬 Dialogue")
                dialogue_box = gr.Markdown("Click a row to view its dialogue.", elem_classes="scrollable report-content", elem_id="dialogue-md")
                copy_dialogue_btn = gr.Button("Copy Dialogue")

            with gr.Column():
                gr.Markdown("## 📝 Report")
                report_box = gr.Markdown("Click a row to view its report.", elem_classes="scrollable report-content", elem_id="report-md")
                copy_report_btn = gr.Button("Copy Report")

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📢 Comment")
                comment_time = gr.Textbox(label="Comment Time", interactive=False, visible=True)
                comment_state = gr.Textbox(label="Comment State", interactive=False, visible=True)
                comment_score = gr.Slider(minimum=0, maximum=5, step=1, label="Comment Score", visible=True)
                comment_box = gr.Textbox(label="Comment Content", lines=10, placeholder="Type any comments here...", elem_classes="scrollable", visible=True)
                lock_message = gr.Textbox(label="Lock Status", interactive=False, visible=False)
                submit_btn = gr.Button("Submit Comment ✅")

        demo.load(
            fn=lambda: list(get_display_df("")) + [str(uuid.uuid4())],
            inputs=[],
            outputs=[table, comment_stats, filtered_df_state, search_term_state, session_id_state],
            queue=False
        )

        search_input.change(
            get_display_df,
            inputs=[search_input],
            outputs=[table, comment_stats, filtered_df_state, search_term_state],
            queue=False
        )

        table.select(
            fn=update_details,
            inputs=[table, session_id_state],
            outputs=[
                idx_box, user_name, user_type, upload_time,
                dialogue_box, report_box, comment_time, comment_score,
                comment_box, comment_state, lock_message, selected_idx_hidden,
                comment_box, comment_score, session_id_state
            ],
            queue=False
        )

        submit_btn.click(
            fn=save_comment_fn,
            inputs=[comment_box, comment_score, selected_idx_hidden, search_term_state, session_id_state],
            outputs=[
                table, comment_stats, comment_state, comment_time,
                filtered_df_state, search_term_state, comment_box, comment_score,
                lock_message, session_id_state
            ],
            queue=False
        )

        refresh_btn.click(
            fn=refresh_table,
            inputs=[search_term_state, selected_idx_hidden, session_id_state],
            outputs=[
                table, comment_stats, filtered_df_state, search_term_state,
                dialogue_box, report_box, comment_box, comment_score,
                lock_message, session_id_state
            ],
            queue=False
        )

        copy_dialogue_btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                const content = document.getElementById('dialogue-md')?.innerText.trim();
                if (content=="Click a row to view its dialogue.") {
                    alert("Please select a row from the table to display the dialogue.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Dialogue copied successfully!");
            }
            """
        )

        copy_report_btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                const content = document.getElementById('report-md')?.innerText.trim();
                if (content=="Click a row to view its report.") {
                    alert("Please select a row from the table to display the report.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Report copied successfully!");
            }
            """
        )

    return demo