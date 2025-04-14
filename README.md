# LLM-Driven Ophthalmology Dialogue Generation and Summarization

This project provides a platform for **LLM-driven generation and summarization of ophthalmology dialogues**, enabling medical AI researchers to review, comment, and evaluate AI-generated clinical outputs. It features a web interface powered by Gradio, MongoDB integration for data storage, and Docker containerization for modularity and scalability.

---

## ✨ Features

- **Dialogue Generation & Summarization**: Generate and summarize ophthalmology dialogues using LLMs.
- **Web Interface**: Interactive UI for viewing, scoring, and commenting on dialogues and reports.
- **MongoDB Integration**: Store dialogues, reports, and comments in a structured database.
- **Dockerized Deployment**: Easily deploy and scale with Docker and Docker Compose.

---

## 📁 Project Structure

```
ophthalmology_app/
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker Compose for container orchestration
├── README.md             # Project documentation
├── app/
│   ├── app.py            # Launches the web UI (Gradio)
│   ├── template_line_import_with_json.py   # Imports preprocessed dialogues and reports into the database
│   ├── template_line_import_with_usecase.py   # Demo script for importing LINE dialogues and generating reports
│   ├── requirements.txt  # Python dependencies
│   ├── pages/            # UI page modules (Gradio)
│   │   ├── home.py
│   │   ├── dialogue_comment.py
│   │   ├── report_comment.py
│   │   ├── report_generator.py
│   │   ├── summary_report.py
│   │   └── line_comment.py
│   ├── services/         # Core business logic
│   │   ├── GenReport.py              # Dialogue-to-report LLM
│   │   ├── EvalCitation.py           # LLM-based citation evaluation
│   │   ├── EvalMetrics.py            # Computes recall/precision
│   │   ├── line_dialogue_report_db.py # Processes LINE dialogues into reports and imports them into the database
│   │   └── report_prompts.py         # Prompts for LLMs
│   ├── database/         # MongoDB interaction
│   │   ├── db_utils_report.py
│   │   ├── Dialogue2db.py
│   │   ├── Report2db.py
│   │   ├── LineComment2db.py
│   │   ├── InsertUsers.py    # Creates usernames and passwords in the database for login
│   │   └── clear_collection.py  # Cleans database collections (line_dialogue_report, line_comment, users)
│   ├── json_dialogue/    # Dialogue JSON data folder
│   ├── json_report/      # Report JSON data folder
│   ├── SOP_module/       # SOP templates
│   │   └── user_task_SOPs/
│   │       └── *.json
│   ├── assets/           # Static images and diagrams
│   │   ├── SchematicFlowDiagram.png
│   │   └── GenReportWorkflow.png
│   └── utils.py          # General-purpose utilities
├── mongo_data/           # MongoDB persistent storage
```

---

## ⚙️ Core Components

- **`app.py`**: Launches the Gradio web interface for user interaction.
- **`pages/*.py`**: Modules for different UI tabs (e.g., dialogue commenting, report generation).
- **`services/*.py`**: Handles LLM integration, including report generation, citation evaluation, and metrics computation.
- **`database/*.py`**: Manages data import/export between JSON files and MongoDB.
- **`json_dialogue/` & `json_report/`**: Stores dialogue and report JSON files.
- **`assets/`**: Contains flow diagrams for documentation.
- **`line_dialogue_report_db.py`**: Processes LINE dialogues into reports and imports them into the database. It takes `idx`, `user_type`, `user_name`, and `dialogue` as inputs. The `idx` is appended with `user_name` and an 8-character random suffix (e.g., `Emily-abcdef12`) to ensure uniqueness. 
  - **Example Output**:       
    ```json
    {
      "idx": "Emily-abcdef12",
      "object_type": "Doctor",
      "object_name": "Emily",
      "dialogue_content": "使用者問題/回覆1: 大約一個星期以來，每次用電腦久了，兩眼都會感到酸痛\n系統回覆1: 系統詢問: 需要提供\"您最近有覺得視力變差嗎？",
      "report_content": "#### **1. Patient Complaint**\n\n- Eye strain and soreness in both eyes. \n\n- This has been going on for about a week.",
      "gen_model": "Llama-3.1-Nemotron-70B-Instruct"
    }
    ```

---

## 🚀 Quick Start

Follow these steps to set up and run the project.

### 1. Clone the Repository
```bash
git clone https://git.dataarch.myds.me/minkuanchen/ophthalmology_app.git
cd ophthalmology_app
```

### 2. Start Docker Services
```bash
docker-compose up --build -d
```

- **Access the app container**:
  ```bash
  docker exec -it ophthalmology_app_container bash
  ```
- **Access the MongoDB container (optional)**:
  ```bash
  docker exec -it ophthalmology_db_container bash
  ```

### 3. Insert Usernames and Passwords
Create default users (user1 to user50, where username equals password) for login:
```bash
cd app/database
python InsertUsers.py
```

### 4. Prepare Data
Place your JSON files in the following directories:
```
app/json_dialogue/  # For dialogues
app/json_report/    # For reports
```

Import the JSON data into MongoDB:
```bash
python Dialogue2db.py
python Report2db.py
```

### 5. Import Preprocessed Dialogues and Reports
Import preprocessed dialogues and reports into the database using `template_line_import_with_json.py`:
```bash
cd ..  # Go to folder /app
python template_line_import_with_json.py
```

