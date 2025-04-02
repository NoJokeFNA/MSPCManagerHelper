import glob
import itertools
import os
import re
import subprocess
import sys
import tkinter as tk
import winreg
from tkinter import messagebox

ERROR_CODE_740 = 740
ERROR_CODE_1 = 1
NSUDO_PATH_X64 = "tools\\NSudo\\NSudoLC_x64.exe"
NSUDO_PATH_ARM64 = "tools\\NSudo\\NSudoLC_ARM64.exe"
FOLDERS_TO_DELETE = [
    os.path.join(os.environ['LocalAppData'], 'Packages', 'Microsoft.MicrosoftPCManager_8wekyb3d8bbwe'),
    os.path.join(os.environ['LocalAppData'], 'Packages', 'Microsoft.PCManager_8wekyb3d8bbwe'),
    os.path.join(os.environ['LocalAppData'], 'PC Manager Store'),
    os.path.join(os.environ['LocalAppData'], 'Windows Master Store'),
    os.path.join(os.environ['ProgramData'], 'Windows Master Setup'),
    os.path.join(os.environ['ProgramData'], 'Windows Master Store'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Packages',
                 'Microsoft.MicrosoftPCManager_8wekyb3d8bbwe'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Packages',
                 'Microsoft.PCManager_8wekyb3d8bbwe'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Windows Master'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local',
                 'Windows Master Store'),
    os.path.join(os.environ['Temp'], 'WM Scan Test')
]
REGISTRY_KEYS_TO_DELETE = [
    r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\MSPCManager Store'
]
FILE_PATHS = [
    os.path.join(os.environ['LocalAppData'], 'Microsoft', 'CLR_v4.0', 'UsageLogs'),
    os.path.join(os.environ['SystemRoot'], 'Prefetch'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Microsoft',
                 'CLR_v4.0', 'UsageLogs')
]
PROCESSES = ["MSPCManager.exe", "MSPCManagerService.exe", "MSPCManagerCore.exe",
             "Microsoft.WIC.PCWndManager.Plugin.exe", "MSPCWndManager.exe", "MSPCManagerWidget.exe"]

