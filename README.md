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




# ping_multiple_hosts
# How to use:
**Save the script as ping_multiple_hosts.py

Basic usage - ping individual hosts:

bash
python ping_multiple_hosts.py google.com github.com 8.8.8.8
Ping hosts from a file (one host per line):

bash
python ping_multiple_hosts.py -f hosts.txt
Customize count and timeout:

bash
python ping_multiple_hosts.py --count 3 --timeout 1 google.com github.com
Change number of concurrent workers:

bash
python ping_multiple_hosts.py -w 20 host1 host2 host3
Features:
✅ Works on Windows, Linux, and macOS

✅ Concurrent pinging (faster than sequential)

✅ Shows latency for successful pings

✅ Summary with success/failure percentage

✅ Exit code 1 if any host fails (useful for scripting)

✅ Reads hosts from file or command line

Would you like me to also create a sample hosts.txt file with common hosts for testing?
