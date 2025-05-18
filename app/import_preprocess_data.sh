#!/bin/bash
set -e  # 如果任一指令失敗就停止腳本

# Step 1: Insert users
cd database
echo "Inserting users..."
python InsertUsers.py

# Step 2: Import dialogues and reports for pages of dialogue comment and report comment
echo "Importing dialogues..."
python Dialogue2db.py
echo "Importing reports..."
python Report2db.py
cd ..

# Step 3: Import preprocessed data for page of line comment
echo "Importing processed data..."
python template_line_import_with_json.py
