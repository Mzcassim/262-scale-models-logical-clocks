import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import time
import sys
import glob

def parse_log_file(log_file):
    """Parse a machine log file and extract timestamp, event type, and logical clock values"""
    data = []
    
    with open(log_file, 'r') as f:
        for line in f:
            # Parse timestamp - handle various timestamp formats
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\w+)?', line)
            if not timestamp_match:
                continue
            
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Skip startup and configuration lines
            if "Starting machine" in line or "Internal event range" in line or "shutdown" in line:
                continue
            
            # Extract system time
            system_time_match = re.search(r'System time: (\d+\.\d+)', line)
            if system_time_match:
                system_time = float(system_time_match.group(1))
            else:
                system_time = None
                continue  # Skip lines without system time
            
            # Extract event type
            if "INTERNAL EVENT" in line:
                event_type = "INTERNAL"
            elif "SEND to" in line:
                event_type = "SEND"
                # Extract target
                target_match = re.search(r'SEND to (\d+)', line)
                if target_match:
                    target = int(target_match.group(1))
                else:
                    target = None
            elif "RECEIVE from" in line:
                event_type = "RECEIVE"
                # Extract source
                source_match = re.search(r'RECEIVE from (\d+)', line)
                if source_match:
                    source = int(source_match.group(1))
                else:
                    source = None
                
                # Extract queue length
                queue_match = re.search(r'Queue length: (\d+)', line)
                if queue_match:
                    queue_length = int(queue_match.group(1))
                else:
                    queue_length = None
            else:
                continue  # Skip lines with unknown event types
            
            # Extract logical clock
            clock_match = re.search(r'Logical clock: (\d+)', line)
            if clock_match:
                logical_clock = int(clock_match.group(1))
            else:
                continue  # Skip lines without logical clock
            
            # Create data entry
            entry = {
                'timestamp': timestamp,
                'system_time': system_time,
                'event_type': event_type,
                'logical_clock': logical_clock
            }
            
            # Add event-specific fields
            if event_type == "SEND":
                entry['target'] = target
            elif event_type == "RECEIVE":
                entry['source'] = source
                entry['queue_length'] = queue_length
            
            data.append(entry)
    
    # Create a DataFrame with default columns even if data is empty
    if not data:
        print(f"Warning: No valid log entries found in {log_file}")
        return pd.DataFrame(columns=['timestamp', 'system_time', 'event_type', 'logical_clock'])
    
    return pd.DataFrame(data)

def analyze_log_data(machine_dfs, run_name=""):
    """Analyze the log data from multiple machines"""
    print(f"=== Analysis for run: {run_name} ===")
    
    empty_data = True
    
    # Print basic statistics for each machine
    for machine_id, df in machine_dfs.items():
        print(f"\nMachine {machine_id} Statistics:")
        if df.empty:
            print(f"  No events recorded (empty log)")
            continue
            
        empty_data = False
        print(f"  Total events: {len(df)}")
        
        if 'event_type' in df.columns:
            event_counts = df['event_type'].value_counts()
            for event_type, count in event_counts.items():
                print(f"  {event_type} events: {count} ({count/len(df)*100:.1f}%)")
        else:
            print("  Warning: No event type data found in log")
        
        if 'queue_length' in df.columns and not df['queue_length'].isna().all():
            max_queue = df['queue_length'].max()
            avg_queue = df['queue_length'].mean()
            print(f"  Maximum queue length: {max_queue}")
            print(f"  Average queue length: {avg_queue:.2f}")
        
        # Calculate logical clock jumps
        if len(df) > 1 and 'logical_clock' in df.columns:
            df = df.sort_values('timestamp')
            df['clock_jump'] = df['logical_clock'].diff()
            max_jump = df['clock_jump'].max()
            avg_jump = df['clock_jump'].mean()
            print(f"  Maximum logical clock jump: {max_jump}")
            print(f"  Average logical clock jump: {avg_jump:.2f}")
    
    if empty_data:
        print("\nNo valid data found for analysis. Check log files or run duration.")
        return
    
    # Plot logical clock values over time for all machines
    plt.figure(figsize=(12, 6))
    
    for machine_id, df in machine_dfs.items():
        if df.empty or 'logical_clock' not in df.columns or 'system_time' not in df.columns:
            continue
            
        df = df.sort_values('timestamp')
        plt.plot(df['system_time'], df['logical_clock'], label=f'Machine {machine_id}')
    
    plt.xlabel('System Time (s)')
    plt.ylabel('Logical Clock Value')
    plt.title(f'Logical Clock Progression - {run_name}')
    plt.legend()
    plt.grid(True)
    
    # Save the plot
    os.makedirs('analysis', exist_ok=True)
    plt.savefig(f'analysis/logical_clock_progression_{run_name}.png')
    
    # Calculate clock drift between machines
    machines_with_data = [m for m, df in machine_dfs.items() 
                         if not df.empty and 'logical_clock' in df.columns]
    
    if len(machines_with_data) > 1:
        print("\nClock Drift Analysis:")
        
        for i in range(len(machines_with_data)):
            for j in range(i+1, len(machines_with_data)):
                machine_a = machines_with_data[i]
                machine_b = machines_with_data[j]
                
                # Get final logical clock values
                final_a = machine_dfs[machine_a].sort_values('timestamp').iloc[-1]['logical_clock']
                final_b = machine_dfs[machine_b].sort_values('timestamp').iloc[-1]['logical_clock']
                
                drift = abs(final_a - final_b)
                print(f"  Drift between Machine {machine_a} and Machine {machine_b}: {drift}")