PC_MANAGER_BETA_FOLDERS_TO_DELETE = [
    os.path.join(os.environ['LocalAppData'], 'PC Manager'),
    os.path.join(os.environ['LocalAppData'], 'Windows Master'),
    os.path.join(os.environ['ProgramData'], 'PCMConfigPath'),
    os.path.join(os.environ['ProgramData'], 'Windows Master'),
    os.path.join(os.environ['ProgramData'], 'Windows Master Setup'),
    os.path.join(os.environ['ProgramFiles'], 'Microsoft PC Manager'),
    os.path.join(os.environ['ProgramFiles'], 'WindowsMaster'),
    os.path.join(os.environ['ProgramFiles'], 'Windows Master'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Windows Master'),
    os.path.join(os.environ['SystemRoot'], 'SystemTemp', 'Windows Master'),
    os.path.join(os.environ['Temp'], 'Windows Master'),
    os.path.join(os.environ['Temp'], 'WM Scan Test')
]

PC_MANAGER_BETA_REGISTRY_KEYS_TO_DELETE = [
    r'HKEY_CURRENT_USER\Software\WindowsMaster',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run\WindowsMasterUI',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsMasterUI',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\MSPCManager',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\微软电脑管家',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\MSPCManager'
]

PC_MANAGER_BETA_FILES_TO_DELETE = [
    os.path.join(os.environ['AppData'], 'Microsoft', 'Internet Explorer', 'Quick Launch', 'User Pinned', 'TaskBar'),
    os.path.join(os.environ['AppData'], 'Microsoft', 'Windows', 'Start Menu'),
    os.path.join(os.environ['LocalAppData'], 'Microsoft', 'CLR_v4.0', 'UsageLogs'),
    os.path.join(os.environ['ProgramData'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
    os.path.join(os.environ['Public'], 'Desktop'),
    os.path.join(os.environ['SystemRoot'], 'Prefetch'),
    os.path.join(os.environ['SystemRoot'], 'System32', 'config', 'systemprofile', 'AppData', 'Local', 'Microsoft', 'CLR_v4.0', 'UsageLogs'),
    os.path.join(os.environ['UserProfile'], 'Desktop')
]

POWERSHELL_COMMANDS = [
    ["powershell.exe", "-Command",
     ("Get-AppxPackage -AllUsers | Where-Object {$_.Name -like 'Microsoft.MicrosoftPCManager'} | "
      "Remove-AppxPackage -AllUsers")],
    ["powershell.exe", "-Command",
     ("Get-AppxPackage -AllUsers | Where-Object {$_.Name -like 'Microsoft.PCManager'} | "
      "Remove-AppxPackage -AllUsers")],
    ["powershell.exe", "-Command",
     ("Get-AppxPackage | Where-Object {$_.Name -like '*Microsoft.MicrosoftPCManager*'} | "
      "ForEach-Object {Remove-AppxPackage -Package $_.PackageFullName}")],
    ["powershell.exe", "-Command",
     ("Get-AppxPackage | Where-Object {$_.Name -like '*Microsoft.PCManager*'} | "
      "ForEach-Object {Remove-AppxPackage -Package $_.PackageFullName}")]
]

class UninstallationFeature:
    """
    A class to handle the uninstallation of PC Manager and related components.

    Attributes:
    translator (Translator): An instance of the Translator class for handling translations.
    result_textbox (tk.Text): A tkinter Text widget for displaying results.
    """

    def __init__(self, translator, result_textbox=None):
        """
        Initializes the UninstallationFeature with a translator and an optional result textbox.

        Args:
        translator (Translator): An instance of the Translator class.
        result_textbox (tk.Text): A tkinter Text widget for displaying results.
        """
        self.translator = translator
        self.result_textbox = result_textbox

    def textbox(self, message):
        """
        Inserts a message into the result textbox.

        Args:
        message (str): The message to be inserted.
        """
        self.result_textbox.config(state="normal")
        self.result_textbox.insert(tk.END, message + "\n")
        self.result_textbox.config(state="disabled")
        self.result_textbox.update_idletasks()  # Refresh the interface

    def get_nsudolc_path(self):
        """
        Retrieves the path to the NSudoLC executable based on the processor architecture.

        Returns:
        str: The path to the NSudoLC executable or None if an error occurs.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                processor_architecture = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]

            if processor_architecture == "AMD64":
                return os.path.join(sys._MEIPASS, NSUDO_PATH_X64) if hasattr(sys, '_MEIPASS') else NSUDO_PATH_X64
            elif processor_architecture == "ARM64":
                return os.path.join(sys._MEIPASS, NSUDO_PATH_ARM64) if hasattr(sys, '_MEIPASS') else NSUDO_PATH_ARM64
            else:
                self.textbox(self.translator.translate("no_match_nsudo_version"))
                return None
        except Exception as e:
            self.textbox(self.translator.translate("error_getting_nsudo_path") + f": {str(e)}")
            return None

    def refresh_result_textbox(self):
        """
        Refreshes the result textbox. (Currently not implemented)
        """
        pass

    def uninstall_for_all_users_in_dism(self):
        """
        Uninstalls PC Manager for all users using DISM and PowerShell commands.

        Returns:
        str: The result of the uninstallation process.
        """
        try:
            provisioned_packages_result = subprocess.run(
                ["Dism.exe", "/Online", "/Get-ProvisionedAppxPackages"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            if provisioned_packages_result.returncode == ERROR_CODE_740:
                return f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code_740')}\n\n{provisioned_packages_result.stdout.strip()}"

            provisioned_pc_manager_packages = subprocess.run(
                ["findstr.exe", "Microsoft.MicrosoftPCManager"],
                input=provisioned_packages_result.stdout, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).stdout

            provisioned_pc_manager_packages_result = subprocess.run(
                ["findstr.exe", "Microsoft.PCManager"],
                input=provisioned_packages_result.stdout, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).stdout

            pc_manager_packages_to_remove = []
            if provisioned_pc_manager_packages:
                pc_manager_packages_to_remove.append(
                    str(provisioned_pc_manager_packages).split('PackageName : ')[1].split('\n')[0])
            if provisioned_pc_manager_packages_result:
                pc_manager_packages_to_remove.append(
                    str(provisioned_pc_manager_packages_result).split('PackageName : ')[1].split('\n')[0])

            if pc_manager_packages_to_remove:
                for provisioned_package_name in pc_manager_packages_to_remove:
                    remove_package_result = subprocess.run(
                        ["Dism.exe", "/Online", "/Remove-ProvisionedAppxPackage",
                         f"/PackageName:{provisioned_package_name}"],
                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    if remove_package_result.returncode != 0:
                        return f"{self.translator.translate('uninstall_for_all_users_in_dism_error')}: {remove_package_result.stderr.strip()}\n{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {remove_package_result.returncode}\n{remove_package_result.stdout.strip()}"

            results = [subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                       for cmd in POWERSHELL_COMMANDS]
            if all(result.returncode == 0 for result in results):
                if messagebox.askyesno(
                        self.translator.translate("cleanup_config_and_files_notice_for_all_users_in_dism"),
                        self.translator.translate("cleanup_config_and_files_for_all_users_in_dism")):

                    nsudolc_path = self.get_nsudolc_path()
                    if not nsudolc_path:
                        return "\n.join(messages)"

                    self._delete_folders(nsudolc_path, FOLDERS_TO_DELETE,
                                         'clearing_configuration_files_for_all_users_in_dism',
                                         'fail_to_clear_configuration_files_path_for_all_users_in_dism',
                                         'fail_to_configuration_files_info_for_all_users_in_dism')
                    self._delete_registry_keys(nsudolc_path, REGISTRY_KEYS_TO_DELETE,
                                               'clearing_registries_for_all_users_in_dism',
                                               'fail_to_clear_registries_info_for_all_users_in_dism')
                    self._delete_files(nsudolc_path, FILE_PATHS, 'clearing_other_files_for_all_users_in_dism',
                                       'fail_to_clear_other_files_for_all_users_in_dism',
                                       'fail_to_clear_other_files_info_for_all_users_in_dism')

                    response_for_advanced_cleanup = messagebox.askyesno(
                        self.translator.translate("advanced_cleanup_config_and_files_notice_for_all_users_in_dism"),
                        self.translator.translate("advanced_cleanup_config_and_files_for_all_users_in_dism")
                    )

                    if response_for_advanced_cleanup:
                        self._kill_processes(nsudolc_path, PROCESSES,
                                             'advanced_cleanup_taskkill_process_for_all_users_in_dism',
                                             'advanced_cleanup_no_processes_killed_for_all_users_in_dism')
                        self._delete_folders(nsudolc_path, FOLDERS_TO_DELETE,
                                             'advanced_clearing_folders_for_all_users_in_dism',
                                             'advanced_fail_to_config_and_files_for_all_users_in_dism',
                                             'advanced_fail_to_config_and_files_info_for_all_users_in_dism')
                        self._delete_files(nsudolc_path, FILE_PATHS,
                                           'advanced_clearing_config_and_files_for_all_users_in_dism',
                                           'advanced_fail_to_config_and_files_for_all_users_in_dism',
                                           'advanced_fail_to_config_and_files_info_for_all_users_in_dism')

                    return '\n' + self.translator.translate("uninstall_and_cleanup_for_all_users_in_dism_success")
                else:
                    return self.translator.translate('uninstall_for_all_users_in_dism_success')

            elif any(result.returncode == ERROR_CODE_1 for result in results):
                return (
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code_1')}\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[2].returncode}\n"
                    f"{results[2].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[3].returncode}\n"
                    f"{results[3].stderr.strip()}"
                )
            else:
                return (
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error')}\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[2].returncode}\n"
                    f"{results[2].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_in_dism_error_code')}: {results[3].returncode}\n"
                    f"{results[3].stderr.strip()}"
                )

        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{self.translator.translate('dism_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return f"{self.translator.translate('uninstall_for_all_users_in_dism_error')}: {str(e)}"

    def uninstall_for_all_users(self):
        """
        Uninstalls PC Manager for all users using PowerShell commands.

        Returns:
        str: The result of the uninstallation process.
        """
        try:
            results = [subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                       for cmd in POWERSHELL_COMMANDS[2:]]
            if all(result.returncode == 0 for result in results):
                if messagebox.askyesno(self.translator.translate("cleanup_config_and_files_notice_for_all_users"),
                                       self.translator.translate("cleanup_config_and_files_for_all_users")):

                    nsudolc_path = self.get_nsudolc_path()
                    if not nsudolc_path:
                        return "\n.join(messages)"

                    self._delete_folders(nsudolc_path, FOLDERS_TO_DELETE,
                                         'clearing_configuration_files_for_all_users',
                                         'fail_to_clear_configuration_files_path_for_all_users',
                                         'fail_to_configuration_files_info_for_all_users')
                    self._delete_registry_keys(nsudolc_path, REGISTRY_KEYS_TO_DELETE,
                                               'clearing_registries_for_all_users',
                                               'fail_to_clear_registries_info_for_all_users')
                    self._delete_files(nsudolc_path, FILE_PATHS, 'clearing_other_files_for_all_users',
                                       'fail_to_clear_other_files_for_all_users',
                                       'fail_to_clear_other_files_info_for_all_users')

                    response_for_advanced_cleanup = messagebox.askyesno(
                        self.translator.translate("advanced_cleanup_config_and_files_notice_for_all_users"),
                        self.translator.translate("advanced_cleanup_config_and_files_for_all_users")
                    )

                    if response_for_advanced_cleanup:
                        self._kill_processes(nsudolc_path, PROCESSES,
                                             'advanced_cleanup_taskkill_process_for_all_users',
                                             'advanced_cleanup_no_processes_killed_for_all_users')
                        self._delete_folders(nsudolc_path, FOLDERS_TO_DELETE,
                                             'advanced_clearing_folders_for_all_users',
                                             'advanced_fail_to_config_and_files_for_all_users',
                                             'advanced_fail_to_config_and_files_info_for_all_users')
                        self._delete_files(nsudolc_path, FILE_PATHS,
                                           'advanced_clearing_config_and_files_for_all_users',
                                           'advanced_fail_to_config_and_files_for_all_users',
                                           'advanced_fail_to_config_and_files_info_for_all_users')

                    return '\n' + self.translator.translate("uninstall_and_cleanup_for_all_users_success")
                else:
                    return self.translator.translate('uninstall_for_all_users_success')

            elif any(result.returncode == ERROR_CODE_1 for result in results):
                return (
                    f"{self.translator.translate('uninstall_for_all_users_error_code_1')}\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[2].returncode}\n"
                    f"{results[2].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[3].returncode}\n"
                    f"{results[3].stderr.strip()}"
                )
            else:
                return (
                    f"{self.translator.translate('uninstall_for_all_users_error')}\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[2].returncode}\n"
                    f"{results[2].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[3].returncode}\n"
                    f"{results[3].stderr.strip()}"
                )

        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return f"{self.translator.translate('uninstall_for_all_users_error')}: {str(e)}"

    def uninstall_for_current_user(self):
        """
        Uninstalls PC Manager for the current user using PowerShell commands.

        Returns:
        str: The result of the uninstallation process.
        """
        try:
            results = [
                subprocess.run(
                    ["powershell.exe", "-Command",
                     ("Get-AppxPackage | Where-Object {$_.Name -like '*Microsoft.MicrosoftPCManager*'} | "
                      "ForEach-Object {Remove-AppxPackage -Package $_.PackageFullName}")],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                ),
                subprocess.run(
                    ["powershell.exe", "-Command",
                     ("Get-AppxPackage | Where-Object {$_.Name -like '*Microsoft.PCManager*'} | "
                      "ForEach-Object {Remove-AppxPackage -Package $_.PackageFullName}")],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            ]

            if all(result.returncode == 0 for result in results):
                if messagebox.askyesno(self.translator.translate("cleanup_config_and_files_notice_for_current_user"),
                                       self.translator.translate("cleanup_config_and_files_for_current_user")):

                    nsudolc_path = self.get_nsudolc_path()
                    if not nsudolc_path:
                        return "\n.join(messages)"

                    self._delete_folders(nsudolc_path, FOLDERS_TO_DELETE,
                                         'clearing_configuration_files_for_current_user',
                                         'fail_to_clear_configuration_files_path_for_current_user',
                                         'fail_to_configuration_files_info_for_current_user')
                    self._delete_registry_keys(nsudolc_path, REGISTRY_KEYS_TO_DELETE,
                                               'clearing_registries_for_current_user',
                                               'fail_to_clear_registries_info_for_current_user')
                    self._delete_files(nsudolc_path, FILE_PATHS, 'clearing_other_files_for_current_user',
                                       'fail_to_clear_other_files_for_current_user',
                                       'fail_to_clear_other_files_info_for_current_user')

                    return '\n' + self.translator.translate("uninstall_and_cleanup_for_current_user_success")
                else:
                    return self.translator.translate('uninstall_for_current_user_success')

            elif any(result.returncode == ERROR_CODE_1 for result in results):
                return (
                    f"{self.translator.translate('uninstall_for_current_user_error_code_1')}\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_all_users_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}"
                )
            else:
                return (
                    f"{self.translator.translate('uninstall_for_current_user_error')}\n\n"
                    f"{self.translator.translate('uninstall_for_current_user_error_code')}: {results[0].returncode}\n"
                    f"{results[0].stderr.strip()}\n\n\n"
                    f"{self.translator.translate('uninstall_for_current_user_error_code')}: {results[1].returncode}\n"
                    f"{results[1].stderr.strip()}"
                )

        except FileNotFoundError as e:
            return f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}"
        except Exception as e:
            return f"{self.translator.translate('uninstall_for_current_user_error')}: {str(e)}"

    def uninstall_pc_manager_beta(self):
        """
        Uninstalls the beta version of PC Manager.

        Returns:
        str: The result of the uninstallation process.
        """
        try:
            pc_manager_beta_path = os.path.join(os.environ['ProgramFiles'], 'Microsoft PC Manager')
            if not os.path.exists(pc_manager_beta_path):
                return self.translator.translate("pc_manager_beta_not_found")

            pc_manager_beta_uninst_exe = os.path.join(pc_manager_beta_path, 'Uninst.exe')
            if not os.path.exists(pc_manager_beta_uninst_exe):
                return self.translator.translate("pc_manager_beta_not_found")

            result = subprocess.run([pc_manager_beta_uninst_exe], capture_output=True, text=True)
            if result.returncode != 0:
                return f"{self.translator.translate('uninstall_pcm_beta_error_info')}: {result.stderr.strip()}"

            tf = True
            while tf:
                if re.search(r'Uninst\w+\.exe', os.popen('tasklist.exe').read()):
                    pass
                else:
                    tf = False

            if not messagebox.askyesno(self.translator.translate("cleanup_pc_manager_beta_config_and_files_notice"),
                                       self.translator.translate("cleanup_pc_manager_beta_config_and_files")):
                return self.translator.translate("pc_manager_beta_uninstalled")

            self._delete_folders(None, PC_MANAGER_BETA_FOLDERS_TO_DELETE,
                                 'clearing_pc_manager_beta_configuration_files',
                                 'fail_to_clear_pc_manager_beta_configuration_files_path',
                                 'fail_to_clear_pc_manager_beta_configuration_files_info')

            self._delete_registry_keys(None, PC_MANAGER_BETA_REGISTRY_KEYS_TO_DELETE,
                                       'clearing_pc_manager_beta_registries',
                                       'fail_to_clear_pc_manager_beta_registries_info')

            self._delete_files(None, PC_MANAGER_BETA_FILES_TO_DELETE,
                               'clearing_pc_manager_beta_other_files',
                               'fail_to_clear_pc_manager_beta_other_files',
                               'fail_to_clear_pc_manager_beta_other_files_info')

            return '\n' + self.translator.translate("uninstalled_cleanup_pc_manager_beta_config_and_files")
        except Exception as e:
            return f"{self.translator.translate('uninstall_pc_manager_beta_error_info')}: {str(e)}"

    def _delete_folders(self, nsudolc_path, folders, success_message, fail_message, fail_info_message):
        """
        Deletes specified folders using NSudoLC.

        Args:
        nsudolc_path (str): The path to the NSudoLC executable.
        folders (list): A list of folder paths to delete.
        success_message (str): The message to display on successful deletion.
        fail_message (str): The message to display on failure.
        fail_info_message (str): Additional information to display on failure.
        """
        is_first = True
        for folder in folders:
            if os.path.exists(folder):
                try:
                    subprocess.run(
                        [nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "cmd.exe", "/C", "rmdir", "/S", "/Q",
                         folder],
                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if is_first:
                        self.textbox('\n' + self.translator.translate(success_message) + ':\n')
                        is_first = False
                    self.textbox('-' + folder + '\n')
                except Exception as e:
                    self.textbox(
                        self.translator.translate(fail_message) + ': ' + str(folder) + ', ' + self.translator.translate(
                            fail_info_message) + ': ' + str(e) + '\n')

    def _delete_registry_keys(self, nsudolc_path, keys, success_message, fail_message):
        """
        Deletes specified registry keys using NSudoLC.

        Args:
        nsudolc_path (str): The path to the NSudoLC executable.
        keys (list): A list of registry keys to delete.
        success_message (str): The message to display on successful deletion.
        fail_message (str): The message to display on failure.
        """
        is_first = True
        for key in keys:
            try:
                subprocess.run([nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "reg.exe", "delete", key, "/f"],
                               capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if is_first:
                    self.textbox('\n' + self.translator.translate(success_message) + ':\n')
                    is_first = False
                self.textbox('-' + key + '\n')
            except Exception as e:
                self.textbox(self.translator.translate(fail_message) + ': ' + str(e) + '\n')

    def _delete_files(self, nsudolc_path, file_paths, success_message, fail_message, fail_info_message):
        """
        Deletes specified files using NSudoLC.

        Args:
        nsudolc_path (str): The path to the NSudoLC executable.
        file_paths (list): A list of file paths to delete.
        success_message (str): The message to display on successful deletion.
        fail_message (str): The message to display on failure.
        fail_info_message (str): Additional information to display on failure.
        """
        prefetch_files = itertools.chain.from_iterable(
            glob.iglob(os.path.join(paths, pattern)) for paths in file_paths for pattern in [
                '*BGADEFMGR*.pf',
                '*CREATEDUMP*.pf',
                '*MICROSOFT.WIC.PCWNDMANAGER*.pf',
                '*MSPCMANAGER*.pf',
                '*MSPCWNDMANAGER*.pf',
                '*PCMAUTORUN*.pf',
                '*PCMCHECKSUM*.pf'
            ]
        )

        clr_logs_files = itertools.chain.from_iterable(
            glob.iglob(os.path.join(paths, pattern)) for paths in file_paths for pattern in [
                '*BGADefMgr*.log',
                '*Microsoft.WIC.PCWndManager.Plugin*.log',
                '*MSPCManager*.log',
                '*MSPCWndManager*.log',
                '*PCMAutoRun*.log',
                '*PCMCheckSum*.log'
            ]
        )

        is_first = True
        for files in itertools.chain(prefetch_files, clr_logs_files):
            try:
                subprocess.run(
                    [nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "cmd.exe", "/C", "del", "/F", "/Q", files],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if is_first:
                    self.textbox('\n' + self.translator.translate(success_message) + ':\n')
                    is_first = False
                self.textbox('-' + files + '\n')
            except Exception as e:
                self.textbox(
                    self.translator.translate(fail_message) + ': ' + str(files) + ', ' + self.translator.translate(
                        fail_info_message) + ': ' + str(e) + '\n')

    def _kill_processes(self, nsudolc_path, processes, success_message, no_processes_message):
        """
        Kills specified processes using NSudoLC.

        Args:
        nsudolc_path (str): The path to the NSudoLC executable.
        processes (list): A list of process names to kill.
        success_message (str): The message to display on successful process termination.
        no_processes_message (str): The message to display if no processes were killed.
        """
        is_first = True
        any_process_killed = False
        for process in processes:
            try:
                result = subprocess.run(
                    [nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "taskkill.exe", "/F", "/IM", process],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    if is_first:
                        self.textbox('\n' + self.translator.translate(success_message) + ':\n')
                        is_first = False
                    self.textbox('-' + process + '\n')
                    any_process_killed = True
            except Exception as e:
                continue

        if not any_process_killed:
            self.textbox(self.translator.translate(no_processes_message))
