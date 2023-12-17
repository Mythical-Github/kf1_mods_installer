import os
import re
import sys
import json
import time
import shutil
import requests
import subprocess
from zipfile import ZipFile
from bs4 import BeautifulSoup

script_dir = os.path.dirname(os.path.abspath(__file__))

settings_path = f"{script_dir}/settings.json"

with open(settings_path, 'r') as file:
    settings = json.load(file)
        
archive_extractor_exe = f"{script_dir}/KFTempArchiveExtractor.exe"
steam_cmd_dir = f"{script_dir}/steamcmd"
steam_cmd_exe = f"{steam_cmd_dir}/steamcmd.exe"
archive_dir = f"{script_dir}/KF Archive Files"

steamcmd_url = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'

def find_bin_files(root_path):
    bin_files = []
    for foldername, subfolders, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith(".bin"):
                bin_files.append(os.path.join(foldername, filename))
    return bin_files

def find_files_in_directory(directory, file_types):
    found_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            for file_type, extensions in file_types.items():
                if file.lower().endswith(tuple(extensions)):
                    found_files.append(os.path.join(root, file))
                    break
    return found_files

def move_files_to_directories(files, settings):
    for file_path in files:
        file_name = os.path.basename(file_path)
        file_type = None

        for dir_name, extensions in settings["dir_names_to_file_types"].items():
            if file_name.lower().endswith(tuple(extensions)):
                file_type = dir_name
                break

        if file_type is not None:
            destination_dir = os.path.join(
                settings["game_dir"],
                settings["mods_dir"],
                file_type
            )

            os.makedirs(destination_dir, exist_ok=True)

            destination_path = os.path.join(destination_dir, file_name)

            shutil.move(file_path, destination_path)
            print(f"File '{file_name}' moved to '{destination_path}'")

def download_and_unzip_steamcmd():
    os.makedirs(steam_cmd_dir, exist_ok=True)
    response = requests.get(steamcmd_url)
    zip_file_path = f"{steam_cmd_dir}/steamcmd.zip"

    with open(zip_file_path, 'wb') as zip_file:
        zip_file.write(response.content)

    with ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(steam_cmd_dir)
        
    os.remove(zip_file_path)

def update_ini_file(game_dir, ini_path, paths_config):
    ini_full_path = os.path.join(game_dir, ini_path)

    with open(ini_full_path, 'r') as ini_file:
        ini_content = ini_file.readlines()

    section_found = False
    for i, line in enumerate(ini_content):
        if '[Core.System]' in line:
            section_found = True
            for path_config in paths_config:
                if path_config not in ini_content:
                    ini_content.insert(i + 1, path_config + '\n')

    if not section_found:
        ini_content.append('\n[Core.System]\n')
        for path_config in paths_config:
            ini_content.append(path_config + '\n')

    with open(ini_full_path, 'w') as ini_file:
        ini_file.writelines(ini_content)

def main():
    with open(settings_path, 'r') as settings_file:
        settings = json.load(settings_file)

    game_dir = settings['game_dir']
    ini_path = 'System/KillingFloor.ini'
    mods_dir = settings['mods_dir']
    dir_names_to_file_types = settings['dir_names_to_file_types']

    paths_config = [
        f'Paths={os.path.join("..", mods_dir, subdir)}/*{ext}'
        for subdir, ext_list in dir_names_to_file_types.items()
        for ext in ext_list
    ]

    update_ini_file(game_dir, ini_path, paths_config)
    
    with open(settings_path, 'r') as settings_file:
        settings = json.load(settings_file)

    urls = settings.get('workshop_collection_urls', [])


    all_subscription_app_ids = []

    for url in urls:
        response = requests.get(url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        collection_items = soup.find_all('div', class_='collectionItem')

        subscription_app_ids = []

        for item in collection_items:
            onclick_attribute = item.find('a', class_='subscribe')['onclick']
            match = re.search(r"SubscribeCollectionItem\(\s*'(\d+)'\s*,\s*'(\d+)'\s*\)", onclick_attribute)

            if match:
                item_id = match.group(1)
                subscription_app_ids.append(item_id)


        all_subscription_app_ids.extend(subscription_app_ids)

    
    
    os.chdir(steam_cmd_dir)

    
    initial_commands = [
            steam_cmd_exe,
            "+login",
            "user",
            "pass"
        ]
    
    middle_commands = [
            "+workshop_download_item",
            "1250"
        ]
    
    end_commands = [
            "+quit"
        ]
    
    max_command_length = 2048
    current_length = sum(len(command) for command in initial_commands + end_commands)
    current_commands = initial_commands + end_commands
    
    for mod_id in all_subscription_app_ids:
        workshop_command = "+workshop_download_item 1250 " + str(mod_id)
        if current_length + len(workshop_command) > max_command_length:

            subprocess.run(current_commands)
    

            current_commands = initial_commands + end_commands
            current_length = sum(len(command) for command in current_commands)
    
        middle_commands.append(workshop_command)
        current_commands.insert(-1, workshop_command)
        current_length += len(workshop_command)
    

    subprocess.run(current_commands)
        
    file_path = f"{steam_cmd_dir}/steamapps/workshop/content/1250"
    
    if not os.path.exists(file_path):
        print(f"The specified path '{file_path}' does not exist.")
        return
    
    bin_files_list = find_bin_files(file_path)
    
    if bin_files_list:
        print("List of bin files:")
        for bin_file in bin_files_list:
            os.system(f"{archive_extractor_exe} {bin_file}")
    else:
        print(f"No bin files found in the specified path: {file_path}")

    if not os.path.exists(archive_dir):
        print("Error: 'KF Archive Files' directory not found.")
        return

    files_to_search = settings["dir_names_to_file_types"]
    found_files = find_files_in_directory(archive_dir, files_to_search)

    if found_files:
        move_files_to_directories(found_files, settings)
    else:
        print("No files found.")

if __name__ == "__main__":
    download_and_unzip_steamcmd()
    print("SteamCMD downloaded and unzipped successfully.")
    main()