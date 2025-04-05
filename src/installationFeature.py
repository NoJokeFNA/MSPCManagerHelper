import os
import shutil
import subprocess
import tempfile
import tkinter as tk
import webbrowser
import winreg
from tkinter import filedialog, messagebox

import requests

ERROR_NO_INTERNET_CONNECTION = 2316632067
ERROR_NO_RESULTS_FOUND = 2316632084
ERROR_SOURCE_RESET_NEEDED = 2316632139
ERROR_ALREADY_INSTALLED = 2316632107
ERROR_ADMIN_REQUIRED = 2147747880
ERROR_FOLDER_DELETION_REQUIRED = 2147747596
ERROR_NO_WRITE_PERMISSION = 2147942583

MSIX_FILETYPES = [("Msix / MsixBundle", "*.msix;*.msixbundle"), ("*", "*")]
LICENSE_FILETYPES = [("License.xml", "*.xml"), ("*", "*")]
DEPENDENCY_FILETYPES = [("Msix", "*.msix"), ("*", "*")]

# MSPCManagerHelper temporary directory
MSPC_MANAGER_HELPER_TEMP_DIR = os.path.join(tempfile.gettempdir(), "MSPCManagerHelper")
# EdgeWebView2 installer temporary download path
WV2_INSTALLER_TEMP_PATH = os.path.join(MSPC_MANAGER_HELPER_TEMP_DIR, "MicrosoftEdgeWebView2Setup.exe")
# EdgeWebView2 installer download link
WV2_INSTALLER_DOWNLOAD_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
# EdgeUpdate.exe log output directory
EDGE_UPDATE_LOG_SOURCE = os.path.join(os.environ['ProgramData'], 'Microsoft', 'EdgeUpdate', 'Log',
                                      'MicrosoftEdgeUpdate.log')
# EdgeUpdate.exe log output directory
EDGE_UPDATE_LOG_DESTINATION = os.path.join(os.environ['UserProfile'], 'Desktop', 'MicrosoftEdgeUpdate.log')