#### About `template_line_import_with_json.py`
- **`ready_report_from_dialogue()`**: Reads dialogues from `./json_dialogue/hole_qa_conversation_process_patient_doctor_v3.json`, generates reports, and saves them to `./json_report/generated_reports.json`.
- **`import_completed_data_to_db()`**: Imports the preprocessed dialogues and reports from `./json_report/generated_reports.json` into the `line_dialogue_report` collection.

Example usage:
```python
# Generate reports from dialogues and save to JSON
# ready_report_from_dialogue()

# Import preprocessed dialogues and reports into the database
import_completed_data_to_db()
```

### 6. (Optional) Import LINE Dialogues for Demo
To demo the LINE comment page, import 10 dialogues and generate reports into the database using `template_line_import_with_usecase.py`:
```bash
python template_line_import_with_usecase.py
```

This script demonstrates the pipeline in `line_dialogue_report_db.py`. It processes LINE dialogues into reports and imports them into the database. Each `idx` is appended with `user_name` and an 8-character random suffix (e.g., `Emily-abcdef12`) to ensure uniqueness.

### 7. Launch the Web App
```bash
python app.py
```

Access the app at:
```
http://localhost:7860
```

---

## 🐳 Docker Commands

| Action                   | Command                                      |
|--------------------------|----------------------------------------------|
| Start containers         | `docker-compose up -d`                      |
| Stop containers          | `docker-compose stop`                       |
| Rebuild containers       | `docker-compose up --build -d`              |
| View logs                | `docker-compose logs`                       |
| Enter app container      | `docker exec -it ophthalmology_app_container bash` |
| Enter MongoDB container  | `docker exec -it ophthalmology_db_container bash` |
| Start Jupyter Notebook   | `jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root` |

---

## 🔧 Maintenance

### Backup MongoDB
```bash
docker-compose stop
cp -r mongo_data mongo_data_backup_$(date +%Y%m%d)
```

### Add SOP Templates
Place new SOP templates in:
```
app/SOP_module/user_task_SOPs/
```
Restart the service:
```bash
docker-compose restart
```

### Update Dependencies
Edit `requirements.txt`, then rebuild:
```bash
docker-compose up --build -d
```

### Clean Database
Clean the `users`, `line_dialogue_report`, and `line_comment` collections. Specify collections to exclude in `clear_collection.py`:
```bash
cd app/database
python clear_collection.py
```

---

## 🗃️ MongoDB Collections

- **Database**: `ophthalmology_db`
- **Collections**:
  - `synthesis_json_user_conv_data_rate_v2`: Stores dialogue data for comments.
  - `reports`: Stores generated and evaluated reports for comments.
  - `user_inter_data_info`: Optional interaction logs for comments.
  - `line_dialogue_report`: Stores LINE dialogues and reports. The `idx` values are appended with `user_name` and an 8-character random suffix (e.g., `Emily-abcdef12`).
    - **Example Document**:
      ```json
      {
        "idx": "Emily-abcdef12",
        "object_type": "Doctor",
        "object_name": "Emily",
        "dialogue_content": "使用者問題/回覆1: 大約一個星期以來，每次用電腦久了，兩眼都會感到酸痛\n系統回覆1: 系統詢問: 需要提供\"您最近有覺得視力變差嗎？",
        "report_content": "#### **1. Patient Complaint**\n\n- Eye strain and soreness in both eyes. \n\n- This has been going on for about a week.",
        "gen_model": "Llama-3.1-Nemotron-70B-Instruct"
      }
      ```
  - `line_comment`: Stores comments for dialogues and reports.
    - **Example Document**:
      ```json
      {
        "idx": "Emily-abcdef12",
        "comment_time": "2025-04-14 10:30:00",
        "user_name": "user1",
        "comment_content": "The report is concise.",
        "comment_score": 4
      }
      ```
  - `users`: Stores login usernames and passwords (user0 to user49, where username equals password).

### Common Collection Management
- **Find Collection**:
  ```bash
  docker exec -it ophthalmology_db_container mongosh
  use ophthalmology_db
  db.users.find()          # Find collection users
  db.line_comment.find()   # Find collection line_comment
  ```
- **Inspect a Document** (e.g., `idx="dialogue_Emily_1-abcdef12"`):
  ```bash
  docker exec -it ophthalmology_db_container mongosh
  use ophthalmology_db
  db.line_dialogue_report.findOne({"idx": "dialogue_Emily_1-abcdef12"})
  ```

---

## 🛠️ Troubleshooting

### 1. **Web App Not Accessible at `http://localhost:7860`**
   - Ensure `app.py` is running in the app container.
   - Check Docker logs for errors:
     ```bash
     docker-compose logs
     ```
   - Verify the port is not blocked by another process.

### 2. **MongoDB Connection Issues**
   - Ensure the MongoDB container is running:
     ```bash
     docker ps
     ```
   - Check the MongoDB logs:
     ```bash
     docker logs ophthalmology_db_container
     ```
   - Verify the connection settings in `docker-compose.yml`.

### 3. **No Data in `line_dialogue_report` Collection**
   - Ensure you have run `template_line_import_with_json.py` or `template_line_import_with_usecase.py` to populate the database.
   - Check the JSON files in `json_dialogue/` and `json_report/` for correct formatting.

---