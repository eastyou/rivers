"""支持 ``python -m rivers`` 运行。"""

import sys

from rivers.cli import main

if __name__ == "__main__":
    sys.exit(main())
