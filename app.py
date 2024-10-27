import asyncio
import random
import streamlit as st
import os
from mlqs import MultiLevelQueueScheduler, add_processes
from plots import plot_results, plot_average_wait_time

# pip install -r requirements.txt

async def run_simulation(num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time):
    """
    Runs the simulation and returns the results.
    """
    scheduler = MultiLevelQueueScheduler(num_cpus, total_processes, speedup_simulation, burst_time)

    # Add processes in the background
    #await add_processes(scheduler, total_processes, processes_per_second)
    asyncio.create_task(add_processes(scheduler, total_processes, processes_per_second, burst_time))

    # Run the scheduler and get results
    cpu_usage_data, queue_fill_data, average_wait_times = await scheduler.run_scheduler()

    return cpu_usage_data, queue_fill_data, average_wait_times

def main():
    st.title("Multi-Level Queue Scheduler Simulation")

    # Input parameters from user
    num_cpus = st.number_input("Number of CPUs", min_value=1, max_value=8, value=4)
    total_processes = st.number_input("Total Processes", min_value=1, max_value=300, value=44)
    processes_per_second = st.number_input("Processes Per Second", min_value=1, max_value=50, value=10)
    speedup_simulation = st.number_input("Speedup Simulation Factor", min_value=1, max_value=100, value=20)
    burst_time = st.number_input("Burst Time", min_value=1, max_value=10, value=3)

    if st.button("Run Simulation"):
        with st.spinner("Running simulation..."):
            # Run the simulation and get results
            cpu_usage_data, queue_fill_data, average_wait_times = asyncio.run(run_simulation(
                num_cpus, total_processes, processes_per_second, speedup_simulation, burst_time
            ))

            # Analyze results and plot
            if cpu_usage_data and queue_fill_data:
                plot_results(cpu_usage_data, queue_fill_data)
                plot_average_wait_time(average_wait_times)
                
# Run the Streamlit app
if __name__ == "__main__":
    main()
