import winreg


class CheckSystemRequirements:
    MIN_BUILD_NUMBER = 19042
    MIN_BUILD_NUMBER_ADMIN = 27718
    ADMIN_APPROVAL_MODE_ENABLED = 2

    def __init__(self, translator):
        """
        Initializes the class with a translator.

        Args:
            translator: A translator object for translating messages.
        """
        self.translator = translator

    def check_system_requirements(self):
        """
        Checks the system requirements by querying the current build number of the operating system.

        Returns:
            str: A translated message indicating whether the system requirements are met or not.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion") as key:
                current_build_number = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                if int(current_build_number) < self.MIN_BUILD_NUMBER:
                    return self.translator.translate("failure_to_meet_system_requirements")
                else:
                    return self.translator.translate("meet_system_requirements")
        except FileNotFoundError:
            return self.translator.translate("cannot_read_version")

    @staticmethod
    def check_system_build_number_and_admin_approval_mode():
        """
        Checks the system build number and the administrator approval mode.

        Returns:
            bool: True if the build number is >= 27718 and the administrator approval mode is enabled, otherwise False.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion") as key:
                current_build_number = int(winreg.QueryValueEx(key, "CurrentBuildNumber")[0])
                if current_build_number < CheckSystemRequirements.MIN_BUILD_NUMBER_ADMIN:
                    return False

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System") as key:
                admin_approval_mode = int(winreg.QueryValueEx(key, "TypeOfAdminApprovalMode")[0])
                if admin_approval_mode == CheckSystemRequirements.ADMIN_APPROVAL_MODE_ENABLED:
                    return True
        except FileNotFoundError:
            return False

        return False
