#!/usr/bin/env python3

import os
try:
    os.system("rm high.csv && rm low.csv && rm open.csv && rm close.csv && rm volume.csv && rm adj_close.csv")
except:
    os.system("rm out.csv")