import os
import rarfile
import zipfile
import shutil
import subprocess


def extract_file(file_path, archive_data, archive_id, image_dir):
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in [".rar", ".cbr"]:
        extract_rar(file_path, archive_data, archive_id, image_dir)
    elif file_ext in [".cbz"]:
        extract_zip(file_path, archive_data, archive_id, image_dir)


def extract_rar(rar_path, archive_data, archive_id, image_dir):
    with rarfile.RarFile(rar_path) as rf:
        for file_info in sorted(rf.infolist(), key=lambda x: x.filename):
            if file_info.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                unique_name = f"{archive_id}_{os.path.basename(file_info.filename)}"
                output_path = os.path.join(image_dir, unique_name)
                rf.extract(file_info, image_dir)
                os.rename(os.path.join(image_dir, file_info.filename), output_path)
                archive_data["image_order"].append(unique_name)
                archive_data["images"].append(output_path)


def extract_zip(zip_path, archive_data, archive_id, image_dir):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for file_name in sorted(zf.namelist()):
            if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                unique_name = f"{archive_id}_{os.path.basename(file_name)}"
                output_path = os.path.join(image_dir, unique_name)
                zf.extract(file_name, image_dir)
                os.rename(os.path.join(image_dir, file_name), output_path)
                archive_data["image_order"].append(unique_name)
                archive_data["images"].append(output_path)


def create_cbr_archive(selected_files, save_path, image_dir):
    """
    Creates a .cbr archive with the selected files and removes temporary files afterward.
    """
    temp_output_dir = "temp_output"
    if not os.path.exists(temp_output_dir):
        os.makedirs(temp_output_dir)

    # Clear the temp_output_dir in case it already exists
    for file in os.listdir(temp_output_dir):
        os.remove(os.path.join(temp_output_dir, file))

    # Copy and rename selected files sequentially into temp_output
    for idx, file in enumerate(selected_files):
        file_ext = os.path.splitext(file)[1]
        new_name = f"{idx:03}{file_ext}"  # Rename files as 001.jpg, 002.png, etc.
        shutil.copy(file, os.path.join(temp_output_dir, new_name))

    # Check for rar utility
    rar_command = shutil.which("rar")
    if not rar_command:
        raise EnvironmentError("RAR utility not found. Please install WinRAR or a compatible RAR tool.")

    # Create the archive using the rar utility
    try:
        subprocess.run(
            [rar_command, "a", "-ep1", save_path, f"{temp_output_dir}/*"],
            check=True,
            text=True,
            shell=False
        )
        print(f"Archive successfully created: {save_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating archive: {e}")
    finally:
        # Ensure cleanup
        if os.path.exists(temp_output_dir):
            shutil.rmtree(temp_output_dir)
            print("Temporary files removed.")
