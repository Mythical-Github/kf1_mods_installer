import os
import re
import sys
import pyjson5 as json
import shutil
import requests
import subprocess
from zipfile import ZipFile
from bs4 import BeautifulSoup


if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir  = os.path.dirname(os.path.abspath(__file__))


settings_path = f'{script_dir}/settings.json'


with open(settings_path, 'r') as file:
    settings = json.load(file)


archive_extractor_exe = f'{script_dir}/KFTempArchiveExtractor.exe'
steam_cmd_dir = f'{script_dir}/steamcmd'
steam_cmd_exe = f'{steam_cmd_dir}/steamcmd.exe'
archive_dir = f'{script_dir}/KF Archive Files'


steamcmd_url = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'


def find_bin_files(root_path):
    bin_files = []
    for foldername, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith('.bin'):
                bin_files.append(os.path.join(foldername, filename))
    return bin_files


def find_files_in_directory(directory, files_to_search):
    found_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            for dir_name, file_types in files_to_search.items():
                if file.endswith(tuple(file_types)):
                    found_files.append(os.path.join(root, file))
    return found_files



def move_files_to_directories(files, settings):
    for file_path in files:
        file_name = os.path.basename(file_path)
        file_type = None

        for dir_name, extensions in settings['dir_names_to_file_types'].items():
            if file_name.lower().endswith(tuple(extensions)):
                file_type = dir_name
                break

        if file_type is not None:
            destination_dir = os.path.join(
                settings['game_dir'],
                settings['mods_dir'],
                file_type
            )

            os.makedirs(destination_dir, exist_ok=True)

            destination_path = os.path.join(destination_dir, file_name)

            shutil.move(file_path, destination_path)
            print(f'File "{file_name}" moved to "{destination_path}"')


def download_and_unzip_steamcmd():
    os.makedirs(steam_cmd_dir, exist_ok=True)
    response = requests.get(steamcmd_url)
    zip_file_path = f'{steam_cmd_dir}/steamcmd.zip'

    with open(zip_file_path, 'wb') as zip_file:
        zip_file.write(response.content)

    with ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(steam_cmd_dir)
        
    os.remove(zip_file_path)
    
    print('SteamCMD downloaded and unzipped successfully.')
    os.chdir(steam_cmd_dir)


def update_ini_file():

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


def get_subscription_ids():
    all_subscription_app_ids = []

    urls = settings.get('workshop_collection_urls', [])

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
    return all_subscription_app_ids


def get_current_commands():
    with open(settings_path, 'r') as settings_file:
        settings = json.load(settings_file)

    user = settings['login_info']['user']
    password = settings['login_info']['password']

    initial_commands = [
            steam_cmd_exe,
            "+login",
            user,
            password
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
    
    for mod_id in get_subscription_ids():
        workshop_command = "+workshop_download_item 1250 " + str(mod_id)
        if current_length + len(workshop_command) > max_command_length:

            subprocess.run(current_commands)
    

            current_commands = initial_commands + end_commands
            current_length = sum(len(command) for command in current_commands)
    
        middle_commands.append(workshop_command)
        current_commands.insert(-1, workshop_command)
        current_length += len(workshop_command)
    return current_commands


def download_mod_archives():
    subprocess.run(get_current_commands())


def unpack_mod_archives():
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


def move_mod_files():
    files_to_search = settings["dir_names_to_file_types"]
    found_files = find_files_in_directory(archive_dir, files_to_search)

    if found_files:
        move_files_to_directories(found_files, settings)
    else:
        print("No files found.")


def download_and_install_mods():
    download_and_unzip_steamcmd()
    update_ini_file()
    download_mod_archives()
    unpack_mod_archives()  
    move_mod_files()
