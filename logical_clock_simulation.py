import socket
import threading
import time
import random
import logging
import os
import multiprocessing
from queue import Empty
from datetime import datetime


def setup_logging(machine_id):
    """Set up logging for a virtual machine process"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/machine_{machine_id}.log"

    # Configure logger with a unique name for this machine
    logger = logging.getLogger(f"Machine_{machine_id}")
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create a file handler for this machine's log file
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8", delay=True)
    formatter = logging.Formatter(
        "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def run_machine(machine, duration_seconds):
    """Run a virtual machine in a separate process"""
    try:
        machine.run(duration_seconds)
    except Exception as e:
        logging.error(f"Error in machine {machine.machine_id}: {e}")
        raise


class VirtualMachine:
    def __init__(
        self,
        machine_id,
        clock_rate,
        port,
        other_machines=None,
        internal_event_range=(4, 10),
    ):
        """
        Initialize a virtual machine with a given ID, clock rate, and port.

        Args:
            machine_id: Identifier for this machine
            clock_rate: Number of clock ticks per second (1-6)
            port: Port to listen for incoming messages
            other_machines: List of (host, port) tuples for other machines
            internal_event_range: Tuple (min, max) for internal event random number range
        """
        if not 0 <= port <= 65535:
            raise ValueError("Port must be between 0 and 65535")

        self.machine_id = machine_id
        self.clock_rate = clock_rate
        self.port = port
        self.logical_clock = multiprocessing.Value("i", 0)
        self.message_queue = multiprocessing.Queue()
        self.running = multiprocessing.Value("b", False)
        self.other_machines = other_machines if other_machines else []
        self.internal_event_range = internal_event_range

        # Initialize sockets
        self._setup_sockets()

        # Set up logging for the main process
        self.logger = None

    def _setup_sockets(self):
        """Set up UDP sockets for communication"""
        # Socket for receiving messages
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("localhost", self.port))

        # Client socket for sending messages
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def update_logical_clock(self, received_time=None):
        """Update the logical clock according to Lamport's rules"""
        with self.logical_clock.get_lock():
            if received_time is not None:
                self.logical_clock.value = (
                    max(self.logical_clock.value, received_time) + 1
                )
            else:
                self.logical_clock.value += 1

    def send_message(self, target_machine):
        """Send the current logical clock value to the target machine"""
        with self.logical_clock.get_lock():
            current_clock = self.logical_clock.value
            message = f"{current_clock}"
            self.client_socket.sendto(message.encode(), target_machine)
            self.update_logical_clock()
            if self.logger:
                self.logger.info(
                    f"SEND to {target_machine[1]} - System time: {time.time():.6f}, "
                    f"Logical clock: {self.logical_clock.value}"
                )

    def receive_messages(self):
        """Process function to continuously receive messages"""
        # Set up logging for this process
        self.logger = setup_logging(self.machine_id)

        self.server_socket.settimeout(
            0.1
        )  # Small timeout to allow checking if still running

        while self.running.value:
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
        # Set up logging for this process
        self.logger = setup_logging(self.machine_id)

        self.running.value = True
        self.logger.info(
            f"Starting machine {self.machine_id} with clock rate {self.clock_rate} ticks/second"
        )
        self.logger.info(f"Internal event range: {self.internal_event_range}")

        # Start the message receiver process
        receiver_process = multiprocessing.Process(target=self.receive_messages)
        receiver_process.daemon = True
        receiver_process.start()

        start_time = time.time()

        try:
            while time.time() - start_time < duration_seconds:
                # Calculate sleep time based on clock rate
                sleep_time = 1.0 / self.clock_rate

                try:
                    # Try to get a message with a small timeout
                    received_clock, addr = self.message_queue.get(timeout=0.1)
                    self.update_logical_clock(received_clock)
                    queue_length = 0  # Can't reliably get queue size in multiprocessing
                    self.logger.info(
                        f"RECEIVE from {addr[1]} - System time: {time.time():.6f}, "
                        f"Queue length: {queue_length}, Logical clock: {self.logical_clock.value}"
                    )
                except Empty:
                    # No message available, generate a random action
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
                    elif (
                        self.internal_event_range[0]
                        <= action
                        <= self.internal_event_range[1]
                    ):
                        # Internal event
                        self.update_logical_clock()
                        self.logger.info(
                            f"INTERNAL EVENT - System time: {time.time():.6f}, "
                            f"Logical clock: {self.logical_clock.value}"
                        )
                    else:
                        # For any other value, do nothing (in this case, it's like an internal event)
                        self.update_logical_clock()
                        self.logger.info(
                            f"INTERNAL EVENT - System time: {time.time():.6f}, "
                            f"Logical clock: {self.logical_clock.value}"
                        )

                # Sleep for the remainder of the clock cycle
                time.sleep(sleep_time)

        finally:
            self.running.value = False
            receiver_process.terminate()
            receiver_process.join(timeout=1.0)
            self.server_socket.close()
            self.client_socket.close()
            self.logger.info(f"Machine {self.machine_id} shutdown")


def run_simulation(
    duration_seconds=60, num_machines=3, max_clock_rate=6, internal_event_range=(4, 10)
):
    """Set up and run the simulation with multiple machines"""
    if __name__ != "__main__":
        # When running in a test, we need to use spawn method for process creation
        multiprocessing.set_start_method("spawn", force=True)

    machines = []
    processes = []
    base_port = 5000

    print(f"Starting simulation with {num_machines} machines...")
    print(f"Clock rates will be between 1 and {max_clock_rate}")
    print(f"Internal event range: {internal_event_range}")

    # Reset root logger to avoid interference between runs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    try:
        # Create the virtual machines
        for i in range(num_machines):
            # Random clock rate between 1 and max_clock_rate
            clock_rate = random.randint(1, max_clock_rate)
            port = base_port + i
            machines.append(
                VirtualMachine(
                    i, clock_rate, port, internal_event_range=internal_event_range
                )
            )

        # Connect the machines to each other
        for i, machine in enumerate(machines):
            other_machines = [
                ("localhost", base_port + j) for j in range(num_machines) if j != i
            ]
            machine.other_machines = other_machines

        # Start all machines in separate processes
        for machine in machines:
            process = multiprocessing.Process(
                target=run_machine, args=(machine, duration_seconds)
            )
            processes.append(process)
            process.start()

        # Wait for all processes to finish
        for process in processes:
            process.join()

        # Give a small delay to ensure all file operations are complete
        time.sleep(0.1)

    finally:
        # Ensure all processes are terminated
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)

    print(f"Simulation completed. Check logs in the 'logs' directory.")


if __name__ == "__main__":
    print("Starting distributed system simulation with logical clocks...")
    run_simulation(duration_seconds=60)
