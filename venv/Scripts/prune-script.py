#!D:\TeleBot\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'oops-datedir-repo==0.0.24','console_scripts','prune'
__requires__ = 'oops-datedir-repo==0.0.24'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('oops-datedir-repo==0.0.24', 'console_scripts', 'prune')()
    )
