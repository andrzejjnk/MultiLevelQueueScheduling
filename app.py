import asyncio
import random
import streamlit as st
import os
from mlqs import MultiLevelQueueScheduler, add_processes
from plots import plot_results, plot_average_wait_time

async def run_simulation_dynamic(num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time, interactive_burst_time_range, use_random_interactive_burst, time_quantum):
    """
    Run a dynamic simulation of the multi-level queue scheduler.

    Args:
        num_cpus (int): Number of CPUs available for the scheduler.
        total_processes (int): Total number of processes to be added dynamically.
        processes_per_second (int): Rate at which processes are added per second.
        speedup_simulation (int): Factor to speed up the simulation.
        burst_time (int): Default burst time for each process.
        interactive_burst_time_range (tuple): Min and max burst time for Interactive processes.
        use_random_interactive_burst (bool): Whether to use random burst time within range for Interactive processes.

    Returns:
        tuple: Contains cpu_usage_data, queue_fill_data, and average_wait_times.
    """
    scheduler = MultiLevelQueueScheduler(num_cpus, total_processes, speedup_simulation, burst_time, time_quantum)
    asyncio.create_task(add_processes(scheduler, total_processes, processes_per_second, burst_time, interactive_burst_time_range, use_random_interactive_burst))
    cpu_usage_data, queue_fill_data, average_wait_times = await scheduler.run_scheduler()
    return cpu_usage_data, queue_fill_data, average_wait_times


async def run_simulation_static(num_cpus, speedup_simulation, process_settings, time_quantum, interactive_burst_time_range=None, use_random_interactive_burst=False):
    """
    Run a static simulation of the multi-level queue scheduler.

    Args:
        num_cpus (int): Number of CPUs available for the scheduler.
        speedup_simulation (int): Factor to speed up the simulation.
        process_settings (dict): Dictionary containing process counts and burst times for each queue type.
        interactive_burst_time_range (tuple, optional): Min and max burst time for Interactive processes.
        use_random_interactive_burst (bool): If True, assigns random burst time within range for Interactive processes.

    Returns:
        tuple: Contains cpu_usage_data, queue_fill_data, and average_wait_times.
    """
    scheduler = MultiLevelQueueScheduler(num_cpus, sum(settings["count"] for settings in process_settings.values()), speedup_simulation, time_quantum=time_quantum)

    for priority, settings in process_settings.items():
        for i in range(settings["count"]):
            process_name = f"{priority}_Process_{i + 1}"
            
            if priority == "Interactive" and use_random_interactive_burst:
                burst_time = random.randint(interactive_burst_time_range[0], interactive_burst_time_range[1])
            else:
                burst_time = settings["burst_time"]
            
            await scheduler.schedule_process(priority, process_name, burst_time)

    cpu_usage_data, queue_fill_data, average_wait_times = await scheduler.run_scheduler()
    return cpu_usage_data, queue_fill_data, average_wait_times



def main():
    """
    Streamlit main function for the multi-level queue scheduler simulation.
    Initializes the simulation parameters based on user input and runs the simulation.

    The interface displays the mode selection for adding processes (Dynamic or Static),
    common settings (number of CPUs, speedup factor), and displays fields based on the selected mode.
    Finally, it displays the simulation results as plots.
    """
    st.title("Multi-Level Queue Scheduler Simulation")

    mode = st.radio("Select Process Adding Mode:", ("Dynamic", "Static"))

    num_cpus = st.number_input("Number of CPUs", min_value=1, max_value=4, value=2)
    speedup_simulation = st.number_input("Speedup Simulation Factor", min_value=1, max_value=100, value=20)
    time_quantum = st.number_input("Time quantum", min_value=1, max_value=5, value=2)

    if mode == "Dynamic":
        total_processes = st.number_input("Total Processes", min_value=1, max_value=300, value=44)
        processes_per_second = st.number_input("Processes Per Second", min_value=1, max_value=50, value=10)
        burst_time = st.number_input("Default Burst Time for Processes", min_value=1, max_value=10, value=3)

    elif mode == "Static":
        process_settings = {}
        total_processes = 0

        for priority in ["Real Time", "System", "Interactive", "Batch", "Low Priority"]:
            with st.expander(f"{priority} Queue Settings"):
                process_count = st.number_input(f"Number of {priority} Processes", min_value=0, max_value=100, value=5)
                burst_time = st.number_input(f"Burst Time for {priority} Processes", min_value=1, max_value=10, value=3)

                process_settings[priority] = {"count": process_count, "burst_time": burst_time}
                total_processes += process_count


    st.subheader("Interactive Process Burst Time Settings")
    use_random_interactive_burst = st.checkbox("Use Random Burst Time for Interactive Processes", value=True)
    interactive_burst_time_range = (1, 10)

    if use_random_interactive_burst:
        min_burst = st.number_input("Minimum Burst Time for Interactive Processes", min_value=1, max_value=10, value=1)
        max_burst = st.number_input("Maximum Burst Time for Interactive Processes", min_value=min_burst, max_value=10, value=10)
        interactive_burst_time_range = (min_burst, max_burst)

    if st.button("Run Simulation"):
        with st.spinner("Running simulation..."):
            if mode == "Dynamic":
                cpu_usage_data, queue_fill_data, average_wait_times = asyncio.run(run_simulation_dynamic(
                    num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time, interactive_burst_time_range, use_random_interactive_burst, time_quantum
                ))
            else:
                cpu_usage_data, queue_fill_data, average_wait_times = asyncio.run(run_simulation_static(
                    num_cpus, speedup_simulation, process_settings, time_quantum, interactive_burst_time_range, use_random_interactive_burst
                ))

            if cpu_usage_data and queue_fill_data:
                plot_results(cpu_usage_data, queue_fill_data)
                plot_average_wait_time(average_wait_times)

if __name__ == "__main__":
    main()
