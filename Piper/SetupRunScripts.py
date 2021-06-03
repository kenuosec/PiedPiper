import os
import sys

def main():
    # Find the path of this file which is located in the same folder as the file needed to be edited

    path = os.path.dirname(os.path.abspath(__file__))
    print(path)

    # the visual basic code to run the batch file
    vbs_code = 'Set WshShell = CreateObject("WScript.Shell")\n' \
               f'WshShell.Run chr(34) & "{path}\\runpiper.bat" & Chr(34), 0\n' \
               'Set WshShell = Nothing'

    print(vbs_code)
    # open file to edit it
    try:
        with open(path+'\\runPiperBat.vbs', 'w') as f:
            f.write(vbs_code)
    except:
        print("try again, error occurred")

    # the batch code to run the piper
    bat_code = f'"{sys.executable}" "{path}\\PiperClient.py"'
    print(bat_code)
    # open file to edit it
    try:
        with open(path + '\\runpiper.bat', 'w') as f:
            f.write(bat_code)
    except:
        print("try again, error occurred")

if __name__ == "__main__":
    main()
