import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
_st=Axes.set_title
def set_title(self,label,*a,**k):
    if k.get("fontsize") is not None and k["fontsize"]<=10 and len(label)<70: return _st(self,label,*a,**k)
    return _st(self,"",*a,**k)
Axes.set_title=set_title
Figure.suptitle=lambda self,*a,**k: None
import runpy; runpy.run_path("/home/user/Hemoglyph/docs/paper1/v7/make_paper_src_figs.py")
