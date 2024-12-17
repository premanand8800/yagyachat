import os

def create_directories():
    base_dir = "e:/yagyachat"
    directories = [
        "app",
        "app/models",
        "app/middleware",
        "app/nodes",
        "app/utils",
        "app/config",
        "tests"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        os.makedirs(full_path, exist_ok=True)
        # Create __init__.py in each directory
        init_file = os.path.join(full_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Initialize package\n")

if __name__ == "__main__":
    create_directories()
