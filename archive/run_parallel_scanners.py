#!/usr/bin/env python3
"""
Parallel Scanner Launcher
Launch 3 independent browser scanner instances
"""

import subprocess
import sys
import time
from datetime import datetime

def launch_scanner_instance(instance_num, scanner_type='sample', sample_size=1000):
    """Launch a single scanner instance"""
    
    if scanner_type == 'sample':
        script = 'browser_sample_scanner.py'
        instance_id = f"sample_{instance_num}"
        
        # Create command with parameters
        cmd = [
            'python3', script
        ]
        
        # Write inputs to file for auto-input
        inputs = f"{sample_size}\n{instance_id}\n"
        
    else:  # comprehensive
        script = 'browser_comprehensive_scanner.py'
        instance_id = f"comp_{instance_num}"
        
        cmd = [
            'python3', script
        ]
        
        # Auto-input for comprehensive scanner
        inputs = f"{instance_id}\n{instance_num}\nyes\n"
    
    print(f"🚀 Launching {scanner_type} scanner instance {instance_num}")
    print(f"   Script: {script}")
    print(f"   Instance ID: {instance_id}")
    
    # Launch process with stdin input
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Send inputs
    try:
        process.stdin.write(inputs)
        process.stdin.flush()
        process.stdin.close()
    except:
        pass
    
    return process, instance_id

def monitor_processes(processes):
    """Monitor running processes"""
    print(f"\n📊 Monitoring {len(processes)} scanner instances...")
    print("=" * 60)
    
    running_processes = [(proc, inst_id) for proc, inst_id in processes]
    
    while running_processes:
        time.sleep(30)  # Check every 30 seconds
        
        still_running = []
        for proc, inst_id in running_processes:
            if proc.poll() is None:  # Still running
                still_running.append((proc, inst_id))
            else:
                return_code = proc.returncode
                print(f"🏁 Instance {inst_id} completed with return code: {return_code}")
        
        running_processes = still_running
        
        if running_processes:
            print(f"⏳ {len(running_processes)} instances still running: {[inst_id for _, inst_id in running_processes]}")
    
    print("✅ All scanner instances completed!")

def main():
    print("🌐 VSDHOne Parallel Scanner Launcher")
    print("=" * 50)
    
    scanner_type = input("Scanner type (sample/comprehensive): ").strip().lower()
    if scanner_type not in ['sample', 'comprehensive']:
        print("❌ Invalid scanner type")
        return
    
    if scanner_type == 'sample':
        sample_size = input("Sample size per instance (default 1000): ").strip()
        if not sample_size:
            sample_size = 1000
        else:
            sample_size = int(sample_size)
        
        print(f"\n🚀 Launching 3 sample scanner instances with {sample_size} samples each")
    else:
        sample_size = None
        print(f"\n🚀 Launching 3 comprehensive scanner instances with predefined ranges")
        print("⚠️  WARNING: Comprehensive scanning is VERY slow (days per instance)")
    
    confirm = input("\nProceed with launching 3 parallel instances? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Launch cancelled")
        return
    
    # Launch instances
    processes = []
    start_time = datetime.now()
    
    print(f"\n🚀 Starting parallel launch at {start_time}")
    
    for i in range(1, 4):  # Launch 3 instances
        try:
            process, instance_id = launch_scanner_instance(i, scanner_type, sample_size)
            processes.append((process, instance_id))
            print(f"   ✅ Instance {i} ({instance_id}) launched successfully")
            time.sleep(2)  # Stagger launches
        except Exception as e:
            print(f"   ❌ Failed to launch instance {i}: {e}")
    
    if not processes:
        print("❌ No instances launched successfully")
        return
    
    print(f"\n✅ Successfully launched {len(processes)} instances")
    print("💡 Each instance runs independently with unique file names")
    print("💡 Use Ctrl+C in each terminal to stop gracefully")
    
    # Monitor processes
    try:
        monitor_processes(processes)
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring interrupted. Processes may still be running.")
        print("Check terminal windows for individual instance status.")

if __name__ == "__main__":
    main() 