import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import usuario_neo as U
import perna_poses as PP
U.preparar()
U.repouso()
arm = U.armadura()
M = arm.matrix_world
for lado in ("direito", "esquerdo"):
    o = PP.ossos_perna(lado)
    print("== perna", lado)
    for k, pb in o.items():
        b = pb.bone
        h, t = M @ b.head_local, M @ b.tail_local
        print("%-10s %-40s pai=%-28s head %s tail %s len %.3f" % (k, pb.name, pb.parent.name if pb.parent else None, tuple(round(x, 3) for x in h), tuple(round(x, 3) for x in t), b.length))
for pb in arm.pose.bones:
    if pb.parent is None:
        b = pb.bone
        print("RAIZ", pb.name, tuple(round(x, 3) for x in (M @ b.head_local)), tuple(round(x, 3) for x in (M @ b.tail_local)))
