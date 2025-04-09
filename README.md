這是優化過後的 `README.md`，語言更為精煉、結構更清晰，同時保留你原本的技術細節與流程：

---

# 🧠 LLM-Based Ophthalmology Report Review Platform

This project provides a platform for **LLM-generated ophthalmology dialogues and report summarization**, enabling users to review, comment, and evaluate AI-generated clinical outputs.

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
│   │   └── summary_report.py

│   ├── services/             # Core business logic
│   │   ├── GenReport.py              # Dialogue-to-report LLM pipeline
│   │   ├── EvalCitation.py           # LLM-based citation evaluation
│   │   ├── EvalMetrics.py            # Computes recall/precision
│   │   ├── generate_full_report.py   # Full pipeline integration
│   │   └── report_prompts.py         # Prompt templates

│   ├── database/             # MongoDB interaction
│   │   ├── db_utils_report.py
│   │   ├── Dialogue2db.py
│   │   └── Report2db.py

│   ├── json_dialogue/        # Dialogue JSON data folder
│   ├── json_report/          # Report JSON data folder

│   ├── SOP_module/
│   │   └── user_task_SOPs/
│   │       └── *.json        # SOPs for generating clinical recommendations

│   ├── assets/               # Static images and diagrams
│   │   ├── SchematicFlowDiagram.png
│   │   └── GenReportWorkflow.png

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

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://git.dataarch.myds.me/minkuanchen/ophthalmology_app.git
cd ophthalmology_app
```

### 2. Start services with Docker

Buile the docker container
```bash
docker-compose up --build -d
```

Access the containers:
```bash
# web container
docker exec -it ophthalmology_app_container bash

# mongo db container
docker exec -it ophthalmology_db_container bash
```

### 3. Prepare data

Put your JSON files in:

```
app/json_dialogue/   # For dialogues
app/json_report/     # For reports
```

Import into MongoDB:

```bash
cd app/database
python Dialogue2db.py
python Report2db.py
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

---

## 🗃️ MongoDB Collections

- **Database**: `ophthalmology_db`
- **Collections**:
  - `synthesis_json_user_conv_data_rate_v2`: Dialogue data
  - `reports`: Generated and evaluated reports
  - `user_inter_data_info`: Optional interaction logs

---