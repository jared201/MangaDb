import subprocess
import sys
import time
import os
import signal

def test_with_args(args):
    """Test the application with the given command-line arguments."""
    cmd = [sys.executable, "main.py"] + args
    print(f"Running: {' '.join(cmd)}")
    
    # Start the process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, bufsize=1, universal_newlines=True)
    
    # Give it a moment to start
    time.sleep(2)
    
    # Forcefully terminate the process
    if os.name == 'nt':  # Windows
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:  # Unix/Linux
        process.send_signal(signal.SIGTERM)
    
    try:
        # Get output with a short timeout
        stdout, stderr = process.communicate(timeout=1)
        
        # Print output
        print("STDOUT:")
        print(stdout)
        print("STDERR:")
        print(stderr)
    except subprocess.TimeoutExpired:
        # If it's still running, kill it
        process.kill()
        stdout, stderr = process.communicate()
        print("Process killed after timeout")
        print("STDOUT (partial):")
        print(stdout)
        print("STDERR (partial):")
        print(stderr)
    
    print("-" * 50)

def main():
    """Run tests with different command-line arguments."""
    # Test with default arguments
    test_with_args(["--api"])
    
    # Test with custom host
    test_with_args(["--api", "--host", "example.com"])
    
    # Test with custom host and port
    test_with_args(["--api", "--host", "localhost", "--port", "27021"])
    
    # Test with TUI
    test_with_args(["--tui", "--host", "localhost", "--port", "27021"])

if __name__ == "__main__":
    main()