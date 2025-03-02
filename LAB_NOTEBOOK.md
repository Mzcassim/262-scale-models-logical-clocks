# Logical Clocks Simulation Lab Notebook

## Project Overview
This project implements a simulation of a distributed system with logical clocks. The system consists of multiple virtual machines that run at different clock rates and communicate with each other using message passing, following the specification provided in the assignment.

## Design Decisions

### Virtual Machine Model
- Each virtual machine runs at a randomly assigned clock rate between 1-6 ticks per second
- Machines have independent logical clocks that are updated according to Lamport's logical clock rules
- Communication between machines is implemented using UDP sockets
- Each machine maintains a queue for incoming messages
- Each machine logs all events to a log file

### Logical Clock Implementation
- The logical clock is implemented as a simple integer counter
- It is updated according to Lamport's rules:
  - On internal events: increment the clock by 1
  - On send events: increment the clock by 1, then send the message
  - On receive events: set the clock to max(local_clock, received_clock) + 1

### Event Processing
- On each clock cycle, a machine either processes a message from its queue or generates a random event
- The probability of different events is controlled by random number generation:
  - 10% chance to send a message to the first machine
  - 10% chance to send a message to the second machine
  - 10% chance to send a message to all other machines
  - 70% chance of an internal event (configurable)

### Logging
- Each machine logs all events with the following information:
  - Event type (INTERNAL, SEND, RECEIVE)
  - System time (for global comparison)
  - Logical clock value
  - For RECEIVE events, the queue length is also logged

## Experimental Results

For each experiment, we ran the simulation for at least 60 seconds and collected logs from all machines. We then analyzed the logs to observe patterns in logical clock behavior, message passing, and queue lengths.

### Experiment 1: Baseline (3 machines, clock rates 1-6, 60 seconds)
- **Event Distribution**: 
  - Machine 0: 329 total events (47.1% INTERNAL, 31.9% SEND, 21.0% RECEIVE)
  - Machine 1: 321 total events (48.0% INTERNAL, 23.4% SEND, 28.7% RECEIVE)
  - Machine 2: 261 total events (31.4% INTERNAL, 30.7% SEND, 37.9% RECEIVE)
- **Queue Performance**:
  - Maximum queue lengths were low: 1.0, 1.0, and 2.0 for machines 0, 1, and 2 respectively
  - Average queue lengths were minimal: 0.01, 0.09, and 0.17
- **Logical Clock Behavior**:
  - Maximum logical clock jumps: 11.0, 9.0, and 12.0
  - Average logical clock jumps: 1.02, 1.04, and 1.28
- **Clock Drift**:
  - Minimal drift between all machines: 1-2 units
  - This suggests the system maintained good synchronization during the baseline run

### Experiment 2: Longer Duration (3 machines, clock rates 1-6, 120 seconds)
- **Event Distribution**:
  - Machine 0: 518 total events (46.9% INTERNAL, 30.9% SEND, 22.2% RECEIVE)
  - Machine 1: 657 total events (52.1% INTERNAL, 36.2% SEND, 11.7% RECEIVE)
  - Machine 2: 120 total events (0% INTERNAL, 0.8% SEND, 99.2% RECEIVE)
- **Queue Performance**:
  - Machine 2 developed a severe queue buildup: maximum 84.0, average 46.45
  - Other machines maintained low queue lengths: 1.0 and 0.0
- **Logical Clock Behavior**:
  - Machine 2 had higher average clock jumps (3.03) compared to others (1.00-1.26)
  - This correlates with the large queue buildup in Machine 2
- **Clock Drift**:
  - Massive drift between Machine 2 and others: 293-295 units
  - Minimal drift between Machine 0 and 1: only 2 units
  - This indicates Machine 2 likely had a much slower clock rate and couldn't keep up with message processing

### Experiment 3: More Machines (5 machines, clock rates 1-6, 60 seconds)
- **Event Distribution**:
  - Highly varied distribution across 5 machines
  - Machine 0 showed extreme imbalance: 98.3% RECEIVE events, only 1.7% INTERNAL events
  - Other machines had more balanced distributions
- **Queue Performance**:
  - Machine 0 developed severe queue buildup: maximum 55.0, average 31.08
  - Other machines maintained low queue lengths, mostly under 1.0
