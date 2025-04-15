from datetime import datetime
import pandas as pd
import pytz
import gradio as gr
from database.LineComment2db import get_line_list, get_line_by_idx, get_comments_by_idx, submit_comment, line_comment_coll

def line_comment_page(username_state):
    print(f"Initializing line_comment_page with username_state: {username_state}")
    display_headers = ["IDX", "Upload time", "Name", "Type", "Number of comment"]
    original_columns = ["idx", "upload_time", "object_name", "object_type"]
    comment_headers = ["IDX", "Comment time", "User", "Comment content", "Score"]
    comment_columns = ["idx", "comment_time", "user_name", "comment_content", "comment_score"]

    def get_statistics():
        data = get_line_list()
        total_records = len(data)
        doctor_count = sum(1 for item in data if item.get("object_type") == "Doctor")
        patient_count = sum(1 for item in data if item.get("object_type") == "Patient")
        doctor_ratio = (doctor_count / total_records * 100) if total_records > 0 else 0
        patient_ratio = (patient_count / total_records * 100) if total_records > 0 else 0
        records_text = total_records
        type_text = (
            f"Doctor: {doctor_count} ({doctor_ratio:.2f}%)\n"
            f"Patient: {patient_count} ({patient_ratio:.2f}%)"
        )
        return records_text, type_text

    def get_display_df(search_term=""):
        print(f"Fetching display dataframe with search_term: {search_term}")
        data = get_line_list()
        df = pd.DataFrame(data)
        for col in original_columns:
            if col not in df.columns:
                df[col] = ""
        df = df.fillna("")
        comment_counts = {}
        all_comments = list(line_comment_coll.find({}, {"idx": 1, "_id": 0}))
        for comment in all_comments:
            idx = comment["idx"]
            comment_counts[idx] = comment_counts.get(idx, 0) + 1
        df["Number of comment"] = df["idx"].apply(lambda x: comment_counts.get(x, 0))
        if search_term:
            mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            df = df[mask]
        filtered_df = df.sort_values(by="upload_time", ascending=False).head(100)
        display_df = filtered_df[original_columns + ["Number of comment"]].copy()
        display_df.columns = display_headers
        records_text, type_text = get_statistics()
        return display_df, filtered_df, search_term, records_text, type_text

    def update_details(evt: gr.SelectData, table_data, username):
        print(f"update_details called with username: {username}, evt.index: {evt.index}")
        if evt.index is None:
            print("No row selected in table")
            return [
                "", "", "", "", "Please select a row from the table to display the dialogue.",
                "Please select a row from the table to display the report.", "", 0, "", "",
                pd.DataFrame(columns=comment_headers), 0, "", "", "", "", ""
            ]
        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(table_data, columns=display_headers)
        current_table.columns = original_columns + ["Number of comment"]
        if idx >= len(current_table):
            print(f"Index {idx} out of range, table length: {len(current_table)}")
            return [
                "", "", "", "", "Out of range", "Out of range", "", 0, "", "",
                pd.DataFrame(columns=comment_headers), 0, "", "", "", "", ""
            ]
        selected_idx = current_table.iloc[idx]['idx']
        print(f"Selected idx: {selected_idx}")
        row = get_line_by_idx(selected_idx)
        comments = get_comments_by_idx(selected_idx)
        comments_df = pd.DataFrame(comments, columns=comment_columns)
        comments_df = comments_df.fillna({"user_name": "Unknown"})
        comments_df.columns = comment_headers
        number_of_comments = len(comments_df)
        user_comments = [c for c in comments if c.get("user_name") == username]
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
            number_of_comments,
            "", "", "", "", ""
        ]

    def refresh_table(search_term, selected_idx, username):
        print(f"refresh_table called with username: {username}, selected_idx: {selected_idx}")
        updated_display_df, filtered_df, search_term, records_text, type_text = get_display_df(search_term)
        if not selected_idx or selected_idx.strip() == "":
            print("No selected_idx in refresh_table")
            return (
                gr.update(value=updated_display_df, visible=True, interactive=False),
                filtered_df,
                search_term,
                gr.update(value=records_text, visible=True),
                gr.update(value=type_text, visible=True),
                gr.update(value="Please select a row from the table to display the dialogue.", visible=True),
                gr.update(value="Please select a row from the table to display the report.", visible=True),
                gr.update(value="", visible=True, interactive=True),
                gr.update(value=0, visible=True, interactive=True),
                gr.update(value="", visible=False),
                pd.DataFrame(columns=comment_headers),
                0,
                "", "", "", "", ""
            )
        row = get_line_by_idx(selected_idx)
        comments = get_comments_by_idx(selected_idx)
        comments_df = pd.DataFrame(comments, columns=comment_columns)
        comments_df = comments_df.fillna({"user_name": "Unknown"})
        comments_df.columns = comment_headers
        number_of_comments = len(comments_df)
        user_comments = [c for c in comments if c.get("user_name") == username]
        user_comment = max(user_comments, key=lambda x: x["comment_time"], default={})
        return (
            gr.update(value=updated_display_df, visible=True, interactive=False),
            filtered_df,
            search_term,
            gr.update(value=records_text, visible=True),
            gr.update(value=type_text, visible=True),
            gr.update(value=row.get("dialogue_content", ""), visible=True),
            gr.update(value=row.get("report_content", ""), visible=True),
            gr.update(value=user_comment.get("comment_content", ""), visible=True, interactive=True),
            gr.update(value=user_comment.get("comment_score", 0), visible=True, interactive=True),
            gr.update(value="", visible=False),
            comments_df,
            number_of_comments,
            "", "", "", "", ""
        )

    def save_comment_fn(comment_content, comment_score, selected_idx, search_term, username):
        print(f"save_comment_fn called with username: {username}, selected_idx: {selected_idx}, comment_content: {comment_content}, comment_score: {comment_score}")
        try:
            if not selected_idx or selected_idx.strip() == "":
                print("No row selected for comment submission")
                return (
                    gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "⚠️ No row selected.", pd.DataFrame(columns=comment_headers),
                    0, "", "", "", "", ""
                )
            if not username:
                print("No valid username provided, submission blocked")
                return (
                    gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "⚠️ Please log in to submit a comment.", pd.DataFrame(columns=comment_headers),
                    0, "", "", "", "", ""
                )
            if not comment_content or comment_content.strip() == "":
                print("No comment content provided")
                return (
                    gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "⚠️ Comment content cannot be empty.", pd.DataFrame(columns=comment_headers),
                    0, "", "", "", "", ""
                )
            if comment_score is None or comment_score < 0 or comment_score > 5:
                print("Invalid comment score")
                return (
                    gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "⚠️ Comment score must be between 0 and 5.", pd.DataFrame(columns=comment_headers),
                    0, "", "", "", "", ""
                )
            taipei_tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            success = submit_comment(selected_idx, comment_content.strip(), comment_score, now, username)
            if not success:
                print("Comment submission failed: empty content or zero score")
                return (
                    gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "⚠️ Submission skipped: empty content or zero score", pd.DataFrame(columns=comment_headers),
                    0, "", "", "", "", ""
                )
            updated_display_df, filtered_df, search_term, records_text, type_text = get_display_df(search_term)
            comments = get_comments_by_idx(selected_idx)
            comments_df = pd.DataFrame(comments, columns=comment_columns)
            comments_df = comments_df.fillna({"user_name": "Unknown"})
            comments_df.columns = comment_headers
            number_of_comments = len(comments_df)
            print(f"Comment submitted successfully for idx: {selected_idx}, username: {username}")
            return (
                updated_display_df, now, filtered_df, search_term, records_text, type_text,
                comment_content, comment_score, "", comments_df,
                number_of_comments, "", "", "", "", ""
            )
        except Exception as e:
            print(f"Error in save_comment_fn: {e}")
            return (
                gr.update(), "", gr.State(), search_term, gr.update(), gr.update(),
                "", 0, f"⚠️ Submission failed: {str(e)}", pd.DataFrame(columns=comment_headers),
                0, "", "", "", "", ""
            )

    def update_comment_details(evt: gr.SelectData, comments_data):
        print("update_comment_details called")
        if evt.index is None:
            return ["", "", "", "", ""]
        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(comments_data, columns=comment_headers)
        if idx >= len(current_table):
            return ["", "", "", "", "Out of range"]
        row = current_table.iloc[idx]
        print(f"Selected comment: {row.to_dict()}")
        return [
            row["IDX"],
            row["Comment time"],
            row["User"],
            row["Comment content"],
            str(row["Score"])
        ]

    def update_username_hidden(username):
        print(f"Updating username_hidden to: {username}")
        return username

    def update_selected_idx_hidden(selected_idx):
        print(f"Updating selected_idx_hidden to: {selected_idx}")
        return selected_idx

    with gr.Blocks() as demo:
        filtered_df_state = gr.State()
        search_term_state = gr.State("")
        username_hidden = gr.Textbox(value="", visible=False)
        selected_idx_hidden = gr.Textbox(value="", visible=False)

        search_input = gr.Textbox(label="🔍 Search", placeholder="Enter keyword to filter table...")

        gr.Markdown("## 📂 Line, Dialogue & Report Table")
        with gr.Row():
            number_of_records = gr.Textbox(label="Number of records", interactive=False)
            number_of_type = gr.Textbox(label="Number of types", interactive=False, lines=2)
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
                comment_score = gr.Slider(minimum=0, maximum=5, step=1, label="Comment Score", value=0, visible=True)
                comment_box = gr.Textbox(label="Comment Content", lines=10, placeholder="Type any comments here...", value="", elem_classes="scrollable", visible=True)
                lock_message = gr.Textbox(label="Lock Status", interactive=False, visible=False)
                submit_btn = gr.Button("Submit Comment ✅")

                gr.Markdown("## 📜 Comment Table for this IDX")
                number_of_comment = gr.Textbox(label="Number of comments", interactive=False, value=0)
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
                    comment_content_box = gr.Textbox(label="Comment Content", lines=10, placeholder="Click a row to view its comment.", elem_id="comment_content_box_id", interactive=False)
                with gr.Row():
                    copy_comment_btn = gr.Button("Copy Comment")

        demo.load(
            fn=lambda: list(get_display_df("")) + [username_state.value if hasattr(username_state, 'value') else "", ""],
            inputs=[],
            outputs=[table, filtered_df_state, search_term_state, number_of_records, number_of_type, username_hidden, selected_idx_hidden],
            queue=False
        )

        search_input.change(
            get_display_df,
            inputs=[search_input],
            outputs=[table, filtered_df_state, search_term_state, number_of_records, number_of_type],
            queue=False
        )

        def handle_table_select(evt: gr.SelectData, table_data, username):
            details = update_details(evt, table_data, username)
            username_updated = update_username_hidden(username)
            selected_idx_updated = update_selected_idx_hidden(details[9])  # details[9] 是 selected_idx
            return details + [username_updated, selected_idx_updated]

        table.select(
            fn=handle_table_select,
            inputs=[table, username_state],
            outputs=[
                idx_box, user_name, user_type, upload_time,
                dialogue_box, report_box, comment_time, comment_score,
                comment_box, selected_idx_hidden, comments_table,
                number_of_comment,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box,
                username_hidden, selected_idx_hidden
            ],
            queue=True
        )

        submit_btn.click(
            fn=lambda comment_content, comment_score, selected_idx, search_term, username: (
                print(f"submit_btn.click triggered with username: {username}, selected_idx: {selected_idx}, comment_content: {comment_content}, comment_score: {comment_score}"),
                save_comment_fn(comment_content, comment_score, selected_idx, search_term, username)
            )[1],
            inputs=[comment_box, comment_score, selected_idx_hidden, search_term_state, username_hidden],
            outputs=[
                table, comment_time, filtered_df_state, search_term_state,
                number_of_records, number_of_type,
                comment_box, comment_score, lock_message, comments_table,
                number_of_comment,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
            ],
            queue=True,
            preprocess=True,
            js="""
            (comment_content, comment_score, selected_idx, search_term, username) => {
                try {
                    if (!username || username === "None") {
                        alert("Please log in to submit a comment.");
                        return null;
                    }

                    if (!selected_idx || selected_idx === "None") {
                        alert("Please select a row from the table before submitting a comment.");
                        return null;
                    }

                    if (!comment_content || comment_content.trim() === "") {
                        alert("Please enter a comment before submitting.");
                        return undefined;
                    }

                    if (comment_score === null || comment_score === undefined || isNaN(comment_score)) {
                        alert("Please provide a score before submitting.");
                        return null;
                    }

                    if (comment_score < 0 || comment_score > 5) {
                        alert("Score must be between 0 and 5.");
                        return null;
                    }

                    const dialogueContent = document.getElementById('dialogue-md')?.innerText.trim();
                    if (dialogueContent === "Click a row to view its dialogue.") {
                        alert("Please select a row to view its dialogue before commenting.");
                        return null;
                    }

                    return [comment_content, comment_score, selected_idx, search_term, username];
                } catch (e) {
                    alert("Error during comment validation: " + e.message);
                    return null;
                }
            } 
            """
        )

        refresh_btn.click(
            fn=refresh_table,
            inputs=[search_term_state, selected_idx_hidden, username_hidden],
            outputs=[
                table, filtered_df_state, search_term_state,
                number_of_records, number_of_type,
                dialogue_box, report_box, comment_box, comment_score,
                lock_message, comments_table,
                number_of_comment,
                comment_idx_box, comment_time_box, comment_user_box, comment_content_box, comment_score_box
            ],
            queue=True
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
                if (content === "Click a row to view its dialogue.") {
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
                if (content === "Click a row to view its report.") {
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
                const element = document.querySelector('[data-testid="textbox"][placeholder="Click a row to view its comment."]');
                if (!element) {
                    console.error("Textarea element not found.");
                    alert("Error: Comment content box not found.");
                    return;
                }
                const content = (element.value || "").trim();
                if (content === "" || content === "Click a row to view its comment.") {
                    alert("Please select a row from the table to display the comment.");
                    return;
                }
                navigator.clipboard.writeText(content);
                alert("✅ Comment copied successfully!");
            }
            """
        )

    return demo