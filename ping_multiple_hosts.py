#!/usr/bin/env python3
"""
ping_multiple_hosts.py

A Python script to check connectivity (ping) to multiple hosts concurrently.
Supports both Windows and Unix-like systems (Linux, macOS).

Usage:
    python ping_multiple_hosts.py host1 host2 host3 ...
    python ping_multiple_hosts.py -f hosts.txt
    python ping_multiple_hosts.py --count 3 --timeout 2 host1 host2

Features:
    - Concurrent pinging using ThreadPoolExecutor
    - Customizable packet count and timeout
    - Summary statistics at the end
    - Reads hosts from command line or file
"""

import argparse
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_host_file(host_file):
    """Read hosts from a file, one per line. Ignores comments and empty lines."""
    hosts = []
    with open(host_file, "r") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line)
    return hosts


def ping_host(host, count=4, timeout=2):
    """Ping a single host and return (host, success, latency_ms, message)."""
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * count + 10)
        success = result.returncode == 0
        
        latency = None
        if "time=" in result.stdout:
            import re
            m = re.search(r"time[=<](\d+\.?\d*)\s*ms", result.stdout, re.I)
            if m:
                latency = float(m.group(1))
        
        msg = f"Success - {latency:.2f}ms" if success and latency else ("Success" if success else "Failed")
        return (host, success, latency, msg)
    except Exception as e:
        return (host, False, None, f"Error - {e}")


def main():
    parser = argparse.ArgumentParser(description="Ping multiple hosts concurrently")
    parser.add_argument("hosts", nargs="*", help="Hosts to ping")
    parser.add_argument("-f", "--file", help="Host file (one host per line)")
    parser.add_argument("-c", "--count", type=int, default=4, help="Packets per host (default: 4)")
    parser.add_argument("-t", "--timeout", type=int, default=2, help="Timeout in seconds (default: 2)")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Max concurrent workers (default: 10)")
    args = parser.parse_args()
    
    hosts = []
    if args.file:
        try:
            hosts.extend(parse_host_file(args.file))
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
    hosts.extend(args.hosts)
    
    if not hosts:
        print("Usage: python ping_multiple_hosts.py host1 host2 ... OR -f hosts.txt")
        print("\nExamples:")
        print("  python ping_multiple_hosts.py google.com github.com")
        print("  python ping_multiple_hosts.py -f hosts.txt")
        sys.exit(1)
    
    # Remove duplicates
    seen = set()
    unique = [h for h in hosts if not (h in seen or seen.add(h))]
    
    print(f"\nPinging {len(unique)} host(s)...")
    print(f"Count: {args.count}, Timeout: {args.timeout}s, Workers: {args.workers}")
    print("-" * 60)
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(ping_host, h, args.count, args.timeout): h for h in unique}
        for fut in as_completed(futures):
            h = futures[fut]
            try:
                host, ok, lat, msg = fut.result()
                results.append((host, ok, lat, msg))
                sym = "✓" if ok else "✗"
                print(f"{sym} {host:25} | {msg}")
            except Exception as e:
                print(f"✗ {h:25} | {e}")
                results.append((h, False, None, str(e)))
    
    print("-" * 60)
    
    # Summary
    ok_cnt = sum(1 for _, s, _, _ in results if s)
    fail_cnt = len(results) - ok_cnt
    lats = [l for _, _, l, _ in results if l]
    avg = sum(lats) / len(lats) if lats else 0
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total hosts:     {len(results)}")
    print(f"Successful:      {ok_cnt} ({100*ok_cnt/len(results):.1f}%)")
    print(f"Failed:          {fail_cnt} ({100*fail_cnt/len(results):.1f}%)")
    if lats:
        print(f"Avg latency:     {avg:.2f}ms")
    print(f"{'='*60}")
    
    if fail_cnt > 0:
        print("\nFailed hosts:")
        for h, s, _, _ in results:
            if not s:
                print(f"  - {h}")
    
    sys.exit(1 if fail_cnt > 0 else 0)


if __name__ == "__main__":
    main()
