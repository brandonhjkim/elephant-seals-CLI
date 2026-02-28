import os
import shutil

# Source directory
source_dir = r"C:\Users\conno\Downloads\Elephant Seals Project Mark 1-Reassigned for Labeling on 02-10-26.coco\Cropped Images"

# Destination directory (new folder in Downloads)
downloads_dir = r"C:\Users\conno\Downloads"
dest_dir = os.path.join(downloads_dir, "Renamed_Cropped_Images")

# Create destination directory if it doesn't exist
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    print(f"Created directory: {dest_dir}")

# Counter for renamed files
renamed_count = 0

# Process all files in source directory
for filename in os.listdir(source_dir):
    # Check if filename starts with "Copy of "
    if filename.startswith("Copy of "):
        # Create new filename by replacing "Copy of " with "Cropped_"
        new_filename = filename.replace("Copy of ", "Cropped_", 1)

        # Full paths
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, new_filename)

        # Copy file with new name
        shutil.copy2(source_path, dest_path)
        print(f"Renamed: {filename} -> {new_filename}")
        renamed_count += 1
    else:
        # If file doesn't start with "Copy of ", copy it as is
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copy2(source_path, dest_path)
        print(f"Copied without renaming: {filename}")

print(f"\nTotal files renamed: {renamed_count}")
print(f"All files saved to: {dest_dir}")