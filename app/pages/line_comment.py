from datetime import datetime
import pandas as pd
import pytz
import gradio as gr
from database.LineComment2db import get_line_list, get_line_by_idx, get_comments_by_idx, submit_comment, line_comment_coll

def line_comment_page(username_state):
    display_headers = ["IDX", "Upload time", "Name", "Type", "Number of comment"]
    original_columns = ["idx", "upload_time", "object_name", "object_type"]
    comment_headers = ["IDX", "Comment time", "User", "Comment content", "Score"]
    comment_columns = ["idx", "comment_time", "user_name", "comment_content", "comment_score"]

    def get_display_df(search_term=""):
        data = get_line_list()
        df = pd.DataFrame(data)

        for col in original_columns:
            if col not in df.columns:
                df[col] = ""

        df = df.fillna("")

        # 統計每個 idx 的評論數量
        comment_counts = {}
        all_comments = list(line_comment_coll.find({}, {"idx": 1, "_id": 0}))
        for comment in all_comments:
            idx = comment["idx"]
            comment_counts[idx] = comment_counts.get(idx, 0) + 1

        # 新增 Number of comment 欄位
        df["Number of comment"] = df["idx"].apply(lambda x: comment_counts.get(x, 0))


        if search_term:
            mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            df = df[mask]

        filtered_df = df.head(50)  # 限制為前 50 行
        display_df = filtered_df[original_columns + ["Number of comment"]].copy()
        display_df.columns = display_headers

        return display_df, filtered_df, search_term

    def update_details(evt: gr.SelectData, table_data, username):
        if evt.index is None:
            return (
                ["", "", "", "", "Please select a row from the table to display the dialogue.", "Please select a row from the table to display the report.", "", 0, "", None, pd.DataFrame(columns=comment_headers), "", "", "", "", ""]
            )

        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(table_data, columns=display_headers)
        current_table.columns = original_columns + ["Number of comment"]
        if idx >= len(current_table):
            return (
                ["", "", "", "", "Out of range", "Out of range", "", 0, "", None, pd.DataFrame(columns=comment_headers), "", "", "", "", ""]
            )

        selected_idx = current_table.iloc[idx]['idx']
        row = get_line_by_idx(selected_idx)

        # 獲取該 idx 的所有評論
        comments = get_comments_by_idx(selected_idx)
        comments_df = pd.DataFrame(comments, columns=comment_columns)
        comments_df.columns = comment_headers

        # 獲取當前使用者的最新評論（如果有）
        user_comments = [c for c in comments if c["user_name"] == username]
        user_comment = max(user_comments, key=lambda x: x["comment_time"], default={})

        return [
            row.get("idx", ""),
            row.get("object_name", ""),
            row.get("object_type", ""),
            row.get("upload_time", ""),
            row.get("dialogue_content", ""),
            row.get("report_content", ""),
            user_comment.get("comment_time", ""),
            user_comment.get("comment_score", 0),
            user_comment.get("comment_content", ""),
            selected_idx,
            comments_df,
            "", "", "", "", ""  # 初始化評論詳細資訊
        ]

    def refresh_table(search_term, selected_idx, username):
        updated_display_df, filtered_df, search_term = get_display_df(search_term)

        if not selected_idx or selected_idx.strip() == "":
            return (
                gr.update(value=updated_display_df, visible=True, interactive=False),
                filtered_df,
                search_term,
                gr.update(value="Please select a row from the table to display the dialogue.", visible=True),
                gr.update(value="Please select a row from the table to display the report.", visible=True),
                gr.update(value="", visible=True, interactive=True),
                gr.update(value=0, visible=True, interactive=True),
                gr.update(value="", visible=False),
                pd.DataFrame(columns=comment_headers),
                "", "", "", "", ""
            )

        row = get_line_by_idx(selected_idx)
        comments = get_comments_by_idx(selected_idx)
        comments_df = pd.DataFrame(comments, columns=comment_columns)
        comments_df.columns = comment_headers

        user_comments = [c for c in comments if c["user_name"] == username]
        user_comment = max(user_comments, key=lambda x: x["comment_time"], default={})

        return (
            gr.update(value=updated_display_df, visible=True, interactive=False),
            filtered_df,
            search_term,
            gr.update(value=row.get("dialogue_content", ""), visible=True),
            gr.update(value=row.get("report_content", ""), visible=True),
            gr.update(value=user_comment.get("comment_content", ""), visible=True, interactive=True),
            gr.update(value=user_comment.get("comment_score", 0), visible=True, interactive=True),
            gr.update(value="", visible=False),
            comments_df,
            "", "", "", "", ""
        )

    def save_comment_fn(comment_content, comment_score, selected_idx, search_term, username):
        try:
            if not selected_idx or selected_idx.strip() == "":
                return (
                    gr.update(), gr.update(value="⚠️ No row selected.", visible=True),
                    gr.update(), gr.update(), gr.update(), gr.update(value=""), gr.update(value=0),
                    gr.update(visible=True), pd.DataFrame(columns=comment_headers),
                    "", "", "", "", ""
                )

            taipei_tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            success = submit_comment(selected_idx, comment_content.strip(), comment_score, now, username)

            if not success:
                return (
                    gr.update(), gr.update(value="⚠️ Submission skipped: empty content or zero score", visible=True),
                    gr.update(), gr.update(), gr.update(value=""), gr.update(value=0),
                    gr.update(value="⚠️ Submission skipped: empty content or zero score", visible=True),
                    pd.DataFrame(columns=comment_headers),
                    "", "", "", "", ""
                )

            updated_display_df, filtered_df, search_term = get_display_df(search_term)
            comments = get_comments_by_idx(selected_idx)
            comments_df = pd.DataFrame(comments, columns=comment_columns)
            comments_df.columns = comment_headers

            return (
                gr.update(value=updated_display_df, visible=True, interactive=False),
                gr.update(value=now, visible=True, interactive=False),
                filtered_df,
                search_term,
                gr.update(value=comment_content, visible=True, interactive=True),
                gr.update(value=comment_score, visible=True, interactive=True),
                gr.update(value="", visible=False),
                comments_df,
                "", "", "", "", ""
            )
        except Exception as e:
            print(f"Error in save_comment_fn: {e}")
            return (
                gr.update(), gr.update(value=f"⚠️ Submission failed: {str(e)}", visible=True),
                gr.update(), gr.update(),
                gr.update(value=""), gr.update(value=0),
                gr.update(value=f"⚠️ Submission failed: {str(e)}", visible=True),
                pd.DataFrame(columns=comment_headers),
                "", "", "", "", ""
            )

    def update_comment_details(evt: gr.SelectData, comments_data):
        if evt.index is None:
            return ["", "", "", "", ""]

        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(comments_data, columns=comment_headers)
        if idx >= len(current_table):
            return ["", "", "", "", "Out of range"]

        row = current_table.iloc[idx]
        return [
            row["IDX"],
            row["Comment time"],
            row["User"],
            row["Comment content"],  # 修正：從 "Comment" 改為 "Comment content"
            str(row["Score"])
        ]

    with gr.Blocks() as demo:

        filtered_df_state = gr.State()
        search_term_state = gr.State("")
        selected_idx_hidden = gr.Textbox(visible=False)

        search_input = gr.Textbox(label="🔍 Search", placeholder="Enter keyword to filter table...")

        gr.Markdown("## 📂 Line, Dialogue & Report Table")
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Table")
        table = gr.Dataframe(
            interactive=False,
            label="Line, Dialogue & Report Table",
            show_label=False,
            row_count=(1, "dynamic"),
            elem_classes="table-scroll"
        )

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 👤 Information")
                with gr.Row():
                    idx_box = gr.Textbox(label="IDX", interactive=False)
                    user_name = gr.Textbox(label="Name", interactive=False)
                    user_type = gr.Textbox(label="Type", interactive=False)
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
                comment_score = gr.Slider(minimum=0, maximum=5, step=1, label="Comment Score", visible=True)
                comment_box = gr.Textbox(label="Comment Content", lines=10, placeholder="Type any comments here...", elem_classes="scrollable", visible=True)
                lock_message = gr.Textbox(label="Lock Status", interactive=False, visible=False)
                submit_btn = gr.Button("Submit Comment ✅")

                gr.Markdown("## 📜 Comment Table for this IDX")
                comments_table = gr.Dataframe(
                    label="Comments",
                    show_label=False,
                    headers=comment_headers,
                    interactive=False,
                    row_count=(1, "dynamic"),
                    elem_classes="table-scroll"
                )

                gr.Markdown("## 📙 Comment Detail")
                with gr.Row():
                    comment_idx_box = gr.Textbox(label="IDX", interactive=False)
                    comment_time_box = gr.Textbox(label="Comment Time", interactive=False)
                    comment_user_box = gr.Textbox(label="User", interactive=False)
                    comment_score_box = gr.Textbox(label="Score", interactive=False)
                with gr.Row():
                    comment_content_box = gr.Textbox(label="Comment Content", lines=10, placeholder="Click a row to view its comment.", interactive=False)
                with gr.Row():
                    copy_comment_btn = gr.Button("Copy Comment", elem_id="comment_content")

        demo.load(
            fn=lambda: list(get_display_df("")) + [None],
            inputs=[],
            outputs=[table, filtered_df_state, search_term_state, selected_idx_hidden],
            queue=False
        )

        search_input.change(
            get_display_df,
            inputs=[search_input],
            outputs=[table, filtered_df_state, search_term_state],
            queue=False
        )

        table.select(
            fn=update_details,
            inputs=[table, username_state],
            outputs=[
                idx_box, user_name, user_type, upload_time,
                dialogue_box, report_box, comment_time, comment_score,
                comment_box, selected_idx_hidden, comments_table,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
            ],
            queue=False
        )

        submit_btn.click(
            fn=lambda comment_content, comment_score, selected_idx, search_term, username: save_comment_fn(comment_content, comment_score, selected_idx, search_term, username),
            inputs=[comment_box, comment_score, selected_idx_hidden, search_term_state, username_state],
            outputs=[
                table, comment_time, filtered_df_state, search_term_state,
                comment_box, comment_score, lock_message, comments_table,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
            ],
            queue=False
        )

        refresh_btn.click(
            fn=lambda search_term, selected_idx, username: refresh_table(search_term, selected_idx, username),
            inputs=[search_term_state, selected_idx_hidden, username_state],
            outputs=[
                table, filtered_df_state, search_term_state,
                dialogue_box, report_box, comment_box, comment_score,
                lock_message, comments_table,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
            ],
            queue=False
        )

        comments_table.select(
            fn=update_comment_details,
            inputs=[comments_table],
            outputs=[
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
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

        copy_comment_btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                const content = document.getElementById('comment_content')?.innerText.trim();
                if (content=="Click a row to view its comment.") {
                    alert("Please select a row from the table to display the comment.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Comment copied successfully!");
            }
            """
        )

    return demo