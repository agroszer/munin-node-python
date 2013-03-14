import win32service
import win32serviceutil
import win32event
import win32evtlogutil
#import win32traceutil
from thread import start_new_thread


class aservice(win32serviceutil.ServiceFramework):
    _svc_name_ = "python_munin"
    _svc_display_name_ = "python munin node"
    _svc_deps_ = ["EventLog"]

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.isAlive = True

    def SvcStop(self):

        # tell Service Manager we are trying to stop (required)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # write a message in the SM (optional)
        # import servicemanager
        # servicemanager.LogInfoMsg("aservice - Recieved stop signal")

        # set the event to call
        win32event.SetEvent(self.hWaitStop)

        self.isAlive = False

    def SvcDoRun(self):
        import servicemanager
        # Write a 'started' event to the event log... (not required)
        #
        win32evtlogutil.ReportEvent(
            self._svc_name_, servicemanager.PYS_SERVICE_STARTED,
            0, servicemanager.EVENTLOG_INFORMATION_TYPE, (self._svc_name_, ''))

        from munin_node import main
        start_new_thread(main, ())

        self.timeout = 1000  # In milliseconds (update every second)

        while self.isAlive:
            # wait for service stop signal, if timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)

        # and write a 'stopped' event to the event log (not required)
        #
        win32evtlogutil.ReportEvent(
            self._svc_name_, servicemanager.PYS_SERVICE_STOPPED,
            0, servicemanager.EVENTLOG_INFORMATION_TYPE, (self._svc_name_, ''))

        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(aservice)
