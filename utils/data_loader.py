import pandas as pd
import json

# File paths
excel_path = "data/questions.xlsx"
json_path = "data/questions.json"

# Read Excel file
df = pd.read_excel(excel_path)

# Convert all non-serializable values to string
df = df.astype(str)

# Convert DataFrame to list of dictionaries
questions_list = df.to_dict(orient="records")

# Save as JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(questions_list, f, indent=4, ensure_ascii=False)

print("✅ Excel successfully converted to JSON")
print(f"Total questions loaded: {len(questions_list)}")
