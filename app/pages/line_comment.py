# line_comment.py
from datetime import datetime
import pandas as pd
import pytz
import gradio as gr
from database.LineComment2db import get_line_list, get_line_by_idx, get_dialogue_comments_by_idx, get_report_comments_by_idx, submit_dialogue_comment, submit_report_comment

def line_comment_page(username_state):
    # print(f"Initializing line_comment_page with username_state: {username_state}")
    display_headers = ["Upload time", "Name", "Type", "Last Dialogue Comment User", "Last Report Comment User", "IDX"]
    original_columns = ["upload_time", "object_name", "object_type", "idx"]
    dialogue_comment_headers = ["Comment time", "User", "Dialogue comment content", "Score"]
    dialogue_comment_columns = ["dialogue_comment_time", "user_name", "dialogue_comment_content", "dialogue_comment_score"]
    report_comment_headers = ["Comment time", "User", "Report comment content", "Score"]
    report_comment_columns = ["report_comment_time", "user_name", "report_comment_content", "report_comment_score"]

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
        # print(f"Fetching display dataframe with search_term: {search_term}")
        data = get_line_list()
        df = pd.DataFrame(data)
        for col in original_columns:
            if col not in df.columns:
                df[col] = ""
        df = df.fillna("")
        df["idx"] = df["idx"].astype(str)
        if search_term:
            mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
            df = df[mask]
        filtered_df = df.sort_values(by="upload_time", ascending=False).head(100)

        def get_last_dialogue_comment_username(idx):
            dialogue_comments = list(get_dialogue_comments_by_idx(idx))
            if not dialogue_comments:
                return "No comments yet"
            latest_comment = max(dialogue_comments, key=lambda x: x["dialogue_comment_time"], default={})
            return latest_comment.get("user_name", "No comments yet")

        def get_last_report_comment_username(idx):
            report_comments = list(get_report_comments_by_idx(idx))
            if not report_comments:
                return "No comments yet"
            latest_comment = max(report_comments, key=lambda x: x["report_comment_time"], default={})
            return latest_comment.get("user_name", "尚未評論")

        filtered_df["Last Dialogue Comment User"] = filtered_df["idx"].apply(get_last_dialogue_comment_username)
        filtered_df["Last  Report  Comment User"] = filtered_df["idx"].apply(get_last_report_comment_username)
        
        display_df = filtered_df[["upload_time", "object_name", "object_type", "Last Dialogue Comment User", "Last  Report  Comment User", "idx"]].copy()
        display_df.columns = display_headers
        records_text, type_text = get_statistics()
        return display_df, filtered_df, search_term, records_text, type_text

    def update_details(evt: gr.SelectData, table_data, username):
        # print(f"update_details called with username: {username}, evt.index: {evt.index}")
        if evt.index is None:
            print("No row selected in table")
            return [
                "", "", "", "", "Please select a row from the table to display the dialogue.",
                "Please select a row from the table to display the report.", 0, "", 0, "",
                pd.DataFrame(columns=dialogue_comment_headers), 0, pd.DataFrame(columns=report_comment_headers), 0,
                "", "", "", "", "", "", "", "", "", ""
            ]
        idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        current_table = pd.DataFrame(table_data, columns=display_headers)
        current_table.columns = ["upload_time", "object_name", "object_type", "Last Dialogue Comment User", "Last  Report  Comment User", "idx"]
        if idx >= len(current_table):
            # print(f"Index {idx} out of range, table length: {len(current_table)}")
            return [
                "", "", "", "", "Out of range", "Out of range", 0, "", 0, "",
                pd.DataFrame(columns=dialogue_comment_headers), 0, pd.DataFrame(columns=report_comment_headers), 0,
                "", "", "", "", "", "", "", "", "", ""
            ]
        selected_idx = current_table.iloc[idx]['idx']
        # print(f"Selected idx: {selected_idx}")
        row = get_line_by_idx(selected_idx)
        dialogue_comments = sorted(list(get_dialogue_comments_by_idx(selected_idx)), key=lambda x: x["dialogue_comment_time"], reverse=True)[:100]
        report_comments = sorted(list(get_report_comments_by_idx(selected_idx)), key=lambda x: x["report_comment_time"], reverse=True)[:100]
        # print(f"First dialogue comment: {dialogue_comments[0] if dialogue_comments else 'None'}")
        # print(f"First report comment: {report_comments[0] if report_comments else 'None'}")
        dialogue_comments_df = pd.DataFrame(dialogue_comments, columns=dialogue_comment_columns)
        dialogue_comments_df = dialogue_comments_df.fillna({"user_name": "Unknown"})
        dialogue_comments_df.columns = dialogue_comment_headers
        report_comments_df = pd.DataFrame(report_comments, columns=report_comment_columns)
        report_comments_df = report_comments_df.fillna({"user_name": "Unknown"})
        report_comments_df.columns = report_comment_headers
        dialogue_number_of_comments = len(dialogue_comments_df)
        report_number_of_comments = len(report_comments_df)
        user_dialogue_comments = [c for c in dialogue_comments if c.get("user_name") == username]
        user_report_comments = [c for c in report_comments if c.get("user_name") == username]
        user_dialogue_comment = max(user_dialogue_comments, key=lambda x: x["dialogue_comment_time"], default={})
        user_report_comment = max(user_report_comments, key=lambda x: x["report_comment_time"], default={})
        return [
            row.get("idx", ""),
            row.get("object_name", ""),
            row.get("object_type", ""),
            row.get("upload_time", ""),
            row.get("dialogue_content", ""),
            row.get("report_content", ""),
            user_dialogue_comment.get("dialogue_comment_score", 0),
            user_dialogue_comment.get("dialogue_comment_content", ""),
            user_report_comment.get("report_comment_score", 0),
            user_report_comment.get("report_comment_content", ""),
            dialogue_comments_df,
            dialogue_number_of_comments,
            report_comments_df,
            report_number_of_comments,
            "", "", "", "", "", "", "", "", "", ""
        ]

    def refresh_table(search_term, selected_idx, username):
        # print(f"refresh_table called with username: {username}, selected_idx: {selected_idx}")
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
                gr.update(value="", visible=True, interactive=True),
                gr.update(value=0, visible=True, interactive=True),
                gr.update(value="", visible=True),
                pd.DataFrame(columns=dialogue_comment_headers),
                0,
                pd.DataFrame(columns=report_comment_headers),
                0,
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="Click a row to view its dialogue comment.", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="Click a row to view its report comment.", visible=True),
                gr.update(value="", visible=True)
            )
        row = get_line_by_idx(selected_idx)
        dialogue_comments = sorted(list(get_dialogue_comments_by_idx(selected_idx)), key=lambda x: x["dialogue_comment_time"], reverse=True)[:100]
        report_comments = sorted(list(get_report_comments_by_idx(selected_idx)), key=lambda x: x["report_comment_time"], reverse=True)[:100]
        # print(f"First dialogue comment: {dialogue_comments[0] if dialogue_comments else 'None'}")
        # print(f"First report comment: {report_comments[0] if report_comments else 'None'}")
        dialogue_comments_df = pd.DataFrame(dialogue_comments, columns=dialogue_comment_columns)
        dialogue_comments_df = dialogue_comments_df.fillna({"user_name": "Unknown"})
        dialogue_comments_df.columns = dialogue_comment_headers
        report_comments_df = pd.DataFrame(report_comments, columns=report_comment_columns)
        report_comments_df = report_comments_df.fillna({"user_name": "Unknown"})
        report_comments_df.columns = report_comment_headers
        dialogue_number_of_comments = len(dialogue_comments_df)
        report_number_of_comments = len(report_comments_df)
        user_dialogue_comments = [c for c in dialogue_comments if c.get("user_name") == username]
        user_report_comments = [c for c in report_comments if c.get("user_name") == username]
        user_dialogue_comment = max(user_dialogue_comments, key=lambda x: x["dialogue_comment_time"], default={})
        user_report_comment = max(user_report_comments, key=lambda x: x["report_comment_time"], default={})
        return (
            gr.update(value=updated_display_df, visible=True, interactive=False),
            filtered_df,
            search_term,
            gr.update(value=records_text, visible=True),
            gr.update(value=type_text, visible=True),
            gr.update(value=row.get("dialogue_content", ""), visible=True),
            gr.update(value=row.get("report_content", ""), visible=True),
            gr.update(value=user_dialogue_comment.get("dialogue_comment_content", ""), visible=True, interactive=True),
            gr.update(value=user_dialogue_comment.get("dialogue_comment_score", 0), visible=True, interactive=True),
            gr.update(value=user_report_comment.get("report_comment_content", ""), visible=True, interactive=True),
            gr.update(value=user_report_comment.get("report_comment_score", 0), visible=True, interactive=True),
            gr.update(value="", visible=True),
            dialogue_comments_df,
            dialogue_number_of_comments,
            report_comments_df,
            report_number_of_comments,
            gr.update(value="", visible=True),
            gr.update(value="", visible=True),
            gr.update(value="", visible=True),
            gr.update(value="Click a row to view its dialogue comment.", visible=True),
            gr.update(value="", visible=True),
            gr.update(value="", visible=True),
            gr.update(value="", visible=True),
            gr.update(value="Click a row to view its report comment.", visible=True),
            gr.update(value="", visible=True)
        )

    def save_dialogue_comment_fn(dialogue_comment_content, dialogue_comment_score, selected_idx, search_term, username):
        # print(f"save_dialogue_comment_fn called with username: {username}, selected_idx: {selected_idx}, dialogue_comment_content: {dialogue_comment_content}, dialogue_comment_score: {dialogue_comment_score}")
        try:
            if not selected_idx or selected_idx.strip() == "":
                print("No row selected for dialogue comment submission")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ No row selected.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if not username:
                print("No valid username provided, dialogue comment submission blocked")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Please log in to submit a dialogue comment.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if not dialogue_comment_content or dialogue_comment_content.strip() == "":
                print("No dialogue comment content provided")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Dialogue comment content cannot be empty.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if dialogue_comment_score is None or dialogue_comment_score < 0 or dialogue_comment_score > 5:
                print("Invalid dialogue comment score")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Dialogue comment score must be between 0 and 5.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            taipei_tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            success = submit_dialogue_comment(selected_idx, dialogue_comment_content.strip(), dialogue_comment_score, now, username)
            message = "✅ Dialogue comment submitted successfully!" if success else "⚠️ Submission skipped: empty content or zero score"
            if not success:
                print("Dialogue comment submission failed: empty content or zero score")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, message, pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            updated_display_df, filtered_df, search_term, records_text, type_text = get_display_df(search_term)
            dialogue_comments = sorted(list(get_dialogue_comments_by_idx(selected_idx)), key=lambda x: x["dialogue_comment_time"], reverse=True)[:100]
            report_comments = sorted(list(get_report_comments_by_idx(selected_idx)), key=lambda x: x["report_comment_time"], reverse=True)[:100]
            # print(f"First dialogue comment: {dialogue_comments[0] if dialogue_comments else 'None'}")
            # print(f"First report comment: {report_comments[0] if report_comments else 'None'}")
            dialogue_comments_df = pd.DataFrame(dialogue_comments, columns=dialogue_comment_columns)
            dialogue_comments_df = dialogue_comments_df.fillna({"user_name": "Unknown"})
            dialogue_comments_df.columns = dialogue_comment_headers
            report_comments_df = pd.DataFrame(report_comments, columns=report_comment_columns)
            report_comments_df = report_comments_df.fillna({"user_name": "Unknown"})
            report_comments_df.columns = report_comment_headers
            dialogue_number_of_comments = len(dialogue_comments_df)
            report_number_of_comments = len(report_comments_df)
            user_dialogue_comments = [c for c in dialogue_comments if c.get("user_name") == username]
            user_report_comments = [c for c in report_comments if c.get("user_name") == username]
            user_dialogue_comment = max(user_dialogue_comments, key=lambda x: x["dialogue_comment_time"], default={})
            user_report_comment = max(user_report_comments, key=lambda x: x["report_comment_time"], default={})
            # print(f"Dialogue comment submitted successfully for idx: {selected_idx}, username: {username}")
            return (
                updated_display_df, filtered_df, search_term, records_text, type_text,
                user_dialogue_comment.get("dialogue_comment_content", ""),
                user_dialogue_comment.get("dialogue_comment_score", 0),
                user_report_comment.get("report_comment_content", ""),
                user_report_comment.get("report_comment_score", 0),
                message,
                dialogue_comments_df, dialogue_number_of_comments,
                report_comments_df, report_number_of_comments,
                "", "", "", "", "", "", "", "", "", username, selected_idx
            )
        except Exception as e:
            print(f"Error in save_dialogue_comment_fn: {e}")
            message = f"⚠️ Submission failed: {str(e)}"
            return (
                gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                "", 0, "", 0, message, pd.DataFrame(columns=dialogue_comment_headers),
                0, pd.DataFrame(columns=report_comment_headers), 0,
                "", "", "", "", "", "", "", "", "", username, selected_idx
            )

    def save_report_comment_fn(report_comment_content, report_comment_score, selected_idx, search_term, username):
        # print(f"save_report_comment_fn called with username: {username}, selected_idx: {selected_idx}, report_comment_content: {report_comment_content}, report_comment_score: {report_comment_score}")
        try:
            if not selected_idx or selected_idx.strip() == "":
                print("No row selected for report comment submission")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ No row selected.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if not username:
                print("No valid username provided, report comment submission blocked")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Please log in to submit a report comment.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if not report_comment_content or report_comment_content.strip() == "":
                print("No report comment content provided")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Report comment content cannot be empty.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            if report_comment_score is None or report_comment_score < 0 or report_comment_score > 5:
                print("Invalid report comment score")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, "⚠️ Report comment score must be between 0 and 5.", pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            taipei_tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            success = submit_report_comment(selected_idx, report_comment_content.strip(), report_comment_score, now, username)
            message = "✅ Report comment submitted successfully!" if success else "⚠️ Submission skipped: empty content or zero score"
            if not success:
                print("Report comment submission failed: empty content or zero score")
                return (
                    gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                    "", 0, "", 0, message, pd.DataFrame(columns=dialogue_comment_headers),
                    0, pd.DataFrame(columns=report_comment_headers), 0,
                    "", "", "", "", "", "", "", "", "", username, selected_idx
                )
            updated_display_df, filtered_df, search_term, records_text, type_text = get_display_df(search_term)
            dialogue_comments = sorted(list(get_dialogue_comments_by_idx(selected_idx)), key=lambda x: x["dialogue_comment_time"], reverse=True)[:100]
            report_comments = sorted(list(get_report_comments_by_idx(selected_idx)), key=lambda x: x["report_comment_time"], reverse=True)[:100]
            # print(f"First dialogue comment: {dialogue_comments[0] if dialogue_comments else 'None'}")
            # print(f"First report comment: {report_comments[0] if report_comments else 'None'}")
            dialogue_comments_df = pd.DataFrame(dialogue_comments, columns=dialogue_comment_columns)
            dialogue_comments_df = dialogue_comments_df.fillna({"user_name": "Unknown"})
            dialogue_comments_df.columns = dialogue_comment_headers
            report_comments_df = pd.DataFrame(report_comments, columns=report_comment_columns)
            report_comments_df = report_comments_df.fillna({"user_name": "Unknown"})
            report_comments_df.columns = report_comment_headers
            dialogue_number_of_comments = len(dialogue_comments_df)
            report_number_of_comments = len(report_comments_df)
            user_dialogue_comments = [c for c in dialogue_comments if c.get("user_name") == username]
            user_report_comments = [c for c in report_comments if c.get("user_name") == username]
            user_dialogue_comment = max(user_dialogue_comments, key=lambda x: x["dialogue_comment_time"], default={})
            user_report_comment = max(user_report_comments, key=lambda x: x["report_comment_time"], default={})
            # print(f"Report comment submitted successfully for idx: {selected_idx}, username: {username}")
            return (
                updated_display_df, filtered_df, search_term, records_text, type_text,
                user_dialogue_comment.get("dialogue_comment_content", ""),
                user_dialogue_comment.get("dialogue_comment_score", 0),
                user_report_comment.get("report_comment_content", ""),
                user_report_comment.get("report_comment_score", 0),
                message,
                dialogue_comments_df, dialogue_number_of_comments,
                report_comments_df, report_number_of_comments,
                "", "", "", "", "", "", "", "", "", username, selected_idx
            )
        except Exception as e:
            print(f"Error in save_report_comment_fn: {e}")
            message = f"⚠️ Submission failed: {str(e)}"
            return (
                gr.update(), gr.State(), search_term, gr.update(), gr.update(),
                "", 0, "", 0, message, pd.DataFrame(columns=dialogue_comment_headers),
                0, pd.DataFrame(columns=report_comment_headers), 0,
                "", "", "", "", "", "", "", "", "", username, selected_idx
            )

    def update_username_hidden(username):
        # print(f"Updating username_hidden to: {username}")
        return username

    def update_selected_idx_hidden(selected_idx):
        # print(f"Updating selected_idx_hidden to: {selected_idx}")
        return selected_idx

    def select_dialogue_comment(evt: gr.SelectData, table_data):
        # print(f"select_dialogue_comment called with evt.index: {evt.index}")
        if evt.index is None or not isinstance(evt.index, (list, tuple)) or evt.index[0] >= len(table_data):
            return (
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="Click a row to view its dialogue comment.", visible=True)
            )
        row_idx = evt.index[0]
        return (
            gr.update(value=table_data.iloc[row_idx]["Comment time"] if row_idx < len(table_data) else "", visible=True),
            gr.update(value=table_data.iloc[row_idx]["User"] if row_idx < len(table_data) else "", visible=True),
            gr.update(value=str(table_data.iloc[row_idx]["Score"]) if row_idx < len(table_data) else "", visible=True),
            gr.update(value=table_data.iloc[row_idx]["Dialogue comment content"] or "無評論內容", visible=True)
        )

    def select_report_comment(evt: gr.SelectData, table_data):
        # print(f"select_report_comment called with evt.index: {evt.index}")
        if evt.index is None or not isinstance(evt.index, (list, tuple)) or evt.index[0] >= len(table_data):
            return (
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="", visible=True),
                gr.update(value="Click a row to view its report comment.", visible=True)
            )
        row_idx = evt.index[0]
        return (
            gr.update(value=table_data.iloc[row_idx]["Comment time"] if row_idx < len(table_data) else "", visible=True),
            gr.update(value=table_data.iloc[row_idx]["User"] if row_idx < len(table_data) else "", visible=True),
            gr.update(value=str(table_data.iloc[row_idx]["Score"]) if row_idx < len(table_data) else "", visible=True),
            gr.update(value=table_data.iloc[row_idx]["Report comment content"] or "無評論內容", visible=True)
        )

    with gr.Blocks(css=".go-to-top { position: fixed; bottom: 20px; right: 20px; z-index: 1000; background-color: #007bff; color: white; border-radius: 5px; }") as demo:
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
            headers=display_headers,
            row_count=(1, "dynamic"),
            elem_classes="table-scroll"
        )

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 👤 Information")
                with gr.Row():
                    upload_time = gr.Textbox(label="Upload Time", interactive=False)
                    user_name = gr.Textbox(label="Name", interactive=False)
                    user_type = gr.Textbox(label="Type", interactive=False)  
                    idx_box = gr.Textbox(label="IDX", interactive=False)

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 💬 Dialogue")
                dialogue_box = gr.Markdown("Click a row to view its dialogue.", elem_classes="scrollable report-content", elem_id="dialogue-md")
                copy_dialogue_btn = gr.Button("Copy Dialogue")
            
            with gr.Column():
                gr.Markdown("## 📢 Dialogue Comment")
                dialogue_comment_score = gr.Slider(minimum=0, maximum=5, step=1, label="Dialogue Comment Score", value=0, visible=True)
                dialogue_comment_box = gr.Textbox(label="Dialogue Comment Content", lines=10, placeholder="Type your dialogue comment here...", value="", elem_classes="scrollable", visible=True)
                dialogue_submit_message = gr.Textbox(label="Submission Status", interactive=False, visible=True)
                dialogue_submit_btn = gr.Button("Submit Dialogue Comment ✅")

                gr.Markdown("## 📜 Dialogue Comment Table for this IDX")
                dialogue_number_of_comments = gr.Textbox(label="# Dialogue comments", interactive=False, value=0)
                dialogue_comments_table = gr.Dataframe(
                    label="Dialogue Comments",
                    show_label=False,
                    headers=dialogue_comment_headers,
                    interactive=False,
                    row_count=(1, "dynamic"),
                    elem_classes="table-scroll"
                )
                with gr.Row():    
                    dialogue_comment_time_box = gr.Textbox(label="Dialogue comment time", interactive=False)
                    dialogue_comment_user_box = gr.Textbox(label="User", interactive=False)
                    dialogue_comment_score_box = gr.Textbox(label="Score", interactive=False)
                with gr.Row():
                    dialogue_comment_content_box = gr.Textbox(label="Dialogue comment content", lines=10, placeholder="Click a row to view its dialogue comment.", interactive=False)

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📝 Report")
                report_box = gr.Markdown("Click a row to view its report.", elem_classes="scrollable report-content", elem_id="report-md")
                copy_report_btn = gr.Button("Copy Report")
            
            with gr.Column():
                gr.Markdown("## 📢 Report Comment")
                report_comment_score = gr.Slider(minimum=0, maximum=5, step=1, label="Report Comment Score", value=0, visible=True)
                report_comment_box = gr.Textbox(label="Report Comment Content", lines=10, placeholder="Type your report comment here...", value="", elem_classes="scrollable", visible=True)
                report_submit_message = gr.Textbox(label="Submission Status", interactive=False, visible=True)
                report_submit_btn = gr.Button("Submit Report Comment ✅")

                gr.Markdown("## 📜 Report Comment Table for this IDX")
                report_number_of_comments = gr.Textbox(label="Number of report comments", interactive=False, value=0)
                report_comments_table = gr.Dataframe(
                    label="Report Comments",
                    show_label=False,
                    headers=report_comment_headers,
                    interactive=False,
                    row_count=(1, "dynamic"),
                    elem_classes="table-scroll"
                )
                with gr.Row():    
                    report_comment_time_box = gr.Textbox(label="Report comment time", interactive=False)
                    report_comment_user_box = gr.Textbox(label="User", interactive=False)
                    report_comment_score_box = gr.Textbox(label="Score", interactive=False)
                with gr.Row():
                    report_comment_content_box = gr.Textbox(label="Report comment content", lines=10, placeholder="Click a row to view its report comment.", interactive=False)

        go_to_top_btn = gr.Button("⬆ Go to Top", elem_classes="go-to-top")

        demo.load(
            fn=lambda: list(get_display_df("")) + [username_state.value if hasattr(username_state, 'value') else ""],
            inputs=[],
            outputs=[table, filtered_df_state, search_term_state, number_of_records, number_of_type, username_hidden],
            queue=False
        )

        search_input.change(
            fn=get_display_df,
            inputs=[search_input],
            outputs=[table, filtered_df_state, search_term_state, number_of_records, number_of_type],
            queue=False
        )

        def handle_table_select(evt: gr.SelectData, table_data, username):
            details = update_details(evt, table_data, username)
            username_updated = update_username_hidden(username)
            selected_idx_updated = update_selected_idx_hidden(details[0])
            return details + [username_updated, selected_idx_updated]

        table.select(
            fn=handle_table_select,
            inputs=[table, username_state],
            outputs=[
                idx_box, user_name, user_type, upload_time,
                dialogue_box, report_box,
                dialogue_comment_score, dialogue_comment_box,
                report_comment_score, report_comment_box,
                dialogue_comments_table, dialogue_number_of_comments,
                report_comments_table, report_number_of_comments,
                dialogue_comment_time_box, dialogue_comment_user_box, dialogue_comment_score_box, dialogue_comment_content_box,
                report_comment_time_box, report_comment_user_box, report_comment_score_box, report_comment_content_box,
                dialogue_submit_message, report_submit_message,
                username_hidden, selected_idx_hidden
            ],
            queue=True
        )

        dialogue_comments_table.select(
            fn=select_dialogue_comment,
            inputs=[dialogue_comments_table],
            outputs=[
                dialogue_comment_time_box, dialogue_comment_user_box, dialogue_comment_score_box, dialogue_comment_content_box
            ],
            queue=True
        )

        report_comments_table.select(
            fn=select_report_comment,
            inputs=[report_comments_table],
            outputs=[
                report_comment_time_box, report_comment_user_box, report_comment_score_box, report_comment_content_box
            ],
            queue=True
        )

        dialogue_submit_btn.click(
            fn=lambda dialogue_comment_content, dialogue_comment_score, selected_idx, search_term, username: (
                save_dialogue_comment_fn(dialogue_comment_content, dialogue_comment_score, selected_idx, search_term, username)
            ),
            inputs=[dialogue_comment_box, dialogue_comment_score, selected_idx_hidden, search_term_state, username_hidden],
            outputs=[
                table, filtered_df_state, search_term_state,
                number_of_records, number_of_type,
                dialogue_comment_box, dialogue_comment_score,
                report_comment_box, report_comment_score,
                dialogue_submit_message,
                dialogue_comments_table, dialogue_number_of_comments,
                report_comments_table, report_number_of_comments,
                dialogue_comment_time_box, dialogue_comment_user_box, dialogue_comment_score_box, dialogue_comment_content_box,
                report_comment_time_box, report_comment_user_box, report_comment_score_box, report_comment_content_box,
                report_submit_message,
                username_hidden, selected_idx_hidden
            ],
            queue=True,
            preprocess=True,
            js="""
            (dialogue_comment_content, dialogue_comment_score, selected_idx, search_term, username) => {
                try {
                    if (!username || username === "None") {
                        alert("Please log in to submit a dialogue comment.");
                        return null;
                    }
                    if (!selected_idx || selected_idx === "None") {
                        alert("Please select a row from the table before submitting a dialogue comment.");
                        return null;
                    }
                    if (!dialogue_comment_content || dialogue_comment_content.trim() === "") {
                        alert("Please enter a dialogue comment before submitting.");
                        return null;
                    }
                    if (dialogue_comment_score === null || dialogue_comment_score === undefined || isNaN(dialogue_comment_score)) {
                        alert("Please provide a dialogue comment score before submitting.");
                        return null;
                    }
                    if (dialogue_comment_score < 0 || dialogue_comment_score > 5) {
                        alert("Dialogue comment score must be between 0 and 5.");
                        return null;
                    }
                    const dialogueContent = document.getElementById('dialogue-md')?.innerText.trim();
                    if (dialogueContent === "Click a row to view its dialogue.") {
                        alert("Please select a row to view its dialogue before commenting.");
                        return null;
                    }
                    return [dialogue_comment_content, dialogue_comment_score, selected_idx, search_term, username];
                } catch (e) {
                    alert("Error during dialogue comment validation: " + e.message);
                    return null;
                }
            }
            """
        )

        report_submit_btn.click(
            fn=lambda report_comment_content, report_comment_score, selected_idx, search_term, username: (
                save_report_comment_fn(report_comment_content, report_comment_score, selected_idx, search_term, username)
            ),
            inputs=[report_comment_box, report_comment_score, selected_idx_hidden, search_term_state, username_hidden],
            outputs=[
                table, filtered_df_state, search_term_state,
                number_of_records, number_of_type,
                dialogue_comment_box, dialogue_comment_score,
                report_comment_box, report_comment_score,
                report_submit_message,
                dialogue_comments_table, dialogue_number_of_comments,
                report_comments_table, report_number_of_comments,
                dialogue_comment_time_box, dialogue_comment_user_box, dialogue_comment_score_box, dialogue_comment_content_box,
                report_comment_time_box, report_comment_user_box, report_comment_score_box, report_comment_content_box,
                dialogue_submit_message,
                username_hidden, selected_idx_hidden
            ],
            queue=True,
            preprocess=True,
            js="""
            (report_comment_content, report_comment_score, selected_idx, search_term, username) => {
                try {
                    if (!username || username === "None") {
                        alert("Please log in to submit a report comment.");
                        return null;
                    }
                    if (!selected_idx || selected_idx === "None") {
                        alert("Please select a row from the table before submitting a report comment.");
                        return null;
                    }
                    if (!report_comment_content || report_comment_content.trim() === "") {
                        alert("Please enter a report comment before submitting.");
                        return null;
                    }
                    if (report_comment_score === null || report_comment_score === undefined || isNaN(report_comment_score)) {
                        alert("Please provide a report comment score before submitting.");
                        return null;
                    }
                    if (report_comment_score < 0 || report_comment_score > 5) {
                        alert("Report comment score must be between 0 and 5.");
                        return null;
                    }
                    const reportContent = document.getElementById('report-md')?.innerText.trim();
                    if (reportContent === "Click a row to view its report.") {
                        alert("Please select a row to view its report before commenting.");
                        return null;
                    }
                    return [report_comment_content, report_comment_score, selected_idx, search_term, username];
                } catch (e) {
                    alert("Error during report comment validation: " + e.message);
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
                dialogue_box, report_box,
                dialogue_comment_box, dialogue_comment_score,
                report_comment_box, report_comment_score,
                dialogue_submit_message,
                dialogue_comments_table, dialogue_number_of_comments,
                report_comments_table, report_number_of_comments,
                dialogue_comment_time_box, dialogue_comment_user_box, dialogue_comment_score_box, dialogue_comment_content_box,
                report_comment_time_box, report_comment_user_box, report_comment_score_box, report_comment_content_box,
                report_submit_message
            ],
            queue=True
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

        go_to_top_btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            preprocess=False,
            js="""
            () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            """
        )

    return demo