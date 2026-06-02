# Python-Automation-Scripts
Python scripts for IT operations, reporting, monitoring, and automation.
Python-Automation-Scripts
│
├── File-Automation
├── Network-Tools
├── Monitoring
├── Reports
├── Utilities



# Basic usage (default: warning at 80%, critical at 90%)
python disk_space_monitor.py

# Custom thresholds
python disk_space_monitor.py --warning 75 --critical 85

# Monitor a specific path
python disk_space_monitor.py --path /home

# JSON output
python disk_space_monitor.py --json

# Save JSON to file
python disk_space_monitor.py --json --json-output disk_status.json

# Exit code for CI/CD (exit 1 on WARNING, 2 on CRITICAL)
python disk_space_monitor.py --exit-code --warning 90 --critical 95
