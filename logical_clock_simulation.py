import socket
import threading
import time
import random
import logging
import os
from queue import Queue
from datetime import datetime

class VirtualMachine:
    def __init__(self, machine_id, clock_rate, port, other_machines=None, internal_event_range=(4, 10)):
        """
        Initialize a virtual machine with a given ID, clock rate, and port.
        
        Args:
            machine_id: Identifier for this machine
            clock_rate: Number of clock ticks per second (1-6)
            port: Port to listen for incoming messages
            other_machines: List of (host, port) tuples for other machines
            internal_event_range: Tuple (min, max) for internal event random number range
        """
        self.machine_id = machine_id
        self.clock_rate = clock_rate
        self.port = port
        self.logical_clock = 0
        self.message_queue = Queue()
        self.running = False
        self.other_machines = other_machines if other_machines else []
        self.internal_event_range = internal_event_range
        
        # Set up logging
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/machine_{machine_id}.log"
        
        # Configure logger with a unique name for this machine
        self.logger = logging.getLogger(f"Machine_{machine_id}")
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers (important for multiple runs)
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Create a file handler for this machine's log file
        file_handler = logging.FileHandler(log_file, mode='w')
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Socket for receiving messages
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('localhost', port))
        
        # Client socket for sending messages
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def update_logical_clock(self, received_time=None):
        """Update the logical clock according to Lamport's rules"""
        if received_time is not None:
            self.logical_clock = max(self.logical_clock, received_time) + 1
        else:
            self.logical_clock += 1
    
    def send_message(self, target_machine):
        """Send the current logical clock value to the target machine"""
        message = f"{self.logical_clock}"
        self.client_socket.sendto(message.encode(), target_machine)
        self.update_logical_clock()
        self.logger.info(
            f"SEND to {target_machine[1]} - System time: {time.time():.6f}, "
            f"Logical clock: {self.logical_clock}"
        )
    
    def receive_messages(self):
        """Thread function to continuously receive messages"""
        self.server_socket.settimeout(0.1)  # Small timeout to allow checking if still running
        
        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                received_clock = int(data.decode().strip())
                self.message_queue.put((received_clock, addr))
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
    
    def run(self, duration_seconds=60):
        """Run the virtual machine for the specified duration"""
        self.running = True
        self.logger.info(f"Starting machine {self.machine_id} with clock rate {self.clock_rate} ticks/second")
        self.logger.info(f"Internal event range: {self.internal_event_range}")
        
        # Start the message receiver thread
        receiver_thread = threading.Thread(target=self.receive_messages)
        receiver_thread.daemon = True
        receiver_thread.start()
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds:
                # Calculate sleep time based on clock rate
                sleep_time = 1.0 / self.clock_rate
                
                # Process one message or perform an action
                if not self.message_queue.empty():
                    # Process a message from the queue
                    received_clock, addr = self.message_queue.get()
                    self.update_logical_clock(received_clock)
                    queue_length = self.message_queue.qsize()
                    self.logger.info(
                        f"RECEIVE from {addr[1]} - System time: {time.time():.6f}, "
                        f"Queue length: {queue_length}, Logical clock: {self.logical_clock}"
                    )
                else:
                    # Generate a random action
                    action = random.randint(1, 10)
                    
                    if action == 1 and len(self.other_machines) >= 1:
                        # Send to the first machine
                        self.send_message(self.other_machines[0])
                    elif action == 2 and len(self.other_machines) >= 2:
                        # Send to the second machine
                        self.send_message(self.other_machines[1])
                    elif action == 3 and len(self.other_machines) >= 2:
                        # Send to all other machines
                        for machine in self.other_machines:
                            self.send_message(machine)
                    elif self.internal_event_range[0] <= action <= self.internal_event_range[1]:
                        # Internal event
                        self.update_logical_clock()
                        self.logger.info(
                            f"INTERNAL EVENT - System time: {time.time():.6f}, "
                            f"Logical clock: {self.logical_clock}"
                        )
                    else:
                        # For any other value, do nothing (in this case, it's like an internal event)
                        self.update_logical_clock()
                        self.logger.info(
                            f"INTERNAL EVENT - System time: {time.time():.6f}, "
                            f"Logical clock: {self.logical_clock}"
                        )
                
                # Sleep for the remainder of the clock cycle
                time.sleep(sleep_time)
        
        finally:
            self.running = False
            receiver_thread.join(timeout=1.0)
            self.server_socket.close()
            self.client_socket.close()
            self.logger.info(f"Machine {self.machine_id} shutdown")


def run_simulation(duration_seconds=60, num_machines=3, max_clock_rate=6, internal_event_range=(4, 10)):
    """Set up and run the simulation with multiple machines"""
    machines = []
    base_port = 5000
    
    print(f"Starting simulation with {num_machines} machines...")
    print(f"Clock rates will be between 1 and {max_clock_rate}")
    print(f"Internal event range: {internal_event_range}")
    
    # Reset root logger to avoid interference between runs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create the virtual machines
    for i in range(num_machines):
        # Random clock rate between 1 and max_clock_rate
        clock_rate = random.randint(1, max_clock_rate)
        port = base_port + i
        machines.append(VirtualMachine(i, clock_rate, port, internal_event_range=internal_event_range))
    
    # Connect the machines to each other
    for i, machine in enumerate(machines):
        other_machines = [('localhost', base_port + j) for j in range(num_machines) if j != i]
        machine.other_machines = other_machines
    
    # Start all machines in separate threads
    threads = []
    for machine in machines:
        thread = threading.Thread(target=machine.run, args=(duration_seconds,))
        threads.append(thread)
        thread.start()
    
    # Wait for all machines to finish
    for thread in threads:
        thread.join()
    
    print(f"Simulation completed. Check logs in the 'logs' directory.")


if __name__ == "__main__":
    print("Starting distributed system simulation with logical clocks...")
    run_simulation(duration_seconds=60) 