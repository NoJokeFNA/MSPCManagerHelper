import winreg


class GetPCManagerVersion:
    """
    A class to get the version numbers of Microsoft PC Manager and its Beta version
    from the Windows registry.
    """

    def __init__(self):
        """
        Initializes the GetPCManagerVersion class.
        """
        super().__init__()
        self.get_current_pc_manager_version = self._get_current_pc_manager_version
        self.get_current_pc_manager_beta_version = self._get_current_pc_manager_beta_version

    def _open_registry_key(self, hive, path):
        """
        Opens a registry key.

        Args:
            hive (int): The registry hive (e.g., HKEY_LOCAL_MACHINE).
            path (str): The path to the registry key.

        Returns:
            The opened registry key or None if the key does not exist.
        """
        try:
            return winreg.OpenKey(hive, path)
        except FileNotFoundError:
            return None

    def _get_registry_value(self, key, value_name):
        """
        Retrieves a value from an opened registry key.

        Args:
            key: The opened registry key.
            value_name (str): The name of the value to retrieve.

        Returns:
            The value or None if the value does not exist.
        """
        try:
            return winreg.QueryValueEx(key, value_name)[0]
        except (FileNotFoundError, OSError):
            return None

    def _get_version_from_registry(self, paths, value_name="PackageFullName", split_index=1):
        """
        Retrieves a version number from the registry.

        Args:
            paths (list): A list of tuples containing the registry hive and path.
            value_name (str, optional): The name of the registry value to retrieve. Defaults to "PackageFullName".
            split_index (int, optional): The index to split the version from the value. Defaults to 1.

        Returns:
            The version number as a string or None if not found.
        """
        for hive, path in paths:
            key = self._open_registry_key(hive, path)
            if key is not None:
                value = self._get_registry_value(key, value_name)
                if value:
                    return value.split('_')[split_index]
        return None

    def _get_current_pc_manager_version(self):
        """
        Retrieves the current version number of Microsoft PC Manager from the registry.

        Returns:
            The current version number as a string or None if not found.
        """
        paths = [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Appx\\AppxAllUserStore\\Applications"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\MSPCManager Store"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion\\AppModel\\SystemAppData\\Microsoft.PCManager_8wekyb3d8bbwe\\Schemas"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion\\AppModel\\SystemAppData\\Microsoft.MicrosoftPCManager_8wekyb3d8bbwe\\Schemas")
        ]
        return self._get_version_from_registry(paths)

    def _get_current_pc_manager_beta_version(self):
        """
        Retrieves the current version number of Microsoft PC Manager Beta from the registry.

        Returns:
            The current version number as a string or None if not found.
        """
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\MSPCManager"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MSPCManager")
        ]
        return self._get_version_from_registry(paths, "ProductVersion", 0)

    def refresh_version(self):
        """
        Retrieves both the current version number of Microsoft PC Manager and its Beta version.

        Returns:
            A tuple containing the current version number and the Beta version number.
        """
        return self.get_current_pc_manager_version(), self.get_current_pc_manager_beta_version()
