import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_medir_soco_3.py")).read().split("for ref in")[0])
print("residuo Kabsch por ilha da luva P e do punho P (parado 219 -> quadro)")
for f in (277, 278, 279):
    print("quadro", f)
    for ilha in [44, 47, 48, 49, 50, 52, 53, 54, 34, 35, 36, 37]:
        g = [(0, [ilha])]
        p0, p1 = pontos(g, 219), pontos(g, f)
        if len(p0) < 4:
            continue
        r, ca, cb, res = kabsch(p0, p1)
        e0, e1 = p0.max(0) - p0.min(0), p1.max(0) - p1.min(0)
        print("  ilha %2d n=%3d res=%.3f  ext parado=(%.2f %.2f %.2f) ext=(%.2f %.2f %.2f)" % (ilha, len(p0), res, *e0, *e1))
