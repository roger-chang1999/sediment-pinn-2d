"""SSC-PINNs：二維水深平均懸浮載濃度 PINNs（單向耦合，水理場為已知可微函數）。"""
from .model import SSCNet
from .physics import Hydro, ssc_residual, total_mass
