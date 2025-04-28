from pymongo import MongoClient
import pandas as pd

# Connect to MongoDB
client = MongoClient("mongodb://ophthalmology_db_container:27017/")
db = client["ophthalmology_db"]
users_collection = db["users"]

def insert_users(csv_path="./assets/username_member.csv"):
    # 清空現有 users 集合（可選）
    # users_collection.delete_many({})

    try:
        # Read CSV into DataFrame
        users_df = pd.read_csv(csv_path)
        print(f"Read {len(users_df)} users from {csv_path}")

        # Validate required columns
        required_columns = ["username", "email", "password"]
        if not all(col in users_df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")

        # Convert DataFrame to list of dictionaries
        users = users_df[required_columns].to_dict("records")

        inserted_count = 0
        skipped_count = 0

        # Check for duplicates and insert
        for user in users:
            # Check if username or email already exists
            if users_collection.find_one({"$or": [
                {"username": user["username"]},
                {"email": user["email"]}
            ]}):
                print(f"Skipping duplicate user: username={user['username']}, email={user['email']}")
                skipped_count += 1
                continue

            # Insert user
            users_collection.insert_one(user)
            inserted_count += 1
            print(f"Inserted user: username={user['username']}, email={user['email']}")

        print(f"Successfully inserted {inserted_count} users, skipped {skipped_count} duplicates.")
        
        # Verify inserted data
        total_users = users_collection.count_documents({})
        print(f"Total users in collection: {total_users}")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Error inserting users: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    insert_users()