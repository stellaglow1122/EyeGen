from LineComment2db import clear_line_dialogue_report_collection, clear_line_comment_collection, clear_users_collection

# 清空 line_dialogue_report 集合
print("Clearing line_dialogue_report collection...")
clear_line_dialogue_report_collection(confirm=True)

# 清空 line_comment 集合
print("Clearing line_comment collection...")
clear_line_comment_collection(confirm=True)

# # 清空 users 集合
# print("Clearing user collection...")
# clear_users_collection(confirm=True)

print("Collections cleared successfully.")