def analyze_run(run_dir):
    """Analyze all machine logs for a specific run"""
    machine_dfs = {}
    
    log_files_found = False
    for log_file in os.listdir(run_dir):
        if log_file.startswith('machine_') and log_file.endswith('.log'):
            log_files_found = True
            machine_id = int(log_file.split('_')[1].split('.')[0])
            log_path = os.path.join(run_dir, log_file)
            
            # Check if file is empty
            if os.path.getsize(log_path) == 0:
                print(f"Warning: Log file {log_file} is empty")
                machine_dfs[machine_id] = pd.DataFrame(columns=['timestamp', 'system_time', 'event_type', 'logical_clock'])
                continue
                
            try:
                df = parse_log_file(log_path)
                machine_dfs[machine_id] = df
            except Exception as e:
                print(f"Error parsing log file {log_file}: {e}")
                machine_dfs[machine_id] = pd.DataFrame(columns=['timestamp', 'system_time', 'event_type', 'logical_clock'])
    
    if not log_files_found:
        print(f"No log files found in directory: {run_dir}")
        return
        
    run_name = os.path.basename(run_dir)
    analyze_log_data(machine_dfs, run_name)

def find_experiment_dirs():
    """Find experiment directories in the current directory"""
    experiment_dirs = []
    
    # Look for experiment_* directories
    for dir_name in os.listdir('.'):
        if os.path.isdir(dir_name) and (dir_name.startswith('experiment_') or dir_name.startswith('logs_')):
            experiment_dirs.append(dir_name)
    
    return sorted(experiment_dirs)

def main():
    """Main function to analyze results from multiple runs"""
    # Check for command line arguments
    if len(sys.argv) > 1:
        # If a directory was specified, analyze that
        run_dir = sys.argv[1]
        if os.path.isdir(run_dir):
            print(f"Analyzing specified directory: {run_dir}")
            analyze_run(run_dir)
        else:
            print(f"Error: Specified directory '{run_dir}' not found.")
        return
    
    # If 'logs' directory exists, process it
    if os.path.exists('logs'):
        # Check if there are any log files in the logs directory
        log_files = glob.glob('logs/machine_*.log')
        if log_files:
            print("Found active logs directory. Analyzing...")
            # Create a directory for this analysis run
            timestamp = int(time.time())
            run_dir = f"logs_{timestamp}"
            os.rename('logs', run_dir)
            os.makedirs('logs', exist_ok=True)  # Create a new logs dir for future runs
            analyze_run(run_dir)
            return
        else:
            print("Logs directory exists but contains no log files.")
    
    # If we get here, there was no 'logs' directory with log files
    # Look for experiment directories to analyze
    experiment_dirs = find_experiment_dirs()
    
    if not experiment_dirs:
        print("No logs or experiment directories found.")
        print("Please run the simulation first with 'python logical_clock_simulation.py'")
        print("Or specify a directory to analyze: 'python analyze_results.py <directory>'")
        return
    
    # Ask user which directory to analyze
    print("Found the following experiment directories:")
    for i, dir_name in enumerate(experiment_dirs):
        print(f"{i+1}. {dir_name}")
    
    try:
        choice = input("Enter the number of the directory to analyze (or 'all' to analyze all): ")
        
        if choice.lower() == 'all':
            for dir_name in experiment_dirs:
                print(f"\nAnalyzing {dir_name}...")
                analyze_run(dir_name)
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(experiment_dirs):
                    analyze_run(experiment_dirs[index])
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input. Please enter a number or 'all'.")
    except KeyboardInterrupt:
        print("\nAnalysis cancelled.")

if __name__ == "__main__":
    main() 