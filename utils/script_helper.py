from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from subprocess import call

from tframe.config import Flag
from tframe.trainers import SmartTrainerHub


flags = [attr for attr in
         [getattr(SmartTrainerHub, key) for key in dir(SmartTrainerHub)]
         if isinstance(attr, Flag)]
flag_names = [f._name for f in flags]

def check_flag_name(method):
  def wrapper(obj, flag_name, *args, **kwargs):
    if flag_name not in flag_names:
      print(
        ' ! `{}` may be an invalid flag, press [Enter] to continue ...'.format(
          flag_name))
      input()
    method(obj, flag_name, *args, **kwargs)
  return wrapper


class Helper(object):

  def __init__(self, module_name):
    self.module_name = module_name
    self._check_module()

    self.public_args = ['python', module_name]
    self.hyper_parameters = {}

  # region : Public Methods

  @check_flag_name
  def register_public_flag(self, flag_name, val):
    self.public_args.append(self._get_config_string(flag_name, val))

  @check_flag_name
  def register_hyper_parameters(self, flag_name, vals):
    assert isinstance(vals, (list, tuple))
    self.hyper_parameters[flag_name] = vals

  def run(self, times=1):
    for _ in range(times):
      for hyper in self._hyper_parameter_lists():
        call(self.public_args + hyper)
        print()

  # endregion : Public Methods

  # region : Private Methods

  @staticmethod
  def _get_config_string(flag_name, val):
    return '--{}={}'.format(flag_name, val)

  def _check_module(self):
    if not os.path.exists(self.module_name):
      raise AssertionError(
        '!! module {} does not exist'.format(self.module_name))

  def _hyper_parameter_lists(self, keys=None):
    if keys is None: keys = list(self.hyper_parameters.keys())
    if len(keys) == 0: yield []
    else:
      for val in self.hyper_parameters[keys[0]]:
        cfg_str = self._get_config_string(keys[0], val)
        for cfg_list in self._hyper_parameter_lists(keys[1:]):
          yield [cfg_str] + cfg_list

  # endregion : Private Methods