import subprocess
import sys

def run_script(script_name, args=[]):
    command = [sys.executable, script_name] + args
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    if result.returncode != 0:
        sys.exit(f"Error: {script_name} failed with exit code {result.returncode}")

if __name__ == "__main__":
    # Run scraper
    run_script("./scripts/scraper.py")

    # Get CP value from arguments or set default
    cp_value = "520"

    # Run calculation
    run_script("./scripts/calculate_cp.py", ["--cp", cp_value])

    print("All steps completed successfully.")
