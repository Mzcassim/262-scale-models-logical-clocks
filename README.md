# Logical Clocks Simulation

This project implements a simulation of a small, asynchronous distributed system with logical clocks. It models multiple virtual machines running at different speeds on a single physical machine, communicating through message passing and maintaining logical clock synchronization according to Lamport's logical clock algorithm.

## Project Overview

The simulation models:
- Multiple virtual machines running asynchronously at different clock rates
- Communication between machines via message passing
- Logical clocks that follow Lamport's rules for synchronization
- Message queues for each machine to handle incoming messages
- Various event types: internal events, sending messages, and receiving messages

## Implementation Details

Each virtual machine in the simulation:

1. **Clock Rate**: Runs at a randomly assigned clock rate between 1-6 ticks per second.
2. **Communication**: Connects to all other virtual machines via UDP sockets.
3. **Message Queue**: Maintains a queue for incoming messages that operate independently of the machine's clock rate.
4. **Logical Clock**: Updates according to Lamport's rules:
   - Internal event: Increment clock by 1
   - Send event: Increment clock by 1, then send the message
   - Receive event: Set clock to max(local_clock, received_clock) + 1
5. **Logging**: Records all events with timestamps, logical clock values, and other relevant data

On each clock cycle, a virtual machine:

1. Checks its message queue for incoming messages:
   - If a message is present, processes it, updates its logical clock, and logs the event with global time, queue length, and updated logical clock value
   - If no message is present, generates a random number (1-10) to determine action:
     - 1: Send a message to the first machine
     - 2: Send a message to the second machine
     - 3: Send a message to all other machines
     - 4-10: Process as an internal event

## Project Structure

- `logical_clock_simulation.py`: Main simulation code with VirtualMachine class
- `analyze_results.py`: Script to analyze log data from simulation runs
- `run_experiments.py`: Script to run multiple experiments with different configurations
- `LAB_NOTEBOOK.md`: Documentation of design decisions and experimental observations

## Requirements

- Python 3.7+
- Required packages:
  - pandas
  - matplotlib
  - numpy

You can install the required packages with:

```
pip install -r requirements.txt
```

## Running the Simulation

### Basic Simulation

To run a basic simulation with the default configuration:

```
python logical_clock_simulation.py
```

This will:
- Create 3 virtual machines with random clock rates (1-6 ticks/second)
- Run the simulation for 60 seconds
- Generate log files in the `logs` directory

### Running Experiments

To run multiple experiments with different configurations (as required for the lab notebook):

```
python run_experiments.py
```

This will run a series of experiments:
1. **Baseline**: 3 machines, clock rates 1-6, 60 seconds
2. **Longer Duration**: 3 machines, clock rates 1-6, 120 seconds
3. **More Machines**: 5 machines, clock rates 1-6, 60 seconds
4. **Smaller Clock Variation**: 3 machines, clock rates 1-3, 60 seconds
5. **Lower Internal Probability**: 3 machines, modified probability of internal events

### Analyzing Results

After running a simulation or experiment, analyze the results:

```
python analyze_results.py
```

The analysis script provides:
- Options to analyze a specific experiment directory or all experiments
- Detailed statistics for each machine (event counts, queue lengths, clock jumps)
- Visualizations of logical clock progression
- Analysis of clock drift between machines

## Configurable Parameters

- `duration_seconds`: Duration of the simulation in seconds
- `num_machines`: Number of virtual machines to simulate
- `max_clock_rate`: Maximum clock rate for the virtual machines (1-6 seconds by default)
- `internal_event_range`: Range for determining internal event probability

## Lab Notebook

The `LAB_NOTEBOOK.md` file contains:
- Documentation of design decisions
- Observations from running experiments
- Analysis of logical clock jumps
- Analysis of clock drift between machines
- Observations on message queue lengths
- Effects of varying clock rates and event probabilities

## Fulfillment of Requirements

The implementation fulfills all assignment requirements:
- ✅ Models multiple machines running at different speeds (1-6 ticks/second)
- ✅ Each machine has a network queue for incoming messages
- ✅ Machines communicate via sockets
- ✅ Each machine logs events to its own log file
- ✅ Machines implement Lamport's logical clock algorithm
- ✅ On each clock cycle, machines either process a message or generate a random event
- ✅ Provides tools to run multiple experiments and analyze results
- ✅ Lab notebook documents observations and findings