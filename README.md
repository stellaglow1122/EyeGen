# Ophthalmology App

**Ophthalmology App** is an tool designed to manage and analyze ophthalmology-related conversation data. This application supports importing conversation and report data from JSON files into MongoDB and provides a web interface for viewing, evaluating, and editing the data. Built with Python and deployed using Docker, it’s ideal for researchers, developers, and medical professionals.

---

## Features
- **Data Import**: Import conversation data (`Dialogue2Mongo.py`) and reports (`Report2Mongo.py`) from JSON into MongoDB.
- **Web Interface**: Interactive UI via `app.py` for data visualization and editing.
- **SOP Support**: Includes Standard Operating Procedure (SOP) JSON files in `SOP_module/user_task_SOPs/`.
- **Containerized Deployment**: Uses Docker and Docker Compose for consistent environments.

---

## Project Structure
```
ophthalmology_app/
├── Dockerfile              # Docker configuration file
├── README.md               # This file
├── app/                    # Main application directory
│   ├── Dialogue2Mongo.py   # Script to import conversation data into MongoDB
│   ├── Report2Mongo.py     # Script to import report data into MongoDB
│   ├── SOP_module/         # Directory for SOP files
│   │   └── user_task_SOPs/
│   │       ├── ask_cataract_len_SOP.json
│   │       ├── ask_lensx_SOP.json
│   │       ├── give_up_SOP.json
│   │       ├── intraocular_lens_decisions_SOP.json
│   │       └── patient_doctor_SOP.json
│   ├── app.py              # Main application (Web interface)
│   ├── assets/             # Static assets
│   │   └── SchematicFlowDiagram.png
│   ├── db_utils_report.py  # MongoDB utility functions
│   ├── json_dialogue/      # Conversation data JSON files
│   ├── json_report/        # Report data JSON files
│   ├── pages/              # Web page modules
│   │   ├── dialogue_comment.py
│   │   ├── home.py
│   │   └── report_comment.py
│   ├── requirements.txt    # Python dependencies
│   └── utils.py            # General utility functions
├── docker-compose.yml      # Docker Compose configuration
└── mongo_data/             # MongoDB data storage directory
```

---

## Prerequisites
Before getting started, ensure you have the following installed:
- **Git**: For cloning the repository from GitLab.
- **Docker**: For containerized deployment (recommended version 20.10 or later).
- **Docker Compose**: For managing multi-container applications (recommended version 1.29 or later).
- **Python**: For local execution without Docker (Python 3.10 or later).
- **MongoDB**: Required locally if not using Docker (version 4.4 or later).

---

## Quick Start
Follow these steps to get the app running quickly using Docker:

1. **Clone the Repository**:
   ```bash
   git clone https://gitlab.com/your-username/ophthalmology_app.git
   cd ophthalmology_app
   ```

2. **Build and Start Containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the Web Application**:
   Open your browser and navigate to `http://localhost:7860`.

