# Opticomp

A desktop tool that shows which processes are using the most CPU and memory and suggests which apps could be removed.

## What is in here

| File | What it does |
| --- | --- |
| `task_list_script.py` | Collects process and large-file usage into CSV files. |
| `suggest_apps_script.py` | Normalizes those CSVs against baseline usage (a minimum of 1 to avoid divide-by-zero) and trains an `XGBClassifier` to flag apps that look safe to remove. |
| `UI_main.py` | Tkinter interface with a dark theme. Runs the scripts on start, charts the top 15 processes by CPU and memory with matplotlib, and lists the suggestions. |

## Running it

```bash
pip install pandas matplotlib psutil xgboost
python UI_main.py
```

Windows is the target, since it uses `tasklist`-style data.

## Caveat

The suggestions come from a model trained on my own machine's history, so treat them as a hint and review them before uninstalling anything.
