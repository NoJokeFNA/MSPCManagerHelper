import ctypes
import sys


class AdvancedStartup:
    @staticmethod
    def is_devmode():
        """
        Checks if the application is running in developer mode.

        Returns:
            bool: True if running in developer mode, False otherwise.
        """
        devmode_args = ['/devmode', '-devmode']
        return any(arg.lower() in devmode_args for arg in sys.argv)

    @staticmethod
    def is_debugdevmode():
        """
        Checks if the application is running in debug developer mode.

        Returns:
            bool: True if running in debug developer mode, False otherwise.
        """
        debugdevmode_args = ['/debugdevmode', '-debugdevmode']
        return any(arg.lower() in debugdevmode_args for arg in sys.argv)

    @staticmethod
    def is_admin():
        """
        Checks if the user is running the application with administrator privileges.

        Returns:
            bool: True if running as administrator, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return 0

    @staticmethod
    def run_as_admin(params):
        """
        Restarts the application with administrator privileges.

        Args:
            params (str): The parameters to pass to the executable.

        Exits:
            Exits the application if the restart is successful.
        """
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 0)
        if result > 32:
            sys.exit()
