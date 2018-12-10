from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from collections import OrderedDict

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import Frame


if matplotlib.get_backend() != 'module://backend_interagg':
  matplotlib.use("TkAgg")


class CriteriaFigure(Frame):
  # Configurations of LossFigure widget
  WIDTH = 500
  HEIGHT = 400
  PCT_PER_STEP = 0.05
  SLIDER_WIDTH = 0.05

  def __init__(self, master, **kwargs):
    # Call parent's constructor
    Frame.__init__(self, master)

    # Attributes
    self._step = None
    self._criteria = OrderedDict()
    self._cursor = None
    self.related_variable_viewer = None

    # Layout
    self.figure = None
    self.subplot = None
    self.figure_canvas = None
    self.tk_canvas = None

    self.scroll_bar = None

    # Define layout
    self._create_layout()

  # region : Properties

  @property
  def length(self):
    if self._step is None: return 0
    assert isinstance(self._step, np.ndarray)
    return self._step.size

  @property
  def cursor(self):
    return 0 if self._cursor is None else self._cursor

  # endregion : Properties

  # region : Public Methods

  def set_context(self, step, criteria):
    # Sanity check
    if isinstance(step, (list, tuple)): step = np.array(step)
    assert isinstance(step, np.ndarray) and isinstance(criteria, OrderedDict)
    assert len(step.shape) == 1
    for k, v in criteria.items():
      assert isinstance(v, np.ndarray) and len(v.shape) == 1
      assert v.size == step.size

    # Set step and loss
    self._step = step
    self._criteria = criteria
    self._cursor = 0

    # Refresh figure
    self.refresh()

  def refresh(self):
    if self._step is None or len(self._criteria) == 0: return

    # Set slider bar
    self._set_slider()

    # Clear subplot
    self.subplot.cla()
    self.subplot.set_xlabel('Epoch')
    self.subplot.set_ylabel('Criteria')

    # Plot criteria
    assert 0 <= self._cursor < len(self._step)
    step = self._step[self._cursor]

    criterion_strings = []
    mark_list = []
    for name, criterion in self._criteria.items():
      # Plot curve
      self.subplot.plot(self._step, criterion)
      # Get string and mark
      val = criterion[self._cursor]
      criterion_strings.append('{} = {:.3f}'.format(name, val))
      mark_list += [step, val, 'rs']
    self.subplot.legend(list(self._criteria.keys()), loc='best')

    # Set title and plot markers
    self.subplot.set_title(', '.join(criterion_strings))
    self.subplot.plot(*mark_list)

    # Tight layout
    # self.figure.tight_layout()
    # Draw update on canvas
    self.figure_canvas.draw()

    # Refresh related variable viewer if necessary
    if self.related_variable_viewer is not None:
      self.related_variable_viewer.refresh()

  # endregion : Public Methods

  # region : Events

  def on_scroll(self, action, *args):
    if self._step is None or self._criteria is None:
      return

    moveto = 'moveto'
    scroll = 'scroll'
    assert action in (moveto, scroll)

    # Set cursor corresponding to action
    if action == moveto:
      # offset \in [0.0, 1.0 - SLIDER_WIDTH]
      offset = float(args[0]) / (1.0 - self.SLIDER_WIDTH)
      offset = min(offset, 1.0)
      self._cursor = int(np.round(offset * (len(self._step) - 1)))
    elif action == scroll:
      # step \in {-1, 1}
      step, what = args
      step = int(step)
      if isinstance(what, str) and what == 'tiny':
        index = self._cursor + step
      else: index = self._cursor + np.round(
        step * self.PCT_PER_STEP * len(self._step))
      index = min(max(0, index), len(self._step) - 1)
      if index == self._cursor: return
      else: self._cursor = int(index)

    # Refresh subplot
    self.refresh()

  # endregion : Events

  # region : Private Methods

  def _create_layout(self):
    # Create figure canvas
    self.figure = plt.Figure()
    self.figure.set_facecolor('white')

    self.subplot = self.figure.add_subplot(111)
    self.subplot.set_xlabel('Epoch')
    self.subplot.set_ylabel('Criteria')

    self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
    self.figure_canvas.show()

    self.tk_canvas = self.figure_canvas.get_tk_widget()
    self.tk_canvas.configure(height=self.HEIGHT, width=self.WIDTH)
    self.tk_canvas.pack(fill=tk.BOTH)

    # Create scroll bar
    scroll_bar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
    scroll_bar.pack(fill=tk.X, side=tk.BOTTOM)
    self.scroll_bar = scroll_bar
    self.scroll_bar.configure(command=self.on_scroll)

  def _set_slider(self):
    """ Set slider position according to index
    """
    # Calculate relative index \in [0.0, 1.0]
    rel_index = 1. * self._cursor / (self.length - 1)
    rel_index *= (1 - self.SLIDER_WIDTH)

    lo = max(0.0, rel_index)
    hi = min(1.0, rel_index + self.SLIDER_WIDTH)
    self.scroll_bar.set(lo, hi)

  # endregion : Private Methods


if __name__ == '__main__':
  t = np.arange(-2, 2, step=0.01)
  criteria = OrderedDict()
  criteria['y_sin'] = np.sin(t)
  criteria['y_cos'] = np.cos(t)

  root = tk.Tk()
  root.bind('<Escape>', lambda _: root.quit())

  cf = CriteriaFigure(root)
  cf.pack(fill=tk.BOTH)
  cf.master.title('Criteria Figure')
  cf.set_context(t, criteria)

  root.mainloop()


"""
slider offset range: [0, SLIDER_WIDTH]
"""