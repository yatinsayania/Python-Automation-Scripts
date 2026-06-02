"""
disk_space_monitor.py - Disk Space Monitor Script

This script monitors disk space usage on your system and alerts you when
disk usage exceeds defined thresholds. It works on Linux, macOS, and Windows.

Features:
- Check disk usage for all mounted drives/partitions
- Configurable warning and critical thresholds (percentage)
- Output in human-readable format (GB, MB)
- Optional: Exit with error code for CI/CD integration
- Optional: JSON output for scripting
"""

import os
import sys
import json
import argparse
from datetime import datetime


def get_disk_usage(path="/"):
    """
    Get disk usage statistics for a given path.
    
    Returns:
        tuple: (total_bytes, used_bytes, free_bytes, percent_used)
    """
    try:
        stat = os.statvfs(path)
        total_bytes = stat.f_blocks * stat.f_frsize
        free_bytes = stat.f_bavail * stat.f_frsize
        used_bytes = total_bytes - free_bytes
        percent_used = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
        return total_bytes, used_bytes, free_bytes, percent_used
    except OSError as e:
        return None, None, None, None


def format_bytes(bytes_value):
    """Convert bytes to human-readable format."""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} EB"


def get_all_partitions():
    """Get all mounted partitions/drives."""
    partitions = []
    
    if sys.platform == "win32":
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                partitions.append(drive)
    else:
        mount_points = ["/", "/home", "/var", "/tmp", "/boot"]
        for mp in mount_points:
            if os.path.exists(mp):
                try:
                    os.statvfs(mp)
                    if mp not in partitions:
                        partitions.append(mp)
                except OSError:
                    continue
        
        if os.path.exists("/proc/mounts"):
            try:
                with open("/proc/mounts", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            mount_point = parts[1]
                            if mount_point not in partitions and os.path.exists(mount_point):
                                try:
                                    os.statvfs(mount_point)
                                    partitions.append(mount_point)
                                except OSError:
                                    continue
            except Exception:
                pass
    
    return partitions if partitions else ["/"]


def check_disk_space(warning_threshold=80, critical_threshold=90, 
                     path="/", output_format="text", json_output_file=None):
    """Check disk space and return results."""
    partitions = get_all_partitions() if path == "/" else [path]
    results = []
    max_status = "OK"
    
    for partition in partitions:
        total, used, free, percent = get_disk_usage(partition)
        
        if total is None:
            continue
        
        if percent >= critical_threshold:
            status = "CRITICAL"
            if max_status != "CRITICAL":
                max_status = "CRITICAL"
        elif percent >= warning_threshold:
            status = "WARNING"
            if max_status not in ["CRITICAL"]:
                max_status = "WARNING"
        else:
            status = "OK"
        
        results.append({
            "partition": partition,
            "total": format_bytes(total),
            "total_bytes": total,
            "used": format_bytes(used),
            "used_bytes": used,
            "free": format_bytes(free),
            "free_bytes": free,
            "percent_used": round(percent, 2),
            "status": status
        })
    
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold,
        "partitions": results,
        "overall_status": max_status
    }
    
    if output_format == "json":
        json_str = json.dumps(output_data, indent=2)
        if json_output_file:
            with open(json_output_file, "w") as f:
                f.write(json_str)
        return json_str
    else:
        output_lines = []
        output_lines.append(f"\n{'='*70}")
        output_lines.append(f"DISK SPACE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"{'='*70}\n")
        output_lines.append(f"Warning Threshold: {warning_threshold}%")
        output_lines.append(f"Critical Threshold: {critical_threshold}%")
        output_lines.append(f"\n{'Partition':<20} {'Total':<12} {'Used':<12} {'Free':<12} {'Used%':<8} {'Status'}")
        output_lines.append("-" * 70)
        
        for p in results:
            output_lines.append(
                f"{p['partition']:<20} {p['total']:<12} {p['used']:<12} "
                f"{p['free']:<12} {p['percent_used']:<8.1f} {p['status']}"
            )
        
        output_lines.append("-" * 70)
        output_lines.append(f"Overall Status: {max_status}")
        output_lines.append(f"{'='*70}\n")
        
        return "\n".join(output_lines), max_status


def main():
    parser = argparse.ArgumentParser(
        description="Monitor disk space usage and alert on threshold violations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python disk_space_monitor.py
  python disk_space_monitor.py --warning 75 --critical 85
  python disk_space_monitor.py --path /home --json
  python disk_space_monitor.py --json --json-output disk_status.json
  python disk_space_monitor.py --exit-code --warning 90 --critical 95
        """
    )
    
    parser.add_argument("--warning", "-w", type=int, default=80,
                        help="Warning threshold percentage (default: 80)")
    parser.add_argument("--critical", "-c", type=int, default=90,
                        help="Critical threshold percentage (default: 90)")
    parser.add_argument("--path", "-p", type=str, default="/",
                        help="Path to monitor (default: / for all partitions)")
    parser.add_argument("--json", action="store_true",
                        help="Output in JSON format")
    parser.add_argument("--json-output", type=str,
                        help="Save JSON output to file")
    parser.add_argument("--exit-code", action="store_true",
                        help="Exit with non-zero code on WARNING/CRITICAL (for CI/CD)")
    
    args = parser.parse_args()
    
    if args.warning >= args.critical:
        print("Error: Warning threshold must be less than critical threshold")
        sys.exit(2)
    
    if args.warning < 0 or args.critical > 100:
        print("Error: Thresholds must be between 0 and 100")
        sys.exit(2)
    
    output_format = "json" if args.json else "text"
    result = check_disk_space(
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        path=args.path,
        output_format=output_format,
        json_output_file=args.json_output
    )
    
    if output_format == "json":
        print(result)
    else:
        text_output, status = result
        print(text_output)
        
        if args.exit_code:
            if status == "CRITICAL":
                sys.exit(2)
            elif status == "WARNING":
                sys.exit(1)
            else:
                sys.exit(0)


if __name__ == "__main__":
    main()
