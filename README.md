# Ophthalmology App

**Ophthalmology App** is a tool designed to manage and analyze ophthalmology-related conversation and report data. It allows importing JSON files into MongoDB and provides a web interface for viewing and commenting on the data. Built with Python and containerized using Docker, this app is ideal for researchers and developers in medical data domains.

---

## 📁 Project Structure

```
ophthalmology_app/
├── Dockerfile                # Docker build configuration
├── docker-compose.yml        # Docker Compose setup
├── README.md                 # Project documentation
├── app/
│   ├── app.py                # Main web application
│   ├── requirements.txt      # Python dependencies
│   ├── Dialogue2Mongo.py     # Script to import dialogue data into MongoDB
│   ├── Report2Mongo.py       # Script to import report data into MongoDB
│   ├── db_utils_report.py    # MongoDB initialization and helper functions
│   ├── utils.py              # General utility functions
│   ├── json_dialogue/        # Folder for dialogue JSON files (must add your files)
│   ├── json_report/          # Folder for report JSON files (must add your files)
│   ├── SOP_module/
│   │   └── user_task_SOPs/   # SOP JSON templates
│   ├── pages/
│   │   ├── home.py
│   │   ├── dialogue_comment.py
│   │   └── report_comment.py
│   └── assets/
│       └── SchematicFlowDiagram.png
└── mongo_data/               # MongoDB volume for persistent data
```

---

## 🧠 Python Script Overview

- **`Dialogue2Mongo.py`**: Imports JSON files from `json_dialogue/` into the `synthesis_json_user_conv_data_rate_v2` collection.
- **`Report2Mongo.py`**: Imports report JSON files from `json_report/` into the `reports` collection.
- **`app.py`**: Main entry point for launching the web interface.
- **`db_utils_report.py`**: Handles database connection and utilities.
- **`pages/*.py`**: UI pages for home, dialogue, and report commenting.

---

## 🚀 Quick Start

#### 1. Clone the Repository

```bash
git clone https://git.dataarch.myds.me/minkuanchen/ophthalmology_app.git
cd ophthalmology_app
```

#### 2. Add JSON Files

> Make sure to add your own data files. The app will not function without these.

```bash
# Add dialogue files to:
app/json_dialogue/

# Add report files to:
app/json_report/
```

#### 3. Start Docker Containers

```bash
docker-compose up --build -d
```

#### 4. Import Data into MongoDB

```bash
# Access the application container
docker exec -it ophthalmology_app_container bash

# Import dialogue data
python Dialogue2Mongo.py

# Import report data
python Report2Mongo.py
```

You can also enter the MongoDB container (for inspection):

```bash
docker exec -it ophthalmology_db_container bash
```

#### 5. Launch the Web App (in container)

```bash
python app.py
```

Then open your browser at:

```
http://localhost:7860
```

---

## 🐳 Docker Commands

| Action                     | Command |
|---------------------------|---------|
| Start containers          | `docker-compose up -d` |
| Stop containers           | `docker-compose stop` |
| Remove containers         | `docker-compose down` |
| Rebuild containers        | `docker-compose up --build -d` |
| List running containers   | `docker ps` |
| Enter app container       | `docker exec -it ophthalmology_app_container bash` |
| Enter MongoDB container   | `docker exec -it ophthalmology_db_container bash` |
| View logs                 | `docker-compose logs` or `docker-compose logs app` |
| Start jupyter in container| `jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root` |

---

## 📦 Maintenance

- **Backup MongoDB Data**:

  ```bash
  docker-compose stop
  cp -r mongo_data mongo_data_backup_$(date +%Y%m%d)
  ```

- **Update Python Packages**:

  Modify `app/requirements.txt` as needed, then rebuild:

  ```bash
  docker-compose up --build -d
  ```

- **Add New SOP Templates**:

  Place your JSON files in:

  ```
  app/SOP_module/user_task_SOPs/
  ```

  Restart the app to apply changes:

  ```bash
  docker-compose restart
  ```

---

## 🗂️ MongoDB Collections

- **Database**: `ophthalmology_db`
- **Collections**:
  - `synthesis_json_user_conv_data_rate_v2`: Dialogue data
  - `reports`: Report data
  - `user_inter_data_info`: (Optional) User interaction metadata