- **Logical Clock Behavior**:
  - Higher maximum jumps across all machines (up to 30.0 for Machine 4)
  - More varied average jumps (1.0 to 3.68)
- **Clock Drift**:
  - Massive drift between Machine 0 and others: 208-216 units
  - Relatively low drift between other machines: 1-8 units
  - The additional communication complexity from more machines led to one machine being overwhelmed

### Experiment 4: Smaller Variation in Clock Cycles (3 machines, clock rates 1-3, 60 seconds)
- **Event Distribution**:
  - More balanced event counts: 122-197 events per machine
  - Machine 2 had more events total (197) compared to others (122-128)
- **Queue Performance**:
  - All machines maintained very low queue lengths: maximum 1.0 across all machines
  - Average queue lengths remained low: 0.09-0.19
- **Logical Clock Behavior**:
  - Smaller maximum logical clock jumps: 6.0-7.0 (compared to 9.0-12.0 in baseline)
  - More consistent average jumps: 1.00-1.60
- **Clock Drift**:
  - Minimal drift between all machines: 0-2 units
  - Machine 1 and Machine 0 had perfect synchronization (0 drift)
  - This demonstrates that more homogeneous clock rates lead to better overall synchronization

### Experiment 5: Lower Probability of Internal Events (3 machines, modified event probability)
- **Event Distribution**:
  - Machine 0: 322 total events (62.1% INTERNAL, 29.5% SEND, 8.4% RECEIVE)
  - Machine 1: 124 total events (33.9% INTERNAL, 15.3% SEND, 50.8% RECEIVE)
  - Machine 2: 130 total events (36.9% INTERNAL, 23.1% SEND, 40.0% RECEIVE)
- **Queue Performance**:
  - Low queue lengths across all machines: maximum 2.0, average under 0.32
- **Logical Clock Behavior**:
  - Higher maximum logical clock jumps: 8.0-16.0
  - Higher average logical clock jumps for some machines: up to 2.57
- **Clock Drift**:
  - Modest drift between machines: 2-5 units
  - Increased communication (fewer internal events) didn't significantly increase drift

## Analysis and Observations

### Logical Clock Jumps
- **Baseline vs. Modified Clock Rates**: When we limited clock rates to 1-3 (Experiment 4), maximum jumps decreased by ~40% (from 9-12 to 6-7). This demonstrates that more homogeneous clock rates lead to smaller logical clock jumps.
- **Impact of System Size**: Adding more machines (Experiment 3) significantly increased maximum jump sizes (up to 30), likely due to increased complexity of the message passing network.
- **Correlation with Queue Length**: Machines with higher queue lengths consistently showed larger average clock jumps. This is logical, as receiving multiple queued messages causes larger jumps when the logical clock catches up to reflect causality.
- **Duration Effects**: In the longer experiment (Experiment 2), Machine 2 developed large jumps due to queue buildup, while machines with manageable queues maintained consistent jump patterns even over longer durations.

### Clock Drift Between Machines
- **Homogeneous vs. Heterogeneous Rates**: The smallest clock variation experiment (Experiment 4) showed near-perfect synchronization with drifts of only 0-2 units. In contrast, the baseline with wider variation had drifts of 1-2 units.
- **Effect of Duration**: Clock drift doesn't necessarily increase linearly with time. In Experiment 2 (longer duration), Machine 0 and 1 maintained a drift of only 2 units after twice the runtime, suggesting some stability in the system.
- **Bottleneck Effects**: In both Experiments 2 and 3, one machine (Machine 2 and Machine 0, respectively) fell dramatically behind, with drifts of 200+ units. This demonstrates how a single slow machine can become a bottleneck in the distributed system.
- **Message Frequency Impact**: Modifying the internal event probability (Experiment 5) didn't significantly impact clock drift (2-5 units), suggesting that the dominant factor is clock rate differences rather than message frequency.

### Impact of Different Timing Parameters
- **Clock Rate Homogeneity**: More homogeneous clock rates led to more balanced event distribution, lower queue lengths, smaller clock jumps, and minimal drift. This is a key finding: reducing the variance in machine speeds significantly improves system stability.
- **Runtime Duration**: Longer runtime (Experiment 2) exposed bottlenecks that weren't apparent in shorter runs. Some machines maintained stability while others fell behind catastrophically, suggesting that stability issues may only emerge over longer periods.
- **Scalability Challenges**: Adding more machines (Experiment 3) increased system complexity and led to greater imbalances, with one machine becoming overwhelmed with receive events.

