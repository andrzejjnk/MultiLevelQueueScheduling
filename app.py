import asyncio
import random
import streamlit as st
import os
from mlqs import MultiLevelQueueScheduler, add_processes
from plots import plot_results, plot_average_wait_time

# pip install -r requirements.txt

async def run_simulation_dynamic(num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time):
    """
    Run a dynamic simulation of the multi-level queue scheduler.

    Args:
        num_cpus (int): Number of CPUs available for the scheduler.
        total_processes (int): Total number of processes to be added dynamically.
        processes_per_second (int): Rate at which processes are added per second.
        speedup_simulation (int): Factor to speed up the simulation.
        burst_time (int): Default burst time for each process.

    Returns:
        tuple: Contains cpu_usage_data, queue_fill_data, and average_wait_times.
    """
    scheduler = MultiLevelQueueScheduler(num_cpus, total_processes, speedup_simulation, burst_time)
    asyncio.create_task(add_processes(scheduler, total_processes, processes_per_second, burst_time))
    cpu_usage_data, queue_fill_data, average_wait_times = await scheduler.run_scheduler()
    return cpu_usage_data, queue_fill_data, average_wait_times


async def run_simulation_static(num_cpus, speedup_simulation, process_settings):
    """
    Run a static simulation of the multi-level queue scheduler.

    Args:
        num_cpus (int): Number of CPUs available for the scheduler.
        speedup_simulation (int): Factor to speed up the simulation.
        process_settings (dict): Dictionary containing process counts and burst times for each queue type.

    Returns:
        tuple: Contains cpu_usage_data, queue_fill_data, and average_wait_times.
    """
    scheduler = MultiLevelQueueScheduler(num_cpus, sum(settings["count"] for settings in process_settings.values()), speedup_simulation)

    # Add processes based on static settings for each priority queue
    for priority, settings in process_settings.items():
        for i in range(settings["count"]):
            process_name = f"{priority}_Process_{i + 1}"
            await scheduler.schedule_process(priority, process_name, settings["burst_time"])

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

    # Process addition mode selection
    mode = st.radio("Select Process Adding Mode:", ("Dynamic", "Static"))

    num_cpus = st.number_input("Number of CPUs", min_value=1, max_value=4, value=2)
    speedup_simulation = st.number_input("Speedup Simulation Factor", min_value=1, max_value=100, value=20)

    if mode == "Dynamic":
        total_processes = st.number_input("Total Processes", min_value=1, max_value=300, value=44)
        processes_per_second = st.number_input("Processes Per Second", min_value=1, max_value=50, value=10)
        burst_time = st.number_input("Burst Time", min_value=1, max_value=10, value=3)

    elif mode == "Static":
        process_settings = {}
        total_processes = 0  # Set total_processes to zero as it's calculated dynamically in static mode

        for priority in ["Real Time", "System", "Interactive", "Batch", "Low Priority"]:
            with st.expander(f"{priority} Queue Settings"):
                process_count = st.number_input(f"Number of {priority} Processes", min_value=0, max_value=100, value=5)
                burst_time = st.number_input(f"Burst Time for {priority} Processes", min_value=1, max_value=10, value=3)
                process_settings[priority] = {"count": process_count, "burst_time": burst_time}
                total_processes += process_count  # Summing the total number of processes

    if st.button("Run Simulation"):
        with st.spinner("Running simulation..."):
            if mode == "Dynamic":
                # Run dynamic process addition simulation
                cpu_usage_data, queue_fill_data, average_wait_times = asyncio.run(run_simulation_dynamic(
                    num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time
                ))
            else:
                # Run static process addition simulation
                cpu_usage_data, queue_fill_data, average_wait_times = asyncio.run(run_simulation_static(
                    num_cpus, speedup_simulation, process_settings
                ))

            # Display results and plots
            if cpu_usage_data and queue_fill_data:
                plot_results(cpu_usage_data, queue_fill_data)
                plot_average_wait_time(average_wait_times)
                
if __name__ == "__main__":
    main()
