# LLM-Driven Generation and Summarization of Ophthalmology Dialogue

This project provides a platform for **LLM-Driven Generation and Summarization of Ophthalmology Dialogue**, enabling users to review, comment, and evaluate AI-generated clinical outputs.

Designed for medical AI researchers, this system allows importing ophthalmology dialogue/report JSON files into **MongoDB**, and provides a **web interface for reviewing and commenting**. Built in Python and containerized with Docker, the system is modular, extensible, and production-ready.

---

## 📁 Project Structure

```
ophthalmology_app/
├── Dockerfile                 # Docker build configuration
├── docker-compose.yml        # Docker Compose for container orchestration
├── README.md                 # Project documentation and usage

├── app/
│   ├── app.py                # Launches the web UI (Gradio)
│   ├── requirements.txt      # Python dependencies

│   ├── pages/                # UI page modules (via Gradio)
│   │   ├── home.py
│   │   ├── dialogue_comment.py
│   │   ├── report_comment.py
│   │   ├── report_generator.py
│   │   ├── summary_report.py
│   │   └── line_comment.py

│   ├── services/             # Core business logic
│   │   ├── GenReport.py              # Dialogue-to-report LLM
│   │   ├── EvalCitation.py           # LLM-based citation evaluation
│   │   ├── EvalMetrics.py            # Computes recall/precision
│   │   └── report_prompts.py         # Prompt for LLM

│   ├── database/             # MongoDB interaction
│   │   ├── db_utils_report.py
│   │   ├── Dialogue2db.py
│   │   ├── Report2db.py
│   │   └── LineComment2db.py # Database operations for line comment

│   ├── json_dialogue/        # Dialogue JSON data folder
│   ├── json_report/          # Report JSON data folder

│   ├── SOP_module/
│   │   └── user_task_SOPs/
│   │       └── *.json        # SOPs for generating clinical recommendations

│   ├── assets/               # Static images and diagrams
│   │   ├── SchematicFlowDiagram.png
│   │   └── GenReportWorkflow.png

│   ├── line_dialogue_report_db.py  # Demonstrates the pipeline from dialogue to report generation and import to db

│   └── utils.py              # General-purpose utilities

├── mongo_data/               # MongoDB persistent storage
```

---

## ⚙️ Core Components

- `app.py`: Entry point for launching the web interface
- `pages/*.py`: Web interface tabs for viewing, scoring, and generating reports
- `services/*.py`: LLM integration (report generation, citation evaluation, metrics)
- `database/*.py`: JSON-to-MongoDB data import
- `json_dialogue/`, `json_report/`: Folders to place your data files
- `assets/`: Flow diagrams for documentation and platform overview
- `line_dialogue_report_db.py`: A utility script demonstrating the pipeline from dialogue to report generation and database import. Provides a function that takes idx, user_type, user_name, dialogue as input.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://git.dataarch.myds.me/minkuanchen/ophthalmology_app.git
cd ophthalmology_app
```

### 2. Start services with Docker

Build the docker container
```bash
docker-compose up --build -d
```

Access the web container:
```bash
docker exec -it ophthalmology_app_container bash
```

Access the mongo db container (optional):
```bash
docker exec -it ophthalmology_db_container bash
```

### 3. Prepare data

Put your JSON files in:

```
app/json_dialogue/   # For dialogue
app/json_report/     # For reports
```

Import into MongoDB:

```bash
cd app/database
python Dialogue2db.py
python Report2db.py
```

Import row dialogue and demonstrate the flow from dialogue to report generation and import into database:
```bash
cd app/
python line_dialogue_report_db.py
```

### 4. Launch the Web App

```bash
python app.py
```

Default URL:

```
http://localhost:7860
```

---

## 🐳 Docker Cheat Sheet

| Action                     | Command |
|---------------------------|---------|
| Start containers          | `docker-compose up -d` |
| Stop containers           | `docker-compose stop` |
| Rebuild containers        | `docker-compose up --build -d` |
| View logs                 | `docker-compose logs` |
| Enter app container       | `docker exec -it ophthalmology_app_container bash` |
| Enter Mongo container     | `docker exec -it ophthalmology_db_container bash` |
| Start jupyter in container| `jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root` |

---

## 🔧 Maintenance

- **Backup MongoDB**:

```bash
docker-compose stop
cp -r mongo_data mongo_data_backup_$(date +%Y%m%d)
```

- **Add SOP templates**:

Put new SOPs in:

```
app/SOP_module/user_task_SOPs/
```

Then restart:

```bash
docker-compose restart
```

- **Update dependencies**:

Update `requirements.txt`, then:

```bash
docker-compose up --build -d
```

- **Clean `line_comment` Collection Lock Info**:

Reset the lock info in the `line_comment` collection:

```bash
docker exec -it ophthalmology_db_container mongosh
use ophthalmology_db
db.line_comment.updateMany( {}, { "$set": { "lock_info": { "locked": false, "session_id": "", "lock_time": 0 } }, "$unset": { "is_locked": "" } } )
```

- **Check `line_comment` Collection**:

Inspect a specific document in the `line_comment` collection (e.g. idx=="jjjjjj"):

```bash
docker exec -it ophthalmology_db_container mongosh
use ophthalmology_db
db.line_comment.findOne({"idx": "jjjjjj"})
```

---

## 🗃️ MongoDB Collections

- **Database**: `ophthalmology_db`
- **Collections**:
  - `synthesis_json_user_conv_data_rate_v2`: Dialogue data for comment
  - `reports`: Generated and evaluated reports for comment
  - `user_inter_data_info`: Optional interaction logs for comment
  - `line_comment`: Stores LINE dialogues, reports, and associated comments with lock information for concurrent access

---