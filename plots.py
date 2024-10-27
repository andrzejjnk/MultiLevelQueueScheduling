import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
from matplotlib.ticker import MaxNLocator
import streamlit as st


plots_folder = "plots"
os.makedirs(plots_folder, exist_ok=True)

def plot_results(cpu_usage_data: List[List[int]], queue_fill_data: Dict[str, List[int]]) -> None:
    """
    Plot CPU usage and queue fill levels over time.
    
    Args:
        cpu_usage_data (List[List[int]]): A 2D list where each sublist represents CPU usage over time for each CPU.
        queue_fill_data (Dict[str, List[int]]): A dictionary with queue names as keys and their fill levels over time as values.
    """
    num_cpus = len(cpu_usage_data)
    time_steps = range(len(cpu_usage_data[0]))

    fig, axs = plt.subplots(num_cpus, 1, figsize=(16, 4 * num_cpus), constrained_layout=True)
    fig.suptitle('CPU Usage Over Time', fontsize=18)

    if num_cpus == 1:
        axs = [axs]

    for i, usage in enumerate(cpu_usage_data):
        axs[i].plot(usage, label=f'CPU {i}', color="tab:blue", alpha=0.7)
        axs[i].set_title(f'CPU {i} Usage', fontsize=14)
        axs[i].set_xlabel('Time (simulation units)', fontsize=12)
        axs[i].set_ylabel('CPU Usage\n(0 = free,\n1 = busy)', fontsize=12, rotation=0, labelpad=30)
        axs[i].legend(loc='upper right')
        axs[i].grid()
        axs[i].yaxis.set_major_locator(MaxNLocator(integer=True))


    cpu_usage_plot_path = os.path.join(plots_folder, "cpu_usage_plot.png")
    plt.savefig(cpu_usage_plot_path)
    print(f"CPU Usage plot saved at: {cpu_usage_plot_path}")

    st.pyplot(fig)
    plt.close(fig)

    # Queue Fill Plot
    num_queues = len(queue_fill_data)
    fig2, axs2 = plt.subplots(num_queues, 1, figsize=(16, 4 * num_queues), constrained_layout=True)
    fig2.suptitle('Queue Fill Levels Over Time', fontsize=18)

    if num_queues == 1:
        axs2 = [axs2]

    for i, (priority, fill_data) in enumerate(queue_fill_data.items()):
        axs2[i].plot(fill_data, label=f'{priority} Queue', color="tab:orange", alpha=0.7)
        axs2[i].set_title(f'{priority} Queue Fill Level', fontsize=14)
        axs2[i].set_xlabel('Time (simulation units)', fontsize=12)
        axs2[i].set_ylabel('Processes\nin Queue', fontsize=12, rotation=0, labelpad=30)
        axs2[i].legend(loc='upper right')
        axs2[i].grid()
        axs2[i].yaxis.set_major_locator(MaxNLocator(integer=True))


    queue_fill_plot_path = os.path.join(plots_folder, "queue_fill_plot.png")
    plt.savefig(queue_fill_plot_path)
    print(f"Queue Fill Levels plot saved at: {queue_fill_plot_path}")

    st.pyplot(fig2)
    plt.close(fig2)


def plot_average_wait_time(average_wait_times: Dict[str, float]) -> None:
    """
    Plot the average wait time for different types of processes.

    Args:
        average_wait_times (Dict[str, float]): A dictionary with process types as keys and their average wait times as values.
    """
    average_times = {key: np.mean(times) for key, times in average_wait_times.items()}

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(average_times.keys(), average_times.values(), color='skyblue')
    ax.set_xlabel('Process Type', fontsize=12)
    ax.set_ylabel("Average Time Spent in Queue (s)", fontsize=12)
    ax.set_title("Average Time Spent in Queue by Different Types of Processes", fontsize=14)
    ax.set_xticks(range(len(average_times)))
    ax.set_xticklabels(average_times.keys(), rotation=45)
    ax.grid(axis='y')


    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:.2f} s', ha='center', va='bottom')

    average_wait_time_plot_path = os.path.join(plots_folder, "average_wait_time_plot.png")
    plt.savefig(average_wait_time_plot_path)
    print(f"Average Wait Time plot saved at: {average_wait_time_plot_path}")

    st.pyplot(fig)
    plt.close(fig)


