import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import psutil
from datetime import datetime

# File patterns for task list and large file data CSVs
TASKLIST_PATTERN = "tasklist_*.csv"
LARGE_FILE_PATTERN = "categorized_large_file_data_*.csv"

# Load and normalize large file data CSVs to get baseline percentages
def get_baseline_usage():
    large_file_files = glob.glob(LARGE_FILE_PATTERN)
    if large_file_files:
        large_file_data = pd.concat([pd.read_csv(f) for f in large_file_files], ignore_index=True)
        avg_cpu = large_file_data['CPU%'].mean() if 'CPU%' in large_file_data else 1
        avg_memory = large_file_data['Memory%'].mean() if 'Memory%' in large_file_data else 1
        
        # Prevent division by zero by setting a minimum baseline of 1
        avg_cpu = max(avg_cpu, 1)
        avg_memory = max(avg_memory, 1)
        return avg_cpu, avg_memory
    return 1, 1  # Default to 1 to avoid division by zero if files are missing

# Load and normalize tasklist data based on large file baseline
def load_tasklist_data(baseline_cpu, baseline_memory):
    tasklist_files = glob.glob(TASKLIST_PATTERN)
    tasklist_data = pd.concat([pd.read_csv(f) for f in tasklist_files], ignore_index=True)
    tasklist_data.dropna(subset=['Name', 'CPU%', 'Memory%'], inplace=True)
    tasklist_data = tasklist_data[tasklist_data['Name'] != "Unknown Process"]
    
    # Normalize CPU and Memory usage and handle any inf values
    tasklist_data['CPU%'] = (tasklist_data['CPU%'] / baseline_cpu) * 100
    tasklist_data['Memory%'] = (tasklist_data['Memory%'] / baseline_memory) * 100
    tasklist_data.replace([float('inf'), -float('inf')], 100, inplace=True)  # Set inf values to 100

    print("Tasklist Data after loading and normalization:", tasklist_data.head())
    return tasklist_data

# Function to select and train ML model
def select_and_train_model(X_train, y_train, model_type="xgboost"):
    model = XGBClassifier() if model_type == "xgboost" else RandomForestClassifier()
    model.fit(X_train, y_train)
    return model

# Suggest apps to remove based on ML model predictions and historical data
def suggest_removable_apps():
    baseline_cpu, baseline_memory = get_baseline_usage()
    tasklist_data = load_tasklist_data(baseline_cpu, baseline_memory)
    
    # Prepare features and labels for training
    X = tasklist_data[['CPU%', 'Memory%']].fillna(0)
    y = (tasklist_data['CPU%'] + tasklist_data['Memory%'] > 10).astype(int)  # Lowered threshold for classification
    
    # Ensure `y` has both classes
    if y.nunique() < 2:
        print("Insufficient class diversity in target variable `y`. No apps to suggest for removal.")
        return
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = select_and_train_model(X_train, y_train, model_type="xgboost")
    
    # Evaluate model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Model Accuracy: {accuracy:.2f}")
    
    # Predict removable processes
    tasklist_data['RemoveSuggestion'] = model.predict(X)
    removable_apps = tasklist_data[(tasklist_data['RemoveSuggestion'] == 1) &
                                   (tasklist_data['CPU%'] < 30) & (tasklist_data['Memory%'] < 30)][['Name', 'CPU%', 'Memory%']]
    
    if removable_apps.empty:
        print("No residual processes which can be removed that are not essential.")
    else:
        print("Suggested removable apps based on usage patterns:")
        print(removable_apps)

    # Display top 5 resource-intensive tasks
    top_tasks = tasklist_data.nlargest(5, ['CPU%', 'Memory%'])
    print("\nTop 5 tasks with highest usage :")
    print(top_tasks[['Name', 'CPU%', 'Memory%']])
     # Save suggested top 5 data with timestamp in filename
    output_csv = f"removable_apps.csv"
    top_tasks.to_csv(output_csv, index=False)
    print(f"Processed data saved to {output_csv}.")

if __name__ == "__main__":
    suggest_removable_apps()