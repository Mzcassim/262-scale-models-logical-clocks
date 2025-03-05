import pytest
import socket
from queue import Queue
from logical_clock_simulation import VirtualMachine


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


def test_vm_initialization(vm):
    """Test that VirtualMachine is initialized with correct values"""
    assert vm.machine_id == 1
    assert vm.clock_rate == 1
    assert vm.port == 5001
    assert vm.logical_clock == 0
    assert isinstance(vm.message_queue, Queue)
    assert len(vm.other_machines) == 2
    assert vm.other_machines == [("localhost", 5002), ("localhost", 5003)]


def test_logical_clock_update(vm):
    """Test logical clock updates"""
    # Test internal event update
    initial_clock = vm.logical_clock
    vm.update_logical_clock()
    assert vm.logical_clock == initial_clock + 1

    # Test update with received time less than current
    vm.logical_clock = 5
    vm.update_logical_clock(received_time=3)
    assert vm.logical_clock == 6  # Should be max(5,3) + 1

    # Test update with received time greater than current
    vm.logical_clock = 5
    vm.update_logical_clock(received_time=10)
    assert vm.logical_clock == 11  # Should be max(5,10) + 1


def test_message_queue(vm):
    """Test message queue functionality"""
    assert vm.message_queue.empty()
    test_message = (5, ("localhost", 5002))
    vm.message_queue.put(test_message)
    assert not vm.message_queue.empty()
    assert vm.message_queue.get() == test_message


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