### Queue Length Analysis
- **Bottleneck Identification**: Across experiments, certain machines developed severe queue buildup (up to 84.0 in Experiment 2 and 55.0 in Experiment 3), while others maintained near-empty queues.
- **Correlation with Clock Rates**: Machines with queue buildups were likely assigned slower clock rates, unable to process incoming messages at the rate they were being sent.
- **Scalability Impact**: Adding more machines increases the likelihood of queue buildup, as seen in Experiment 3 where Machine 0 was overwhelmed with a 55.0 maximum queue length.
- **Homogeneity Benefit**: More homogeneous clock rates (Experiment 4) resulted in balanced queue performance across all machines, with no machine developing significant backlogs.

### Interesting Patterns Observed
- **Critical Slowdown Threshold**: There appears to be a critical threshold where a machine's clock rate becomes too slow relative to others, leading to catastrophic queue buildup. This was observed in both Experiment 2 (Machine 2) and Experiment 3 (Machine 0).
- **Self-Regulating Behavior**: In experiments without severe bottlenecks, machines maintained reasonable synchronization despite different clock rates, suggesting Lamport's algorithm provides inherent stability within certain bounds.
- **Event Type Specialization**: Some machines became specialized in primarily receiving messages (e.g., Machine 2 in Experiment 2 with 99.2% RECEIVE events), while others became balanced or send-heavy.
- **Cascade Effects**: Once a machine falls significantly behind, it tends to process almost exclusively RECEIVE events (over 98% in extreme cases), creating a cascade effect where it falls further behind due to inability to generate SEND or INTERNAL events.

## Comparison to Theoretical Expectations

- **Causal Ordering Preservation**: Lamport's logical clocks successfully maintained causal ordering within each machine, as evidenced by the consistent progression of logical clock values. No machine ever decreased its logical clock value.
- **Expected vs. Observed Drift**: Theoretical expectations would suggest clock drift should increase with time and wider clock rate variations. Our results confirm this, with minimal drift in homogeneous systems and catastrophic drift in heterogeneous systems over longer periods.
- **Queue Behavior**: Classical queueing theory suggests that queues can grow unbounded when arrival rate exceeds service rate. We observed this precisely in machines that likely had slower clock rates, where queue lengths grew substantially over time.
- **Surprising Stability**: Despite having no global synchronization mechanism beyond Lamport's algorithm, machines with comparable clock rates maintained remarkably low drift (0-2 units) even in longer experiments, demonstrating the algorithm's inherent stability properties.

## Conclusions and Reflections

- **Key Insights**:
  1. Clock rate homogeneity is crucial for system stability. Narrower clock rate variations led to more balanced performance, minimal queue buildup, and lower clock drift.
  2. Even with Lamport's logical clocks, significant differences in machine speeds can lead to bottlenecks where some machines fall catastrophically behind.
  3. System behavior can change dramatically over longer durations, with stable short-term behavior evolving into unstable patterns when run longer.
  4. Adding more machines increases system complexity and the likelihood of bottlenecks.

- **Practical Implications**:
  1. Real distributed systems should aim for processing nodes with similar performance characteristics to avoid bottlenecks.
  2. Monitoring queue lengths provides an effective early warning for machines that are falling behind.
  3. Lamport's logical clocks work well within certain bounds of heterogeneity but may not be sufficient when machine speeds vary drastically.
  4. System testing should include extended-duration tests to uncover potential bottlenecks that might not appear in shorter tests.

- **Limitations and Future Work**:
  1. Our simulation used a simple model for message generation. Real systems might have more complex patterns of communication.
  2. We didn't implement flow control or backpressure mechanisms that could help manage queue buildup.
  3. Future experiments could explore dynamic adjustment of machine behavior based on queue length, which might better represent real systems.
  4. Adding network delays and message loss would make the simulation more realistic.

- **Effectiveness of Lamport's Algorithm**:
  Lamport's logical clock algorithm successfully maintained causal ordering within each machine, but it doesn't prevent system-wide bottlenecks when machines operate at significantly different speeds. The algorithm provides a foundation for understanding causality in distributed systems, but practical implementations need additional mechanisms to manage heterogeneity in processing speeds. 