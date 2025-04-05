import os
import shutil
import subprocess
import sys
import tkinter as tk
import winreg
from datetime import datetime
from tkinter import filedialog, messagebox

from otherFeature import OtherFeature
from uninstallationFeature import UninstallationFeature

ERROR_ADMIN_REQUIRED = 1
ERROR_FOLDER_DELETION_REQUIRED = 0x8004070c
ERROR_NO_WRITE_PERMISSION = 0x800700b7
PROCESS_NAMES = ["MSPCManager.exe", "MSPCManagerService.exe", "MSPCManagerCore.exe", "MSPCManagerWidget.exe",
                 "Microsoft.WIC.PCWndManager.Plugin.exe", "MSPCWndManager.exe"]


class MainFeature:
    """
    Main feature class for managing PC Manager operations.

    Attributes:
        translator (object): Translator object for translating messages.
        result_textbox (tk.Text): Textbox for displaying results.
        other_feature (OtherFeature): Instance of OtherFeature class.
        uninstallation_feature (UninstallationFeature): Instance of UninstallationFeature class.
    """

    def __init__(self, translator, result_textbox=None):
        """
        Initializes the MainFeature class.

        Args:
            translator (object): Translator object for translating messages.
            result_textbox (tk.Text, optional): Textbox for displaying results. Defaults to None.
        """
        self.translator = translator
        self.result_textbox = result_textbox
        self.other_feature = OtherFeature(self.translator, self.result_textbox)
        self.uninstallation_feature = UninstallationFeature(self.translator, self.result_textbox)

    def textbox(self, message):
        """
        Displays a message in the result textbox.

        Args:
            message (str): Message to be displayed.
        """
        message = str(message)
        self.result_textbox.config(state="normal")
        self.result_textbox.insert(tk.END, message + "\n")
        self.result_textbox.config(state="disabled")
        self.result_textbox.update_idletasks()  # Refresh the interface

    def get_nsudolc_path(self):
        """
        Retrieves the path to the NSudoLC executable based on the processor architecture.

        Returns:
            str: Path to the NSudoLC executable or None if an error occurs.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                processor_architecture = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]

            if processor_architecture == "AMD64":
                if hasattr(sys, '_MEIPASS'):
                    return os.path.join(sys._MEIPASS, "tools", "NSudo", "NSudoLC_x64.exe")
                else:
                    return os.path.join("tools", "NSudo", "NSudoLC_x64.exe")
            elif processor_architecture == "ARM64":
                if hasattr(sys, '_MEIPASS'):
                    return os.path.join(sys._MEIPASS, "tools", "NSudo", "NSudoLC_ARM64.exe")
                else:
                    return os.path.join("tools", "NSudo", "NSudoLC_ARM64.exe")
            else:
                self.textbox(self.translator.translate("no_match_nsudo_version"))
                return None
        except Exception as e:
            self.textbox(self.translator.translate("error_getting_nsudo_path") + f": {str(e)}")
            return None

    def refresh_result_textbox(self):
        """
        Refreshes the result textbox for other features.
        """
        self.other_feature.result_textbox = self.result_textbox
        self.uninstallation_feature.result_textbox = self.result_textbox

    def repair_pc_manager(self):
        """
        Repairs the PC Manager by uninstalling and reinstalling necessary components.

        Returns:
            str: Message indicating the result of the operation.
        """
        try:
            response = messagebox.askyesno(self.translator.translate("repair_pc_manager_notice"),
                                           self.translator.translate("repair_pc_manager_to_perform"))
            if response:
                self.textbox(self.uninstallation_feature.uninstall_for_all_users_in_dism())
                self.textbox(self.uninstallation_feature.uninstall_pc_manager_beta())
                self.textbox(self.other_feature.repair_edge_wv2_setup())
                return self.translator.translate("repair_pc_manager_success")
            else:
                return self.translator.translate("user_canceled")
        except Exception as e:
            return f"{self.translator.translate('repair_pc_manager_error')}: {str(e)}"

    def get_pc_manager_logs(self):
        """
        Retrieves and compresses PC Manager logs.

        Returns:
            str: Message indicating the result of the operation.
        """
        try:
            nsudolc_path = self.get_nsudolc_path()
            if not nsudolc_path:
                return "\n.join(messages)"

            date_str = datetime.now().strftime(datetime.now().isoformat().replace(":", "."))
            logs_destination = os.path.join(os.getenv("UserProfile"), "Desktop", "Microsoft PC Manager Logs", date_str)
            program_logs_source_path = os.path.join(os.getenv("ProgramData"), "Windows Master Store")
            appdata_clr_4_0_logs_source = os.path.join(os.getenv("LocalAppData"), "Microsoft", "CLR_v4.0", "UsageLogs")
            systemroot_clr_4_0_logs_source = os.path.join(os.getenv("SystemRoot"), "System32", "config",
                                                          "systemprofile", "AppData", "Local", "Microsoft", "CLR_v4.0",
                                                          "UsageLogs")
            common_logs_source = os.path.join(program_logs_source_path, "Common")
            crash_files_source = os.path.join(common_logs_source, "Crash")
            setup_logs_source = os.path.join(program_logs_source_path, "Setup")
            service_logs_source = os.path.join(program_logs_source_path, "ServiceData")
            exe_setup_logs_source = os.path.join(os.getenv("ProgramData"), "Windows Master Setup")
            logs_zip_archive = os.path.join(os.getenv("UserProfile"), "Desktop")

            os.makedirs(logs_destination, exist_ok=True)
            os.makedirs(os.path.join(logs_destination, "Common"), exist_ok=True)

            self._copy_logs(nsudolc_path, appdata_clr_4_0_logs_source,
                            os.path.join(logs_destination, "AppData_CLR_v4.0"), "*.log")
            self._copy_logs(nsudolc_path, systemroot_clr_4_0_logs_source,
                            os.path.join(logs_destination, "SystemRoot_CLR_v4.0"), "*.log")
            self._copy_logs(nsudolc_path, common_logs_source, os.path.join(logs_destination, "Common"), "*.log")
            self._copy_logs(nsudolc_path, crash_files_source, os.path.join(logs_destination, "Common", "Crash"), "*.*")
            self._copy_logs(nsudolc_path, setup_logs_source, os.path.join(logs_destination, "Setup"), "*.*")
            self._copy_logs(nsudolc_path, service_logs_source, os.path.join(logs_destination, "ServiceData"), "*.*")
            self._copy_logs(nsudolc_path, exe_setup_logs_source, os.path.join(logs_destination, "Windows Master Setup"),
                            "*.*")

            self._copy_other_logs(nsudolc_path, program_logs_source_path, logs_destination)

            self._copy_evtx_log(nsudolc_path, logs_destination)

            self._retrieve_computer_info(logs_destination)

            response_for_retrieve_dumps = messagebox.askyesno(
                self.translator.translate("ask_to_retrieve_pc_manager_dumps_notice"),
                self.translator.translate("ask_to_retrieve_pc_manager_dumps")
            )

            if response_for_retrieve_dumps:
                self._retrieve_dumps(nsudolc_path, logs_destination, date_str)

            self._compress_logs(logs_destination, logs_zip_archive, date_str)

            response_for_clear_logs = messagebox.askyesno(
                self.translator.translate("ask_to_clear_pc_manager_logs_notice"),
                self.translator.translate("ask_to_clear_pc_manager_logs")
            )

            if response_for_clear_logs:
                self._clear_logs(nsudolc_path)

            return "\n" + self.translator.translate("retrieve_pc_manager_logs_success")

        except Exception as e:
            self.textbox(self.translator.translate("retrieve_pc_manager_logs_error") + f":\n{str(e)}")

    def _copy_logs(self, nsudolc_path, source, destination, pattern):
        """
        Copies logs from the source to the destination using the specified pattern.

        Args:
            nsudolc_path (str): Path to the NSudoLC executable.
            source (str): Source directory.
            destination (str): Destination directory.
            pattern (str): File pattern to match.
        """
        if os.path.exists(source):
            try:
                result = subprocess.run([nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "Robocopy.exe",
                                         source, destination, pattern],
                                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.textbox(self.translator.translate("retrieve_pc_manager_logs_success"))
                else:
                    self.textbox(self.translator.translate("retrieve_pc_manager_logs_error") + f":\n{result.stdout}")
            except Exception as e:
                self.textbox(self.translator.translate("retrieve_pc_manager_logs_error") + f":\n{str(e)}")

    def _copy_other_logs(self, nsudolc_path, program_logs_source_path, logs_destination):
        """
        Copies other logs from the source to the destination.

        Args:
            nsudolc_path (str): Path to the NSudoLC executable.
            program_logs_source_path (str): Source directory.
            logs_destination (str): Destination directory.
        """
        try:
            isfile = [file for file in os.listdir(program_logs_source_path) if
                      not os.path.isfile(os.path.join(program_logs_source_path, file))]
            filtered = ["Common", "Setup", "ServiceData"]
            other_logs_destinations = []
            for name in isfile:
                try:
                    if any([".log" in file for file in
                            os.listdir(os.path.join(program_logs_source_path, name))]) and name not in filtered:
                        other_logs_destinations.append((os.path.join(program_logs_source_path, name), name))
                except:
                    pass

            for destination, file_name in other_logs_destinations:
                try:
                    result = subprocess.run(
                        [nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "xcopy.exe", destination,
                         os.path.join(os.path.join(logs_destination, "OtherLogs"), file_name), "/H", "/I", "/S", "/Y"],
                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        self.textbox(self.translator.translate("retrieve_pc_manager_other_logs_success"))
                    else:
                        self.textbox(
                            self.translator.translate("retrieve_pc_manager_other_logs_error") + f": {result.stdout}")
                except Exception as e:
                    self.textbox(self.translator.translate("retrieve_pc_manager_other_logs_error") + f": {str(e)}")
        except Exception as e:
            self.textbox(self.translator.translate("retrieve_pc_manager_other_logs_error") + f": {str(e)}")

    def _copy_evtx_log(self, nsudolc_path, logs_destination):
        """
        Copies the Application.evtx log to the destination.

        Args:
            nsudolc_path (str): Path to the NSudoLC executable.
            logs_destination (str): Destination directory.
        """
        if os.path.exists(os.path.join(os.getenv("SystemRoot"), "System32", "winevt", "Logs", "Application.evtx")):
            try:
                result = subprocess.run([nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "xcopy.exe",
                                         os.path.join(os.getenv("SystemRoot"), "System32", "winevt", "Logs",
                                                      "Application.evtx"), logs_destination, "/H", "/I", "/Y"],
                                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.textbox(self.translator.translate("retrieve_pc_manager_evtx_success"))
                else:
                    self.textbox(self.translator.translate("retrieve_pc_manager_evtx_error") + f":\n{result.stdout}")
            except Exception as e:
                self.textbox(self.translator.translate("retrieve_pc_manager_evtx_error") + f":\n{str(e)}")

    def _retrieve_computer_info(self, logs_destination):
        """
        Retrieves computer information and saves it to a file.

        Args:
            logs_destination (str): Destination directory.
        """
        try:
            self.textbox("\n" + self.translator.translate("retrieving_computer_info"))
            computer_info_path = os.path.join(logs_destination, "ComputerInfo.txt")
            subprocess.run(["powershell.exe", "-Command",
                            "Get-ComputerInfo | Out-File -FilePath '{}' -Encoding utf8".format(computer_info_path)],
                           capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.textbox(self.translator.translate("retrieve_computer_info_success"))
        except FileNotFoundError as e:
            self.textbox(f"{self.translator.translate('powershell_not_found')}\n{str(e)}: {e.filename}")
        except Exception as e:
            self.textbox(self.translator.translate("retrieve_computer_info_error") + f":\n{str(e)}")

    def _retrieve_dumps(self, nsudolc_path, logs_destination, date_str):
        """
        Retrieves dump files for specified processes.

        Args:
            nsudolc_path (str): Path to the NSudoLC executable.
            logs_destination (str): Destination directory.
            date_str (str): Date string for naming the dump files.
        """
        dumps_destination = os.path.join(logs_destination, 'Dumps')
        os.makedirs(dumps_destination, exist_ok=True)

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                processor_architecture = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]

            if processor_architecture == "AMD64":
                if hasattr(sys, '_MEIPASS'):
                    procdump_path = os.path.join(sys._MEIPASS, "tools", "ProcDump", "procdump64.exe")
                else:
                    procdump_path = os.path.join("tools", "ProcDump", "procdump64.exe")
            elif processor_architecture == "ARM64":
                if hasattr(sys, '_MEIPASS'):
                    procdump_path = os.path.join(sys._MEIPASS, "tools", "ProcDump", "procdump64a.exe")
                else:
                    procdump_path = os.path.join("tools", "ProcDump", "procdump64a.exe")
            else:
                self.textbox(self.translator.translate("no_match_procdump_version"))
                return "\n.join(messages)"

            self.textbox("\n" + self.translator.translate("procdump_agreement"))

            for process_name in PROCESS_NAMES:
                self.textbox("\n" + f"{self.translator.translate('retrieving_progress_name')}: {process_name}")
                dump_file = os.path.join(dumps_destination, f"{process_name}_{date_str}.dmp")
                try:
                    result = subprocess.run([procdump_path, "-accepteula", "-ma", process_name, dump_file],
                                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == ERROR_ADMIN_REQUIRED:
                        self.textbox(self.translator.translate("retrieve_pc_manager_dumps_success") + f": {dump_file}")
                    elif result.returncode == 4294967294:
                        self.textbox(self.translator.translate("retrieve_pc_manager_dumps_code_4294967294"))
                    else:
                        self.textbox({result.returncode})
                        self.textbox(
                            self.translator.translate("retrieve_pc_manager_dumps_error") + f": {result.stdout}")
                except subprocess.CalledProcessError as e:
                    self.textbox(self.translator.translate("retrieve_pc_manager_dumps_error") + f":\n{str(e)}")

        except Exception as e:
            self.textbox(self.translator.translate("retrieve_pc_manager_logs_error") + f":\n{str(e)}")

    def _compress_logs(self, logs_destination, logs_zip_archive, date_str):
        """
        Compresses the logs into a zip file.

        Args:
            logs_destination (str): Destination directory.
            logs_zip_archive (str): Directory to save the zip file.
            date_str (str): Date string for naming the zip file.
        """
        try:
            self.textbox("\n" + self.translator.translate("compressing_pc_manager_logs"))
            zip_file_name = f"{self.translator.translate('pc_manager_logs_zip_archive')}_{date_str}"
            zip_file_path = os.path.join(logs_zip_archive, zip_file_name)
            shutil.make_archive(zip_file_path, 'zip', logs_destination)
            self.textbox(self.translator.translate("path_to_pc_manager_logs_zip_archive") + f": {zip_file_path}.zip")
            messagebox.showwarning(self.translator.translate("warning"),
                                   self.translator.translate("do_not_share_log_files_with_untrusted_users"))
            self.textbox("\n" + self.translator.translate("do_not_share_log_files_with_untrusted_users"))

        except Exception as e:
            self.textbox(self.translator.translate("retrieve_pc_manager_logs_error") + f":\n{str(e)}")

    def _clear_logs(self, nsudolc_path):
        """
        Clears the logs from the desktop.

        Args:
            nsudolc_path (str): Path to the NSudoLC executable.
        """
        try:
            result = subprocess.run(
                [nsudolc_path, "-U:T", "-P:E", "-ShowWindowMode:Hide", "cmd.exe", "/C", "rmdir", "/S", "/Q",
                 "%UserProfile%\\Desktop\\Microsoft PC Manager Logs"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                self.textbox("\n" + self.translator.translate("clearing_pc_manager_logs_success"))
            else:
                self.textbox(self.translator.translate("clearing_pc_manager_logs_error") + f":\n{result.stdout}")
        except Exception as e:
            self.textbox(self.translator.translate("clearing_pc_manager_logs_error") + f":\n{str(e)}")

    def debug_dev_mode(self):
        """
        Debugs the developer mode by running selected files.

        Returns:
            str: Message indicating the result of the operation.
        """
        try:
            file_paths = filedialog.askopenfilenames(filetypes=[("*", "*")])

            if file_paths:
                results = []
                for file_path in file_paths:
                    result = subprocess.run([file_path], capture_output=True, text=True)
                    results.append(result.stdout)
                return self.translate("feature_unavailable") + '\n' + '\n'.join(results)
            else:
                return self.translator.translate("no_files_selected")
        except Exception as e:
            return self.translator.translate("warning") + f": {str(e)}"
