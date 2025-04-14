# LLM-Driven Ophthalmology Dialogue Generation and Summarization

This project provides a platform for **LLM-driven generation and summarization of ophthalmology dialogues**, allowing medical AI researchers to review, comment, and evaluate AI-generated clinical outputs. It features a web interface, MongoDB integration for data storage, and is containerized with Docker for modularity and scalability.

---

## 📁 Project Structure

```
ophthalmology_app/
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker Compose for container orchestration
├── README.md             # Project documentation

├── app/
│   ├── app.py            # Launches the web UI (Gradio)
│   ├── template_line_import.py   # Demo script for importing LINE dialogues and generating reports
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
│   │   ├── line_dialogue_report_db.py # Processes LINE dialogues to reports and imports them into DB
│   │   └── report_prompts.py         # Prompts for LLM
│   ├── database/         # MongoDB interaction
│   │   ├── db_utils_report.py
│   │   ├── Dialogue2db.py
│   │   ├── Report2db.py
│   │   ├── LineComment2db.py
│   │   ├── InsertUsers.py    # Creates users and passwords in DB for login
│   │   └── clear_collection.py  # Cleans DB collections (line_dialogue_report, line_comment, users)
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

- **`app.py`**: Launches the web interface (Gradio).
- **`pages/*.py`**: Web tabs for viewing, scoring, and generating reports.
- **`services/*.py`**: LLM integration (report generation, citation evaluation, metrics).
- **`database/*.py`**: Handles JSON-to-MongoDB data import.
- **`json_dialogue/` & `json_report/`**: Store dialogue and report JSON files.
- **`assets/`**: Flow diagrams for documentation.
- **`line_dialogue_report_db.py`**: Utility script for processing LINE dialogues into reports and importing them into the database. Takes `idx`, `user_type`, `user_name`, and `dialogue` as inputs. Note that the `idx` will be appended with an 8-character random suffix (e.g., `test1` becomes `test1-abcdef12`) to ensure uniqueness.

---

## 🚀 Quick Start

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

### 3. Prepare Data
Place your JSON files in:
```
app/json_dialogue/  # For dialogues
app/json_report/    # For reports
```

Import into MongoDB:
```bash
cd database
python Dialogue2db.py
python Report2db.py
```

### 4. Insert Usernames and Passwords
```bash
cd database
python InsertUsers.py
```

### 5. Import LINE Dialogues and Generate Reports
To demo the LINE comment page, import 10 dialogues and generate reports into the database:
```bash
cd .. # go to folder /app
python template_line_import.py
```

This demonstrates the pipeline in `line_dialogue_report_db.py`. It processes LINE dialogues into reports and imports them into the database. Note that each `idx` in the input data will be appended with an 8-character random suffix (e.g., `test1` becomes `test1-abcdef12`) to ensure uniqueness in the database.

### 6. Launch the Web App
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
| Start Jupyter notebook   | `jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root` |

---

## 🔧 Maintenance

### Backup MongoDB
```bash
docker-compose stop
cp -r mongo_data mongo_data_backup_$(date +%Y%m%d)
```

### Add SOP Templates
Place new SOPs in:
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
Clean the collections `users`, `line_dialogue_report`, and `line_comment`. You can specify collections to exclude from cleaning in `clear_collection.py`.

```bash
cd database
python clear_collection.py
```

---

## 🗃️ MongoDB Collections
- **Database**: `ophthalmology_db`
- **Collections**:
  - `synthesis_json_user_conv_data_rate_v2`: Dialogue data for comments.
  - `reports`: Generated and evaluated reports for comments.
  - `user_inter_data_info`: Optional interaction logs for comments.
  - `line_dialogue_report`: Stores LINE dialogues and reports. Note that `idx` values are appended with an 8-character random suffix (e.g., `test1-abcdef12`).
  - `line_comment`: Stores comments for dialogues and reports.
  - `users`: Stores login usernames and passwords (user0 to user49, where username equals password).

### Common Collection Management
- **Find Collection**:
  ```bash
  docker exec -it ophthalmology_db_container mongosh
  use ophthalmology_db
  db.users.find()          # Find collection users
  db.line_comment.find()   # Find collection line_comment
  ```
- **Inspect a Document** (e.g., `idx="test1-abcdef12"`):
  ```bash
  docker exec -it ophthalmology_db_container mongosh
  use ophthalmology_db
  db.line_dialogue_report.findOne({"idx": "test1-abcdef12"})
  ```