class InstallationFeature:
    def __init__(self, translator, result_textbox=None):
        """
        Initializes the InstallationFeature class.

        Args:
            translator: An instance of a translator for translating messages.
            result_textbox: An optional tkinter Text widget for displaying results.
        """
        self.translator = translator
        self.result_textbox = result_textbox

    def textbox(self, message):
        """
        Inserts a message into the result_textbox.

        Args:
            message (str): The message to insert.
        """
        self.result_textbox.config(state="normal")
        self.result_textbox.insert(tk.END, message + "\n")
        self.result_textbox.config(state="disabled")
        self.result_textbox.update_idletasks()  # 刷新界面

    def refresh_result_textbox(self):
        """
        Refreshes the result_textbox. Currently not implemented.
        """
        pass

    def download_from_winget(self):
        """
        Downloads Microsoft PC Manager using WinGet.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # Check if WinGet is installed
            result = subprocess.Popen(['where.exe', 'winget.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            if result.returncode != 0:
                return self.translator.translate("winget_not_installed")

            # Prompt user for Microsoft Store source agreement
            self.textbox(self.translator.translate("winget_msstore_source_agreement") + '\n')
            response = messagebox.askyesnocancel(
                self.translator.translate("winget_msstore_source_agreement_notice"),
                self.translator.translate("ask_winget_msstore_source_agreement")
            )
            if response is None:
                return self.translator.translate("user_canceled")
            elif not response:
                return self.translator.translate("disagree_winget_msstore_source_agreement")

            # Search for Microsoft PC Manager using WinGet
            result = subprocess.Popen(
                ['winget.exe', 'search', 'Microsoft PC Manager', '--source', 'msstore', '--accept-source-agreements'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            if result.returncode != 0:
                if result.returncode == ERROR_NO_INTERNET_CONNECTION:
                    return self.translator.translate("winget_not_internet_connection")
                elif result.returncode == ERROR_NO_RESULTS_FOUND:
                    return self.translator.translate("winget_no_results_found")
                elif result.returncode == ERROR_SOURCE_RESET_NEEDED:
                    return self.translator.translate("winget_source_reset_needed")
                else:
                    stderr = stderr.strip() if stderr else self.translator.translate("winget_not_error_info")
                    stdout = stdout.strip() if stdout else self.translator.translate("winget_not_output")
                    return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {stderr}\n{self.translator.translate('winget_error_code')}: {result.returncode}\n{self.translator.translate('winget_output')}: {stdout}"

            # Install Microsoft PC Manager using WinGet
            result = subprocess.Popen(
                ['winget.exe', 'install', 'Microsoft PC Manager', '--source', 'msstore', '--accept-source-agreements',
                 '--accept-package-agreements'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            self.textbox(self.translator.translate("downloading_pc_manager_from_winget") + '\n')
            if result.returncode != 0:
                if result.returncode == ERROR_ALREADY_INSTALLED:
                    return self.translator.translate("already_installed_pc_manager_from_winget")
                else:
                    stderr = stderr.strip() if stderr else self.translator.translate("winget_not_error_info")
                    stdout = stdout.strip() if stdout else self.translator.translate("winget_not_output")
                    return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {stderr}\n{self.translator.translate('winget_error_code')}: {result.returncode}\n{self.translator.translate('winget_output')}: {stdout}"

            return self.translator.translate("pc_manager_has_been_installed_from_winget")
        except Exception as e:
            return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {str(e)}\n{self.translator.translate('winget_not_error_code')}"

    def download_from_msstore(self):
        """
        Downloads Microsoft PC Manager from the Microsoft Store.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # Check if Microsoft Store is installed
            result = subprocess.run(
                ['powershell.exe', '-Command', 'Get-AppxPackage -Name Microsoft.WindowsStore'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if 'PackageFamilyName : Microsoft.WindowsStore_8wekyb3d8bbwe' in result.stdout:
                try:
                    # If Microsoft Store is installed, run the command
                    subprocess.run(
                        ["start", "ms-windows-store://pdp/?ProductId=9PM860492SZD"],
                        check=True, shell=True)
                    return self.translator.translate("download_from_msstore_app_opened")
                except Exception as e:
                    return f"{self.translator.translate('download_from_msstore_app_error')}: {str(e)}"
            else:
                # If Microsoft Store is not installed, open the specified URL
                webbrowser.open("https://www.microsoft.com/store/productid/9PM860492SZD")
                return self.translator.translate("download_from_msstore_site_opened")
        except Exception as e:
            return f"{self.translator.translate('download_from_msstore_site_error')}: {str(e)}"

    def install_for_all_users(self):
        """
        Installs an application package for all users.

        Returns:
            str: A message indicating the result of the operation.
        """
        # Open file selection dialog to select the file
        all_users_application_package_file_path = filedialog.askopenfilename(filetypes=MSIX_FILETYPES)
        if not all_users_application_package_file_path:
            return self.translator.translate("no_files_selected")

        # Prompt user to select a license file
        response_for_all_users_license = messagebox.askyesnocancel(
            self.translator.translate("install_for_all_users_license_select_notice"),
            self.translator.translate("install_for_all_users_license_select")
        )

        all_users_dependency_package_paths = None
        if response_for_all_users_license:  # Use license
            all_users_license_path = filedialog.askopenfilename(filetypes=LICENSE_FILETYPES)
            if not all_users_license_path:
                return self.translator.translate("no_files_selected")
        elif response_for_all_users_license is None:
            return self.translator.translate("user_canceled")
        else:
            all_users_license_path = None

        # Prompt user to select dependency packages
        response_for_all_users_dependency = messagebox.askyesnocancel(
            self.translator.translate("install_for_all_users_dependency_package_select_notice"),
            self.translator.translate("install_for_all_users_dependency_package_select")
        )

        if response_for_all_users_dependency:  # Select dependency packages
            all_users_dependency_package_paths = filedialog.askopenfilenames(filetypes=DEPENDENCY_FILETYPES)
            if not all_users_dependency_package_paths:
                return self.translator.translate("no_files_selected")
        elif response_for_all_users_dependency is None:
            return self.translator.translate("user_canceled")

        try:
            # Build Dism.exe command
            all_users_dism_command = ['Dism.exe', '/Online', '/Add-ProvisionedAppxPackage',
                                      f'/PackagePath:{all_users_application_package_file_path}']

            if all_users_license_path:  # Use license file
                all_users_dism_command.append(f'/LicensePath:{all_users_license_path}')
            else:  # Do not use license file
                all_users_dism_command.append('/SkipLicense')

            if all_users_dependency_package_paths:  # Use dependency packages, skip if not
                for dependency_path in all_users_dependency_package_paths:
                    all_users_dism_command.append(f'/DependencyPackagePath:{dependency_path}')

            # Install application using Dism.exe
            result = subprocess.run(all_users_dism_command, capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("install_for_all_users_success")
            else:
                return self.translator.translate("install_for_all_users_error") + f": {result.stderr}\n{result.stdout}"
        except FileNotFoundError as e:
            return f"{self.translator.translate('dism_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return self.translator.translate("install_for_all_users_error") + f": {str(e)}"

    def install_for_current_user(self):
        """
        Installs an application package for the current user.

        Returns:
            str: A message indicating the result of the operation.
        """
        # Open file selection dialog to select the file
        current_user_application_package_file_path = filedialog.askopenfilename(filetypes=MSIX_FILETYPES)
        if not current_user_application_package_file_path:
            return self.translator.translate("no_files_selected")

        # Prompt user to select dependency packages
        response_for_current_user_dependency = messagebox.askyesnocancel(
            self.translator.translate("install_for_current_user_dependency_package_select_notice"),
            self.translator.translate("install_for_current_user_dependency_package_select")
        )

        current_user_dependency_package_paths = None
        if response_for_current_user_dependency:  # Select dependency packages
            current_user_dependency_package_paths = filedialog.askopenfilenames(filetypes=DEPENDENCY_FILETYPES)
            if not current_user_dependency_package_paths:
                return self.translator.translate("no_files_selected")
        elif response_for_current_user_dependency is None:
            return self.translator.translate("user_canceled")

        try:
            # Build Add-AppxPackage command
            command = ['powershell.exe', '-Command',
                       f'Add-AppxPackage -Path "{current_user_application_package_file_path}"']
            if current_user_dependency_package_paths:  # Use dependency packages, skip if not
                dependency_paths = ",".join([f'"{additional_dependency_paths}"' for additional_dependency_paths in
                                             current_user_dependency_package_paths])
                command.append(f'-DependencyPath {dependency_paths}')

            # Install application using Add-AppxPackage command
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("install_for_current_user_success")
            else:
                return self.translator.translate(
                    "install_for_current_user_error") + f": {result.stderr}\n{result.stdout}"
        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return self.translator.translate("install_for_current_user_error") + f": {str(e)}"

    def reinstall_pc_manager(self):
        """
        Reinstalls Microsoft PC Manager.

        Returns:
            str: A message indicating the result of the operation.
        """
        whether_to_reinstall_for_all_users = messagebox.askyesnocancel(
            self.translator.translate("ask_whether_to_reinstall_for_all_users"),
            self.translator.translate("whether_to_reinstall_for_all_users")
        )

        if whether_to_reinstall_for_all_users is None:
            return self.translator.translate("user_canceled")

        if whether_to_reinstall_for_all_users:
            command = [
                "powershell.exe",
                "-Command",
                "Get-AppxPackage -AllUsers *Microsoft.MicrosoftPCManager* | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppxManifest.xml\"}"
            ]
        else:
            command = [
                "powershell.exe",
                "-Command",
                "Get-AppxPackage *Microsoft.MicrosoftPCManager* | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppxManifest.xml\"}"
            ]

        result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

        if result.returncode == 0:
            if "0x80073D02" in result.stderr:
                return self.translator.translate(
                    "reintsall_pc_manager_error_code_0x80073D02") + f"\n\n{result.stdout}\n{result.stderr}"
            return self.translator.translate("reinstall_pc_manager_success")
        elif result.returncode == 1:
            return self.translator.translate(
                "reintsall_pc_manager_error_code_1") + f"\n\n{result.stdout}\n{result.stderr}"
        elif result.returncode == 2:
            return self.translator.translate(
                "reintsall_pc_manager_error_code_2") + f"\n\n{result.stdout}\n{result.stderr}"
        else:
            return f"{self.translator.translate('reinstall_pc_manager_error')}\n{self.translator.translate('reinstall_pc_manager_error_code')}: {result.returncode}\n\n{result.stdout}\n{result.stderr}"

    def update_from_application_package(self):
        """
        Updates an application package.

        Returns:
            str: A message indicating the result of the operation.
        """
        # Open file selection dialog to select the file
        update_application_package_file_path = filedialog.askopenfilename(
            filetypes=[("Msix / MsixBundle", "*.msix;*.msixbundle"),
                       ("*", "*")])

        if not update_application_package_file_path:
            return self.translator.translate("no_files_selected")

        # Prompt user to select dependency packages
        response_for_update_dependency = messagebox.askyesnocancel(
            self.translator.translate("update_from_application_package_dependency_package_select_notice"),
            self.translator.translate("update_from_application_package_dependency_package_select")
        )

        update_dependency_package_paths = None
        if response_for_update_dependency:  # Select dependency packages
            update_dependency_package_paths = filedialog.askopenfilenames(filetypes=DEPENDENCY_FILETYPES)
            if not update_dependency_package_paths:
                return self.translator.translate("no_files_selected")
        elif response_for_update_dependency is None:
            return self.translator.translate("user_canceled")

        try:
            # Build Add-AppxPackage command
            command = ['powershell.exe', '-Command',
                       f'Add-AppxPackage -Path "{update_application_package_file_path}"']
            if update_dependency_package_paths:  # Use dependency packages, skip if not
                dependency_paths = ",".join([f'"{additional_dependency_paths}"' for additional_dependency_paths in
                                             update_dependency_package_paths])
                command.append(f'-DependencyPath {dependency_paths}')

            # Install application using Add-AppxPackage command
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("update_from_application_package_success")
            else:
                return self.translator.translate(
                    "update_from_application_package_error") + f": {result.stderr}\n{result.stdout}"
        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return self.translator.translate("update_from_application_package_error") + f": {str(e)}"

    def install_from_appxmanifest(self):
        """
        Installs an application from an AppxManifest file.

        Returns:
            str: A message indicating the result of the operation.
        """
        # Prompt user if Microsoft PC Manager is already installed
        responding_to_whether_or_not_it_was_installed = messagebox.askyesnocancel(
            self.translator.translate("warning"),
            self.translator.translate("install_from_appxmanifest_warn")
        )

        if responding_to_whether_or_not_it_was_installed is None or not responding_to_whether_or_not_it_was_installed:
            return self.translator.translate("user_canceled")

        # Open file selection dialog to select the file
        pc_manager_package_file_path = filedialog.askopenfilename(
            filetypes=[("Msix / MsixBundle", "*.msix;*.msixbundle"), ("*", "*")]
        )

        if not pc_manager_package_file_path:
            return self.translator.translate("user_canceled")

        try:
            # Create temporary directory
            mspcmanagerhelper_temp_dir = os.path.join(tempfile.gettempdir(),
                                                      "MSPCManagerHelper")  # MSPCManagerHelper temporary directory
            if not os.path.exists(mspcmanagerhelper_temp_dir):
                os.makedirs(mspcmanagerhelper_temp_dir)

            # Copy file to MSPCManagerHelper temporary directory and rename to .zip
            pc_manager_package_file_name = os.path.basename(
                pc_manager_package_file_path)  # Microsoft PC Manager package file name
            pc_manager_zip_package_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                            pc_manager_package_file_name + ".zip")  # Add .zip to package file name
            self.textbox(self.translator.translate("install_from_appxmanifest_copying_files"))
            shutil.copyfile(pc_manager_package_file_path,
                            pc_manager_zip_package_file_path)  # Copy source file to MSPCManagerHelper temporary directory

            # Unzip file
            pc_manager_package_unpacked_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                                 os.path.splitext(pc_manager_package_file_name)[
                                                                     0])  # Unzipped file path
            self.textbox(self.translator.translate("install_from_appxmanifest_unzipping_files"))
            shutil.unpack_archive(pc_manager_zip_package_file_path, pc_manager_package_unpacked_file_path)  # Unzip file

            # Check if there are .msix files in the unpacked folder
            pc_manager_msix_files = [f for f in os.listdir(pc_manager_package_unpacked_file_path) if
                                     f.endswith('.msix')]
            if not pc_manager_msix_files:
                pass
            else:
                # Check if the file name contains x64 or arm64
                x64_file = next((f for f in pc_manager_msix_files if 'x64' in f), None)
                arm64_file = next((f for f in pc_manager_msix_files if 'arm64' in f), None)
                if not x64_file and not arm64_file:
                    # Clean up files in the MSPCManagerHelper temporary directory
                    for temporary_files in os.listdir(
                            mspcmanagerhelper_temp_dir):  # Traverse files in the MSPCManagerHelper temporary directory
                        temporary_files_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                            temporary_files)  # Temporary file path
                        self.textbox(self.translator.translate("install_from_appxmanifest_cleaning_up"))
                        if os.path.isfile(temporary_files_path):  # If it is a file, delete it
                            os.remove(temporary_files_path)
                        elif os.path.isdir(temporary_files_path):  # If it is a directory, delete it
                            shutil.rmtree(temporary_files_path)
                    return self.translator.translate("install_from_appxmanifest_no_match_pc_manager_architecture")

                # Read the value of PROCESSOR_ARCHITECTURE to determine the package
                processor_architecture = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                                                            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                                                             "PROCESSOR_ARCHITECTURE"
                                                             )[0]

                if processor_architecture == "AMD64" and x64_file:
                    pc_manager_zip_package_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                                    x64_file + ".zip")  # Add .zip to the package file name
                    shutil.copyfile(os.path.join(pc_manager_package_unpacked_file_path, x64_file),
                                    pc_manager_zip_package_file_path)  # Copy file to MSPCManagerHelper temporary directory
                    self.textbox(self.translator.translate("install_from_appxmanifest_copying_files"))
                    shutil.unpack_archive(pc_manager_zip_package_file_path, os.path.join(mspcmanagerhelper_temp_dir,
                                                                                         os.path.splitext(x64_file)[
                                                                                             0]))  # Unzip file
                    self.textbox(self.translator.translate("install_from_appxmanifest_unzipping_files") + '\n')
                    pc_manager_package_unpacked_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                                         os.path.splitext(x64_file)[
                                                                             0])  # Unzipped file path
                elif processor_architecture == "ARM64" and arm64_file:
                    pc_manager_zip_package_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                                    arm64_file + ".zip")  # Add .zip to the package file name
                    shutil.copyfile(os.path.join(pc_manager_package_unpacked_file_path, arm64_file),
                                    pc_manager_zip_package_file_path)  # Copy file to MSPCManagerHelper temporary directory
                    self.textbox(self.translator.translate("install_from_appxmanifest_copying_files"))
                    shutil.unpack_archive(pc_manager_zip_package_file_path, os.path.join(mspcmanagerhelper_temp_dir,
                                                                                         os.path.splitext(arm64_file)[
                                                                                             0]))  # Unzip file
                    self.textbox(self.translator.translate("install_from_appxmanifest_unzipping_files") + '\n')
                    pc_manager_package_unpacked_file_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                                         os.path.splitext(arm64_file)[
                                                                             0])  # Unzipped file path
                else:
                    # Clean up files in the MSPCManagerHelper temporary directory
                    for temporary_files in os.listdir(
                            mspcmanagerhelper_temp_dir):  # Traverse files in the MSPCManagerHelper temporary directory
                        temporary_files_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                            temporary_files)  # Temporary file path
                        self.textbox(self.translator.translate("install_from_appxmanifest_cleaning_up"))
                        if os.path.isfile(temporary_files_path):  # If it is a file, delete it
                            os.remove(temporary_files_path)
                        elif os.path.isdir(temporary_files_path):  # If it is a directory, delete it
                            shutil.rmtree(temporary_files_path)
                    return self.translator.translate("install_from_appxmanifest_no_match_architecture")

            # Copy the last unzipped folder to %ProgramFiles%
            pc_manager_program_files_path = os.path.join(os.environ['ProgramFiles'], os.path.basename(
                pc_manager_package_unpacked_file_path))  # Microsoft PC Manager installation path
            if not os.path.exists(pc_manager_program_files_path):
                os.makedirs(pc_manager_program_files_path)
            self.textbox(self.translator.translate("install_from_appxmanifest_copying_files") + '\n')
            subprocess.run(
                ["Robocopy.exe", pc_manager_package_unpacked_file_path, pc_manager_program_files_path,  # Copy folder
                 "/E",  # Copy all subdirectories, including empty directories
                 "/XD", "AppxMetadata",  # Exclude directories
                 "/XF", "[Content_Types].xml", "AppxBlockMap.xml", "AppxSignature.p7x"  # Exclude files
                 ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # Modify the AppxManifest.xml file
            appxmanifest_path = os.path.join(pc_manager_program_files_path, "AppxManifest.xml")
            self.textbox(self.translator.translate("install_from_appxmanifest_modifying_appxmanifest") + '\n')
            with open(appxmanifest_path, 'r', encoding='utf-8') as file:  # Read the AppxManifest.xml file
                lines = file.readlines()  # Read the file content

            with open(appxmanifest_path, 'w', encoding='utf-8') as file:  # Write the AppxManifest.xml file
                for line in lines:  # Traverse the file content
                    if '<TargetDeviceFamily' in line and not line.strip().startswith(
                            '<!--'):  # If the <TargetDeviceFamily> tag is found
                        indent = line[:len(line) - len(line.lstrip())]  # Indent
                        file.write(f"{indent}<!-- {line.strip()} -->\n")  # Comment out the original line
                        file.write(
                            f"{indent}<TargetDeviceFamily Name=\"Windows.Universal\" MinVersion=\"0.0.0.0\" MaxVersionTested=\"0.0.0.0\"/>\n")  # Add a new line
                    else:
                        file.write(line)  # Write the original line

            # Prompt user to select dependency packages
            response_for_dependency = messagebox.askyesnocancel(
                self.translator.translate("install_from_appxmanifest_dependency_package_select_notice"),
                self.translator.translate("install_from_appxmanifest_dependency_package_select")
            )

            if response_for_dependency:  # Select dependency packages
                dependency_package_paths = filedialog.askopenfilenames(filetypes=DEPENDENCY_FILETYPES)
                if not dependency_package_paths:  # If no files are selected
                    # Clean up files in the MSPCManagerHelper temporary directory
                    for temporary_files in os.listdir(
                            mspcmanagerhelper_temp_dir):  # Traverse files in the MSPCManagerHelper temporary directory
                        temporary_files_path = os.path.join(mspcmanagerhelper_temp_dir,
                                                            temporary_files)  # Temporary file path
                        self.textbox(self.translator.translate("install_from_appxmanifest_cleaning_up"))
                        if os.path.isfile(temporary_files_path):  # If it is a file, delete it
                            os.remove(temporary_files_path)
                        elif os.path.isdir(temporary_files_path):  # If it is a directory, delete it
                            shutil.rmtree(temporary_files_path)
                    return self.translator.translate("no_files_selected")

                for dependency_path in dependency_package_paths:
                    self.textbox(
                        self.translator.translate("install_from_appxmanifest_installing_dependency_package") + '\n')
                    subprocess.run(['powershell.exe', '-Command', f'Add-AppxPackage -Path "{dependency_path}"'],
                                   capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                                   )

            # Register AppxManifest.xml
            self.textbox(self.translator.translate("install_from_appxmanifest_registering_app") + '\n')
            subprocess.run(['powershell.exe', '-Command',
                            f'Add-AppxPackage -Register "{pc_manager_program_files_path}\\AppxManifest.xml"'],
                           capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                           )

            # Ask if the service should be registered
            response_for_service = messagebox.askyesno(
                self.translator.translate("install_from_appxmanifest_register_svc_notice"),
                self.translator.translate("install_from_appxmanifest_register_svc")
            )

            if response_for_service:
                # Check if the service "PCManager Service Store" exists
                service_store_check = subprocess.run(
                    ['powershell.exe', '-Command', 'Get-Service -Name "PCManager Service Store"'],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )

                # Check if the service "PC Manager Service" exists
                service_store_old_check = subprocess.run(
                    ['powershell.exe', '-Command', 'Get-Service -Name "PC Manager Service"'],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )

                if any(check.returncode == 0 for check in [service_store_check, service_store_old_check]):
                    messagebox.showwarning(
                        self.translator.translate("install_from_appxmanifest_svc_exists_warning"),
                        self.translator.translate("install_from_appxmanifest_svc_exists")
                    )
                else:
                    # Create service
                    self.textbox(self.translator.translate("install_from_appxmanifest_registering_svc") + '\n')
                    service_create = subprocess.run(['sc.exe', 'create', 'PCManager Service Store', 'binPath=',
                                                     f'"{pc_manager_program_files_path}\\PCManager\\MSPCManagerService.exe"',
                                                     'DisplayName=', '"MSPCManager Service (Store)"', 'start=', 'auto'],
                                                    capture_output=True, text=True,
                                                    creationflags=subprocess.CREATE_NO_WINDOW
                                                    )

                    if service_create.returncode == 0:
                        # Set service description
                        subprocess.run(['sc.exe', 'description', 'PCManager Service Store',
                                        '"Microsoft PCManager Service For Store"'],
                                       capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                                       )
                        # Start service
                        subprocess.run(['sc.exe', 'start', 'PCManager Service Store'],
                                       capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                                       )

            # Clean up files in the MSPCManagerHelper temporary directory
            for temporary_files in os.listdir(
                    mspcmanagerhelper_temp_dir):  # Traverse files in the MSPCManagerHelper temporary directory
                temporary_files_path = os.path.join(mspcmanagerhelper_temp_dir, temporary_files)  # Temporary file path
                self.textbox(self.translator.translate("install_from_appxmanifest_cleaning_up"))
                if os.path.isfile(temporary_files_path):  # If it is a file, delete it
                    os.remove(temporary_files_path)
                elif os.path.isdir(temporary_files_path):  # If it is a directory, delete it
                    shutil.rmtree(temporary_files_path)

            return self.translator.translate("install_from_appxmanifest_success")
        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return self.translator.translate("install_from_appxmanifest_error") + f": {str(e)}"

    def install_wv2_runtime(self, app):
        """
        Installs the WebView2 runtime.

        Args:
            app: An instance of the application.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # Check if the temporary directory exists, if not, create it
            if not os.path.exists(MSPC_MANAGER_HELPER_TEMP_DIR):
                os.makedirs(MSPC_MANAGER_HELPER_TEMP_DIR, exist_ok=True)

            # Download the file
            response = requests.get(WV2_INSTALLER_DOWNLOAD_URL)
            if response.status_code == 200:
                with open(WV2_INSTALLER_TEMP_PATH, 'wb') as file:
                    file.write(response.content)
            else:
                return self.translator.translate("wv2_download_error")

            # Run the installer
            app.current_process = subprocess.Popen([WV2_INSTALLER_TEMP_PATH, "/install"], stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
            stdout, stderr = app.current_process.communicate()

            if app.cancelled:
                return self.translator.translate("wv2_installation_cancelled")

            if app.current_process.returncode == 0:
                return self.translator.translate("wv2_runtime_install_success") + '\n' + self.translator.translate(
                    "wv2_runtime_installer_download_link")
            elif app.current_process.returncode == ERROR_ADMIN_REQUIRED:
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_runtime_already_installed')}"
            elif app.current_process.returncode == ERROR_FOLDER_DELETION_REQUIRED:
                shutil.copy(EDGE_UPDATE_LOG_SOURCE, EDGE_UPDATE_LOG_DESTINATION)
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_exit_code_0x8004070c')}\n{self.translator.translate('edgeupdate_log_export_path')}: {EDGE_UPDATE_LOG_DESTINATION}\n{self.translator.translate('seek_help_from_system_administrator')}"
            elif app.current_process.returncode == ERROR_NO_WRITE_PERMISSION:
                shutil.copy(EDGE_UPDATE_LOG_SOURCE, EDGE_UPDATE_LOG_DESTINATION)
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_exit_code_0x800700b7')}\n{self.translator.translate('edgeupdate_log_export_path')}: {EDGE_UPDATE_LOG_DESTINATION}\n{self.translator.translate('seek_help_from_system_administrator')}"
            else:
                shutil.copy(EDGE_UPDATE_LOG_SOURCE, EDGE_UPDATE_LOG_DESTINATION)
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_error')}\n{self.translator.translate('edgeupdate_log_export_path')}: {EDGE_UPDATE_LOG_DESTINATION}\n{self.translator.translate('seek_help_from_system_administrator')}"

        except Exception as e:
            return f"{self.translator.translate('wv2_download_error_info')}: {str(e)}"
        finally:
            # Delete the temporary directory
            if os.path.exists(MSPC_MANAGER_HELPER_TEMP_DIR):
                shutil.rmtree(MSPC_MANAGER_HELPER_TEMP_DIR)
            app.current_process = None
