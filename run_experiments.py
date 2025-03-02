import os
import subprocess
import time
import shutil
import traceback
import logging
from logical_clock_simulation import run_simulation
from analyze_results import analyze_run

def run_experiment(experiment_name, duration_seconds=60, num_machines=3, **kwargs):
    """Run a simulation experiment with the given parameters"""
    print(f"\n=== Running experiment: {experiment_name} ===")
    print(f"Duration: {duration_seconds} seconds, Machines: {num_machines}")
    
    # Make sure logs directory exists and is empty
    if os.path.exists('logs'):
        shutil.rmtree('logs')
    os.makedirs('logs', exist_ok=True)
    
    # Create a directory for this experiment
    experiment_dir = f"experiment_{experiment_name}"
    
    try:
        # Run the simulation
        run_simulation(duration_seconds, num_machines, **kwargs)
        
        # Check if log files were created
        log_files = [f for f in os.listdir('logs') if f.startswith('machine_') and f.endswith('.log')]
        if not log_files:
            print(f"Warning: No log files were created for experiment: {experiment_name}")
            
        # Rename logs directory to experiment directory
        if os.path.exists(experiment_dir):
            shutil.rmtree(experiment_dir)
        os.rename('logs', experiment_dir)
        os.makedirs('logs', exist_ok=True)  # Create a new logs dir for future runs
        
        # Analyze the results
        print(f"\nAnalyzing results for experiment: {experiment_name}")
        analyze_run(experiment_dir)
        
        return experiment_dir
        
    except Exception as e:
        print(f"Error running experiment {experiment_name}: {e}")
        traceback.print_exc()
        
        # Ensure logs directory exists for next experiment
        if os.path.exists('logs'):
            if os.path.exists(experiment_dir):
                shutil.rmtree(experiment_dir)
            os.rename('logs', experiment_dir)
        os.makedirs('logs', exist_ok=True)
        
        return experiment_dir

def main():
    """Run a series of experiments with different configurations"""
    # Create a directory for analysis results
    os.makedirs('analysis', exist_ok=True)
    
    experiment_dirs = []
    
    # Experiment 1: Default parameters (baseline)
    # 3 machines with clock rates 1-6, running for 60 seconds
    exp_dir = run_experiment(
        experiment_name="baseline", 
        duration_seconds=60, 
        num_machines=3
    )
    experiment_dirs.append(exp_dir)
    
    # Experiment 2: Longer duration
    exp_dir = run_experiment(
        experiment_name="longer_duration", 
        duration_seconds=120, 
        num_machines=3
    )
    experiment_dirs.append(exp_dir)
    
    # Experiment 3: More machines
    exp_dir = run_experiment(
        experiment_name="more_machines", 
        duration_seconds=60, 
        num_machines=5
    )
    experiment_dirs.append(exp_dir)
    
    # Experiment 4: Smaller variation in clock cycles (1-3 instead of 1-6)
    exp_dir = run_experiment(
        experiment_name="smaller_clock_variation", 
        duration_seconds=60, 
        num_machines=3,
        max_clock_rate=3  # This parameter will be used in modified run_simulation
    )
    experiment_dirs.append(exp_dir)
    
    # Experiment 5: Lower probability of internal events (1-5 instead of 4-10)
    exp_dir = run_experiment(
        experiment_name="lower_internal_probability", 
        duration_seconds=60, 
        num_machines=3,
        internal_event_range=(4, 5)  # This parameter will be used in modified run_simulation
    )
    experiment_dirs.append(exp_dir)
    
    print("\n=== Experiments completed ===")
    print("Experiment directories:")
    for exp_dir in experiment_dirs:
        print(f"  {exp_dir}")

if __name__ == "__main__":
    main() 