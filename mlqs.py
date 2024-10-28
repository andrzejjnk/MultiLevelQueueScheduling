import asyncio
import random
import numpy as np
import time
from typing import Dict, List, Tuple, Optional
from plots import plot_results, plot_average_wait_time


class Process:
    def __init__(self, name: str, burst_time: int) -> None:
        self.name = name
        self.burst_time = burst_time
        self.remaining_time = burst_time  # Initially, remaining time equals burst time

    def __repr__(self) -> str:
        return f"{self.name}(BT: {self.burst_time}, RT: {self.remaining_time})"

class ProcessQueue:
    def __init__(self, name: str, algorithm: str) -> None:
        """
        Initialize a queue for processing tasks.

        Args:
            name (str): Name of the queue.
            algorithm (str): Algorithm used for CPU scheduling (e.g., FIFO, Round Robin).
        """
        self.name = name
        self.queue = asyncio.Queue()  # Queue of processes for processing
        self.new_process_count = 0
        self.wait_times: List[float] = []  # List of process wait times
        self.timestamps: List[float] = []   # Timestamps for when processes are added to the queue
        self.algorithm = algorithm

    async def add_process(self, process: Process) -> None:
        """
        Add a process to the queue and record the entry timestamp.

        Args:
            process (str): Name or ID of the process.
        """
        await self.queue.put(process)
        self.new_process_count += 1
        timestamp = time.time()
        self.timestamps.append(timestamp)
        print(f'Process {process} added to {self.name} queue')

    async def get_process(self) -> str:
        """
        Retrieve a process from the queue and calculate the wait time.

        Returns:
            str: The process retrieved from the queue.
        """
        process = await self.queue.get()
        wait_time = time.time() - self.timestamps.pop(0)
        self.wait_times.append(wait_time)
        print(f'Process {process} leaving {self.name} queue. Wait time: {wait_time:.2f} s')
        return process

    async def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        return self.queue.empty()


class CPU:
    def __init__(self, id: int, speedup: int, burst_time: int) -> None:
        """
        Initialize a CPU for task processing.

        Args:
            id (int): Unique identifier for the CPU.
            speedup (int): Factor by which CPU execution time is adjusted.
        """
        self.id = id
        self.is_free = True  # CPU status
        self.completed_process_count = 0  # Count of completed processes
        self.execution_times: List[float] = []  # List of process execution times
        self.speedup = speedup
        self.burst_time = burst_time

    async def execute_process(self, priority, process: Process) -> None:
        """
        Simulate executing a process on the CPU.

        Args:
            process (Process): The Process object to be executed.
        """
        process_time = min(process.remaining_time, self.burst_time)
        adjusted_time = process_time / self.speedup

        print(f'CPU {self.id} starts executing process: {process.name} (remaining time: {process.remaining_time} seconds)')
        
        await asyncio.sleep(adjusted_time)
        
        # Update remaining time after execution
        process.remaining_time -= process_time

        print(f'CPU {self.id} completed executing process: {process.name}, remaining time: {process.remaining_time}')
        self.is_free = True
        self.completed_process_count += 1
        self.execution_times.append(process_time)



