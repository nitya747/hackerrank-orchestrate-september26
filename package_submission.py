import os
import zipfile

def package_code(zip_name="code.zip"):
    included_files = [
        "README.md",
        "log.txt",
        "code/__init__.py",
        "code/main.py",
        "code/loader.py",
        "code/evidence.py",
        "code/events.py",
        "code/forecast.py",
        "code/plans.py",
        "code/planner.py",
        "code/output.py",
        "evaluation/evaluate_samples.py",
        "evaluation/validate_output.py",
        "evaluation/usage_report.md",
    ]
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in included_files:
            if os.path.exists(f):
                zipf.write(f, arcname=f)
                print(f"Added '{f}' to {zip_name}")
            else:
                print(f"WARNING: File '{f}' missing!")

    print(f"\nSuccessfully created submission archive '{zip_name}' ({os.path.getsize(zip_name)} bytes).")

if __name__ == "__main__":
    package_code()
