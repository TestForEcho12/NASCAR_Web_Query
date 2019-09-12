import win32com.client
import time


class Excel:
    
    def __init__(self, year, series):
        file = r'C:\Users\greg5\Documents\NASCAR\NASCAR {} - '.format(year)
        series = {1: 'Cup',
                  2: 'Xfinity',
                  3: 'Trucks'}[series]
        self.excel_file = r'{}{}.xlsm'.format(file, series)

    def all_drivers(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)    
        print('Updating Drivers...')
        xl.Application.Run('Fetch_All_Names')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl
        
    def ineligible_drivers(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)    
        print('Updating Ineligible Drivers...')
        xl.Application.Run('Ineligible_Drivers')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl
    
    def results_from_csv(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)    
        print('Fetching Results...')
        xl.Application.Run('Fetch_Results')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl
    
    def full_run(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Full Run...')
        xl.Application.Run('Full_Run')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl
    
    def calculate_points(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Calculating Points...')
        xl.Application.Run('Calculate_Points')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl   
        
    def laps_led(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Laps Led...')
        xl.Application.Run('Laps_Led')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl

    def export_pictures(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Exporting Pictures...')
        xl.Application.Run('Pictures')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        print('Picture export complete\n')
        del xl
        
        
    def pre_race(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Updating Drivers...')
        xl.Application.Run('Fetch_All_Names')
        print('Updating Ineligible Drivers...')
        xl.Application.Run('Ineligible_Drivers')
        print('Fetching Results...')
        xl.Application.Run('Fetch_Results')
        print('Calculating Points...')
        xl.Application.Run('Calculate_Points')
        print('Full Run...')
        xl.Application.Run('Full_Run')
        time.sleep(5)
        print('Laps Led...')
        xl.Application.Run('Laps_Led')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        print('Pre-race complete\n')
        del xl
        
    def in_race(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.excel_file)
        print('Fetching Results...')
        xl.Application.Run('Fetch_Results')
        print('Calculating Points...')
        xl.Application.Run('Calculate_Points')
        print('Laps Led...')
        xl.Application.Run('Laps_Led')
        print('Exporting Pictures...')
        xl.Application.Run('Pictures')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        print('Picture export complete\n')
        del xl


class v2:
    
    def __init__(self, year, series_id):
        series = {1: 'Cup',
                  2: 'Xfinity',
                  3: 'Trucks'}[series_id]
        self.file = r'C:\Users\greg5\Documents\NASCAR\V2\NASCAR {} - {} 2.0.xlsm'.format(year, series)

    def practice(self):
        xl=win32com.client.Dispatch('Excel.Application')
        wb = xl.Workbooks.Open(Filename = self.file)    
        xl.Application.Run('Run_Practice')
        wb.Save()
        xl.DisplayAlerts = False  #Ignores dialog box and allows close without saving
        xl.Application.Quit()
        del xl