class MultiLevelQueueScheduler:
    def __init__(self, num_cpus: int, total_processes: int, speedup_simulation: int = 1, time_quantum: int = 2, burst_time=3) -> None:
        """
        Initialize the multi-level queue scheduler with specified CPU count and settings.

        Args:
            num_cpus (int): Number of CPUs available.
            speedup_simulation (int): Factor to speed up simulation execution times.
            time_quantum (int): Time quantum for Round Robin scheduling.
        """
        self.time_quantum = time_quantum
        self.queues: Dict[str, ProcessQueue] = {
            'Real Time': ProcessQueue("Real-Time", "FIFO"),
            'System': ProcessQueue("System", "Round Robin"),
            'Interactive': ProcessQueue("Interactive", "SJF"),
            'Batch': ProcessQueue("Batch", "FIFO"),
            'Low Priority': ProcessQueue("Low Priority", "Round Robin")
        }
        self.cpus: List[CPU] = [CPU(i, speedup_simulation, burst_time) for i in range(num_cpus)]
        self.completed_processes = 0
        self.cpu_usage_data: List[List[int]] = [[] for _ in range(num_cpus)]
        self.queue_fill_data: Dict[str, List[int]] = {key: [] for key in self.queues}
        self.speedup_simulation = speedup_simulation
        self.burst_time = burst_time
        self.total_processes = total_processes

    async def schedule_process(self, priority: str, name: str, burst_time: int) -> None:
        """
        Schedule a process by adding it to the appropriate queue.

        Args:
            priority (str): Priority level of the process.
            process (str): Name or ID of the process.
        """
        process = Process(name, burst_time)
        queue = self.queues[priority]
        await queue.add_process(process)

    async def execute_and_count(self, cpu: CPU, priority: str, process: Process) -> None:
        """
        Execute a process on a specified CPU and update completion count.

        Args:
            cpu (CPU): The CPU executing the process.
            priority (str): The priority level of the process.
            process (str): Name or ID of the process.
        """
        await cpu.execute_process(priority, process)
        self.completed_processes += 1

    async def run_scheduler(self) -> Tuple[List[List[int]], Dict[str, List[int]], Dict[str, float]]:
        """
        Run the scheduler, managing processes across multiple queues and CPUs.

        Returns:
            Tuple containing:
                - CPU usage data
                - Queue fill data
                - Average wait times per queue
        """
        round_robin_counters = {key: 0 for key in self.queues if self.queues[key].algorithm == "Round Robin"}
        
        while True:
            all_empty = True
            for priority, queue in self.queues.items():
                if not await queue.is_empty():
                    all_empty = False
                    process = None

                    if queue.algorithm == "Round Robin":
                        process = await self.get_rr_process(queue)
                        round_robin_counters[priority] += 1
                    elif queue.algorithm == "FIFO":
                        process = await queue.get_process()
                    elif queue.algorithm == "SJF":
                        process = await self.get_sjf_process(queue)

                    if process:
                        available_cpu = next((cpu for cpu in self.cpus if cpu.is_free), None)
                        if available_cpu:
                            available_cpu.is_free = False
                            asyncio.create_task(self.execute_and_count(available_cpu, priority, process))
                        else:
                            await queue.add_process(process)

                for i, cpu in enumerate(self.cpus):
                    self.cpu_usage_data[i].append(0 if cpu.is_free else 1)

            for priority, queue in self.queues.items():
                self.queue_fill_data[priority].append(queue.queue.qsize())

            if all_empty and self.completed_processes == self.total_processes:
                print("All processes have been completed.")
                break

            await asyncio.sleep(1)

        return self.cpu_usage_data, self.queue_fill_data, self.average_wait_times()
    
    def get_process_time(self, process: str) -> int:
        """
        Retrieve the execution time for a given process based on its type.

        Args:
            process (str): The name or ID of the process.

        Returns:
            int: The estimated execution time for the process.
        """

        return self.burst_time

    async def get_rr_process(self, queue: ProcessQueue) -> Optional[Process]:
        """
        Retrieve and process the next Round Robin task from the queue.

        Args:
            queue (ProcessQueue): The queue from which to retrieve the process.

        Returns:
            Optional[Process]: The Process object being executed.
        """
        process = await queue.get_process()
        
        # Check if the process can be completed
        if process.remaining_time <= self.time_quantum:
            print(f'Process {process.name} has completed execution.')
            return process  # Process completed successfully

        # If remaining time exceeds time quantum, attempt to execute
        while process.remaining_time > 0:
            time_to_run = min(process.remaining_time, self.time_quantum)
            process.remaining_time -= time_to_run
            
            print(f'Process {process.name} needs more time, {process.remaining_time} seconds remain, staying in queue.')
            await queue.add_process(process)  # Re-add process to the queue
            return None  # Return None to indicate it needs to be processed again later

        print(f'Process {process.name} could not be completed. Marking as complete or moving to another queue.')
        self.completed_processes += 1  # Mark as completed
        return process  # Return the process that was skipped


    async def get_sjf_process(self, queue: ProcessQueue) -> Optional[Process]:
        """
        Retrieve the shortest job from the queue.

        Args:
            queue (ProcessQueue): The queue from which to retrieve the process.

        Returns:
            Optional[Process]: The shortest Process object.
        """
        processes = [await queue.get_process() for _ in range(queue.queue.qsize())]
        if not processes:
            return None

        # Sort processes based on burst time
        processes.sort(key=lambda p: p.burst_time)
        selected_process = processes[0]
        
        # Re-add the remaining processes back into the queue
        for process in processes:
            if process != selected_process:
                await queue.add_process(process)

        return selected_process


    def average_wait_times(self) -> Dict[str, float]:
        """
        Calculate average wait times for each queue.

        Returns:
            Dict[str, float]: A dictionary with average wait times for each queue.
        """
        return {key: np.mean(queue.wait_times) if queue.wait_times else 0 for key, queue in self.queues.items()}


async def add_processes(scheduler: MultiLevelQueueScheduler, total_processes: int, processes_per_second: int, burst_time: int, interactive_burst_time_range: tuple, use_random_interactive_burst: bool) -> None:
    """
    Continuously add processes to the scheduler with configurable burst times.

    Args:
        scheduler (MultiLevelQueueScheduler): The scheduler to which processes will be added.
        total_processes (int): Total number of processes to add.
        processes_per_second (int): Number of processes to add per second.
        burst_time (int): Default burst time for non-interactive processes.
        interactive_burst_time_range (tuple): Min and max burst time for Interactive processes.
        use_random_interactive_burst (bool): If True, assigns random burst time within range for Interactive processes.
    """
    for i in range(total_processes):
        await asyncio.sleep(1 / processes_per_second)
        process_name = f'Process_{i + 1}'
        priority = random.choice(list(scheduler.queues.keys()))

        if priority == "Interactive" and use_random_interactive_burst:
            process_burst_time = random.randint(interactive_burst_time_range[0], interactive_burst_time_range[1])
        else:
            process_burst_time = burst_time

        await scheduler.schedule_process(priority, process_name, process_burst_time)
