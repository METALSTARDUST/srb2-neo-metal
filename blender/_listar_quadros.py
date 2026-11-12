import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import golpes_ref as G
q, sup = G.ler()
ant = None
ini = 0
for i, n in enumerate(q + ["~"]):
    g = n.rstrip("0123456789")
    if g != ant:
        if ant is not None:
            print("%3d-%3d %s" % (ini, i - 1, ant))
        ant, ini = g, i
