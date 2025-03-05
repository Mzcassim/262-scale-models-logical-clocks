import pytest
import socket
import multiprocessing
import time
import os
import shutil
from queue import Empty
from logical_clock_simulation import VirtualMachine, run_simulation


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment and clean up after all tests"""
    # Set up multiprocessing
    multiprocessing.set_start_method("spawn", force=True)

    # Clean up logs directory before tests
    log_dir = "logs"
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    yield

    # Clean up after all tests
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)


@pytest.fixture
def clean_logs():
    """Clean up log files before each test that needs it"""
    log_dir = "logs"
    if os.path.exists(log_dir):
        for f in os.listdir(log_dir):
            if f.startswith("machine_"):
                os.remove(os.path.join(log_dir, f))


@pytest.fixture
def vm():
    """Create a basic VirtualMachine instance for testing"""
    machine = VirtualMachine(
        machine_id=1,
        clock_rate=1,
        port=5001,
        other_machines=[("localhost", 5002), ("localhost", 5003)],
    )
    yield machine
    # Cleanup
    machine.server_socket.close()
    machine.client_socket.close()


@pytest.fixture
def connected_vms():
    """Create two connected VirtualMachine instances"""
    vm1 = VirtualMachine(1, 1, 5001, [("localhost", 5002)])
    vm2 = VirtualMachine(2, 1, 5002, [("localhost", 5001)])
    yield vm1, vm2
    # Cleanup
    vm1.server_socket.close()
    vm1.client_socket.close()
    vm2.server_socket.close()
    vm2.client_socket.close()


def test_vm_initialization(vm):
    """Test that VirtualMachine is initialized with correct values"""
    assert vm.machine_id == 1
    assert vm.clock_rate == 1
    assert vm.port == 5001
    assert vm.logical_clock.value == 0
    assert isinstance(vm.message_queue, multiprocessing.queues.Queue)
    assert len(vm.other_machines) == 2
    assert vm.other_machines == [("localhost", 5002), ("localhost", 5003)]


def test_logical_clock_update(vm):
    """Test logical clock updates"""
    # Test internal event update
    initial_clock = vm.logical_clock.value
    vm.update_logical_clock()
    assert vm.logical_clock.value == initial_clock + 1

    # Test update with received time less than current
    with vm.logical_clock.get_lock():
        vm.logical_clock.value = 5
    vm.update_logical_clock(received_time=3)
    assert vm.logical_clock.value == 6  # Should be max(5,3) + 1

    # Test update with received time greater than current
    with vm.logical_clock.get_lock():
        vm.logical_clock.value = 5
    vm.update_logical_clock(received_time=10)
    assert vm.logical_clock.value == 11  # Should be max(5,10) + 1


def test_message_queue(vm):
    """Test message queue functionality"""
    # For multiprocessing Queue, we need to use get with timeout
    test_message = (5, ("localhost", 5002))
    vm.message_queue.put(test_message)

    try:
        received = vm.message_queue.get(timeout=1)
        assert received == test_message
    except Empty:
        pytest.fail("Failed to get message from queue")


def test_socket_binding(vm):
    """Test that sockets are properly bound"""
    assert vm.server_socket.getsockname() == ("127.0.0.1", 5001)
    assert isinstance(vm.client_socket, socket.socket)


def test_multiple_machines():
    """Test creation of multiple machines with different ports"""
    vm1 = VirtualMachine(1, 1, 5001)
    vm2 = VirtualMachine(2, 2, 5002)

    assert vm1.port != vm2.port
    assert vm1.machine_id != vm2.machine_id
    assert vm1.clock_rate != vm2.clock_rate

    # Cleanup
    vm1.server_socket.close()
    vm1.client_socket.close()
    vm2.server_socket.close()
    vm2.client_socket.close()


def test_message_sending(connected_vms, clean_logs):
    """Test sending messages between two machines"""
    vm1, vm2 = connected_vms

    # Start receiver process for vm2
    vm2.running.value = True
    receiver_process = multiprocessing.Process(target=vm2.receive_messages)
    receiver_process.daemon = True
    receiver_process.start()

    # Give some time for the receiver to start
    time.sleep(0.1)

    # Send message from vm1 to vm2
    initial_clock = vm1.logical_clock.value
    vm1.send_message(("localhost", 5002))

    # Give some time for message to be received
    time.sleep(0.1)

    # Check that vm1's clock was incremented
    assert vm1.logical_clock.value == initial_clock + 1

    # Check that vm2 received the message
    try:
        received_clock, addr = vm2.message_queue.get(timeout=1)
        # We only care that we received the message with the correct clock value
        # The source port might be random since it's from an ephemeral port
        assert received_clock == initial_clock
    except Empty:
        pytest.fail("No message received")

    # Cleanup
    vm2.running.value = False
    receiver_process.terminate()
    receiver_process.join(timeout=1.0)


def test_edge_cases():
    """Test edge cases and error conditions"""
    # Test with invalid port (negative)
    with pytest.raises(ValueError):
        VirtualMachine(1, 1, -1)

    # Test with invalid port (too large)
    with pytest.raises(ValueError):
        VirtualMachine(1, 1, 65536)

    # Test with invalid clock rate
    vm = VirtualMachine(1, 0, 5001)
    assert vm.clock_rate == 0
    vm.server_socket.close()
    vm.client_socket.close()


def test_internal_event_range():
    """Test different internal event ranges"""
    vm = VirtualMachine(1, 1, 5001, internal_event_range=(1, 3))
    assert vm.internal_event_range == (1, 3)
    vm.server_socket.close()
    vm.client_socket.close()


def test_short_simulation(clean_logs):
    """Test running a short simulation"""
    # Run a very short simulation with 2 machines
    run_simulation(duration_seconds=2, num_machines=2, max_clock_rate=2)

    # Give some time for log files to be written and processes to clean up
    time.sleep(1)

    # Check that log files were created
    assert os.path.exists("logs/machine_0.log")
    assert os.path.exists("logs/machine_1.log")

    # Check log file contents
    with open("logs/machine_0.log", "r", encoding="utf-8") as f:
        log_contents = f.read()
        assert "Starting machine 0" in log_contents
        assert "shutdown" in log_contents


@pytest.mark.skip(reason="Long running test")
def test_full_simulation(clean_logs):
    """Test running a full simulation (skipped by default)"""
    run_simulation(
        duration_seconds=5,
        num_machines=3,
        max_clock_rate=6,
        internal_event_range=(4, 10),
    )
    # Add assertions about simulation results if needed