4. **Populate the Database**:
   See the [Populating the Database](#populating-the-database-with-content) section below.

---

## Docker Container Setup and Operations

### Start Containers
To start the containers without rebuilding (preserving data):
```bash
docker-compose up -d
```

### Stop Without Removing (Preserve Data)
To stop the containers while keeping data intact:
```bash
docker-compose stop
```

### Stop and Remove Containers
To stop and remove containers (data in `mongo_data/` persists):
```bash
docker-compose down
```

### Rebuilding Containers
To rebuild and restart containers (e.g., after code changes):
```bash
docker-compose up --build -d
```

### Entering a Container
To access a running container (e.g., for debugging or running scripts):
1. List running containers:
   ```bash
   docker ps
   ```
   Identify the container name or ID (e.g., `ophthalmology_app_container` for the app service, `ophthalmology_db_container` for MongoDB).
2. Enter the container:
   - For the app container:
     ```bash
     docker exec -it ophthalmology_app_container bash
     ```
   - For the MongoDB container:
     ```bash
     docker exec -it ophthalmology_db_container bash
     ```
3. Once inside, you can run commands (e.g., `python Dialogue2Mongo.py`) or inspect the environment.

### Viewing Logs
To view logs for debugging:
```bash
docker-compose logs
```
For a specific service (e.g., `app`):
```bash
docker-compose logs app
```

---

## Launching the Web Application

### Via Docker
1. Ensure Docker and Docker Compose are installed.
2. Start the containers:
   ```bash
   docker-compose up -d
   ```
3. Access the app at `http://localhost:7860`.

### Locally (Without Docker)
1. Install dependencies:
   ```bash
   cd app
   pip install -r requirements.txt
   ```
2. Start a local MongoDB instance (e.g., `mongod`).
3. Run the app:
   ```bash
   python app.py
   ```
4. Access at `http://localhost:7860`.

---

## Populating the Database with Content

### Importing Conversation Data
To import conversation data from JSON into MongoDB:
1. Ensure the JSON file (e.g., `hole_qa_v2_doctor_eval_data_30.json`) is in `app/json_dialogue/`.
2. Run the import script:
   - Via Docker:
     ```bash
     docker exec -it ophthalmology_app_container python Dialogue2Mongo.py
     ```
   - Locally:
     ```bash
     cd app
     python Dialogue2Mongo.py
     ```
   - This imports data into the `synthesis_json_user_conv_data_rate_v2` collection in the `ophthalmology_db` database.
   - If data already exists (checked by `uid`, `prev_step_str`, and `user_response`), it will be skipped.

### Importing Report Data
To import report data from JSON:
1. Ensure report JSON files are in `app/json_report/`.
2. Run the import script:
   - Via Docker:
     ```bash
     docker exec -it ophthalmology_app_container python Report2Mongo.py
     ```
   - Locally:
     ```bash
     cd app
     python Report2Mongo.py
     ```
   - This populates the report collection (adjust script as needed).

---

## Maintenance

### Backup Database
To back up MongoDB data:
1. Stop the containers:
   ```bash
   docker-compose stop
   ```
2. Copy the `mongo_data/` directory:
   ```bash
   cp -r mongo_data/ mongo_data_backup_$(date +%Y%m%d)
   ```

### Update Dependencies
To update Python packages:
1. Edit `app/requirements.txt` as needed.
2. Rebuild containers:
   ```bash
   docker-compose up --build -d
   ```

### Add New SOPs
To add new SOP JSON files:
1. Place the file in `app/SOP_module/user_task_SOPs/`.
2. Restart the app to load the new SOP:
   ```bash
   docker-compose restart
   ```

---

## Usage Example
1. **Import Data**:
   ```bash
   docker exec -it ophthalmology_app_container python Dialogue2Mongo.py
   ```
   Output:
   ```
   len(doctor_eval_datas): 682
   Connected to database: ophthalmology_db
   Inserted document 1 with _id: ...
   Successfully inserted 682 new datas, skipped 0 existing datas into db synthesis_json_user_conv_data_rate_v2 table !!!
   ```

2. **Launch the App**:
   ```bash
   docker-compose up -d
   ```
   Visit `http://localhost:7860` to view and edit data.

3. **Verify Data**:
   ```bash
   docker exec -it ophthalmology_app_container python test.py
   ```
   Output:
   ```
   Total documents in synthesis_json_user_conv_data_rate_v2: 682
   Document 1: {...}
   ```

---

根據你提供的程式碼，我可以幫你分析目前使用的資料庫名稱以及其中的表（collection）名稱。MongoDB 使用「資料庫」（database）和「集合」（collection）來組織數據，這與傳統 SQL 資料庫的「表」（table）概念類似。以下是分析結果：

---

## 資料庫名稱
 `db_utils_report.py` 中的 `init_db()` 函數來初始化資料庫連線。該函數的定義如下：

```python
def init_db():
    client = MongoClient("mongodb://report_db:27017/")
    db = client["ophthalmology_db"]
    return db
```

- **資料庫名稱**：`ophthalmology_db`
  - 這是透過 `client["ophthalmology_db"]` 明確指定的。
  - 所有後續操作都基於這個資料庫。


#### 資料庫名稱
- **`ophthalmology_db`**

#### 集合名稱
1. **`reports`**
   - 用於儲存報告數據。
   - 出現在 `Report2Mongo.py`、`db_utils_report.py` 和 `report_comment.py` 中。
2. **`synthesis_json_user_conv_data_rate_v2`**
   - 用於儲存對話數據和評分。
   - 出現在 `Dialogue2Mongo.py` 和 `dialogue_comment.py` 中。
3. **`user_inter_data_info`**
   - 出現在 `dialogue_comment.py` 中，可能用於儲存用戶交互數據，但目前程式碼未見具體操作。
