#!/usr/bin/env python3
"""
Script to check the status of the autonomous agent.
"""
from state_monitor import StateMonitor

def main():
    """Show the agent's status."""
    monitor = StateMonitor()
    monitor.print_status_report()

if __name__ == "__main__":
    main()