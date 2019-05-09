from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

import tframe as tfr

from .flag import Flag
from .model_configs import ModelConfigs
from .trainer_configs import TrainerConfigs
from .note_configs import NoteConfigs
from .rnn_configs import RNNConfigs
from .monitor_configs import MonitorConfigs
from .cloud_configs import CloudConfigs
from .dataset_configs import DataConfigs


class Config(
  ModelConfigs,
  TrainerConfigs,
  NoteConfigs,
  RNNConfigs,
  MonitorConfigs,
  CloudConfigs,
  DataConfigs,
):
  registered = False

  record_dir = Flag.string('records', 'Root path for records')
  log_folder_name = Flag.string('logs', '...')
  ckpt_folder_name = Flag.string('checkpoints', '...')
  snapshot_folder_name = Flag.string('snapshots', '...')

  job_dir = Flag.string(
    './records', 'The root directory where the records should be put',
    name='job-dir')
  data_dir = Flag.string('', 'The data directory')

  dtype = Flag.whatever(tf.float32, 'Default dtype for tensors', is_key=None)
  tb_port = Flag.integer(6006, 'Tensorboard port number')
  show_structure_detail = Flag.boolean(False, '...')

  # logging will be suppressed if this flag is set to True when agent
  #   is launching a model
  suppress_logging = Flag.boolean(
    True, 'Whether to set logging level down to get rid of the device '
          'information')
  progress_bar = Flag.boolean(True, 'Whether to show progress bar')

  keep_trainer_log = Flag.boolean(
    False, 'Whether to keep trainer logs. Usually be used for probe '
           'methods')

  # Device related config
  visible_gpu_id = Flag.string(
    None, 'CUDA_VISIBLE_DEVICES option', name='gpu_id')
  allow_growth = Flag.boolean(True, 'tf.ConfigProto().gpu_options.allow_growth')
  gpu_memory_fraction = Flag.float(
    0.4, 'config.gpu_options.per_process_gpu_memory_fraction')

  # Other fancy stuff
  int_para_1 = Flag.integer(0, 'Used to pass an integer parameter using '
                               ' command line')
  bool_para_1 = Flag.boolean(False, 'Used to pass a boolean parameter using'
                                    ' command line')
  alpha = Flag.float(0.0, 'Alpha', is_key=None)
  beta = Flag.float(0.0, 'Beta', is_key=None)
  gamma = Flag.float(0.0, 'Gamma', is_key=None)
  epsilon = Flag.float(0.0, 'Epsilon', is_key=None)
  delta = Flag.float(0.0, 'Delta', is_key=None)

  def __init__(self, as_global=False):
    # Try to register flags into tensorflow
    if not self.__class__.registered:
      self.__class__.register()

    if as_global:
      tfr.hub.redirect(self)

  # region : Properties

  @property
  def should_create_path(self):
    return self.train and not self.on_cloud

  @property
  def key_options(self):
    ko = {}
    for name in self.__dir__():
      if name in ('key_options', 'config_strings'): continue
      attr = self.get_attr(name)
      if not isinstance(attr, Flag): continue
      if attr.is_key:
        ko[name] = attr.value
    return ko

  @property
  def config_strings(self):
    return sorted(['{}: {}'.format(k, v) for k, v in self.key_options.items()])

  # endregion : Properties

  # region : Override

  def __getattribute__(self, name):
    attr = object.__getattribute__(self, name)
    if not isinstance(attr, Flag): return attr
    else: return attr.value

  def __setattr__(self, name, value):
    # If attribute is not found (say during instance initialization),
    # .. use default __setattr__
    if not hasattr(self, name):
      object.__setattr__(self, name, value)
      return

    # If attribute is not a Flag, use default __setattr__
    attr = object.__getattribute__(self, name)
    if not isinstance(attr, Flag):
      object.__setattr__(self, name, value)
      return

    # Now attr is definitely a Flag
    # if name == 'visible_gpu_id':
    #   import os
    #   assert isinstance(value, str)
    #   os.environ['CUDA_VISIBLE_DEVICES'] = value

    if attr.frozen and value != attr._value:
      raise AssertionError(
        '!! config {} has been frozen to {}'.format(name, attr._value))
    # If attr is a enum Flag, make sure value is legal
    if attr.is_enum:
      if value not in list(attr.enum_class):
        raise TypeError(
          '!! Can not set {} for enum flag {}'.format(value, name))

    attr._value = value
    if attr.ready_to_be_key: attr._is_key = True

    # Replace the attr with a new Flag TODO: tasks with multi hubs?
    # object.__setattr__(self, name, attr.new_value(value))


  # endregion : Override

  # region : Public Methods

  @classmethod
  def register(cls):
    queue = {key: getattr(cls, key) for key in dir(cls)
             if isinstance(getattr(cls, key), Flag)}
    for name, flag in queue.items():
      if flag.should_register: flag.register(name)
      elif flag.name is None: flag.name = name
    cls.registered = True

  def redirect(self, config):
    """Redirect self to config"""
    assert isinstance(config, Config)

    # flag_names = [name for name, value in self.__dict__.items()
    #               if isinstance(value, Flag)]

    flag_names = [name for name in config.__dir__()
                  if hasattr(config, name) and
                  isinstance(object.__getattribute__(config, name), Flag)]
    for name in flag_names:
      # value = getattr(config, name)
      # Set flag to self

      object.__setattr__(self, name, config.get_flag(name))

      # Assign value to self.flag
      # self.__setattr__(name, value)

  def smooth_out_conflicts(self):
    self.smooth_out_cloud_configs()
    self.smooth_out_monitor_configs()
    self.smooth_out_note_configs()
    self.smooth_out_model_configs()

    if self.export_dl_dx or self.export_dl_ds_stat:
      self.allow_loss_in_loop = True
    if self.prune_on and self.pruning_iterations > 0:
      self.overwrite = False

  def get_attr(self, name):
    return object.__getattribute__(self, name)

  def get_flag(self, name):
    flag = super().__getattribute__(name)
    if not isinstance(flag, Flag):
      raise TypeError('!! flag {} not found'.format(name))
    return flag

  def get_optimizer(self):
    from tframe.optimizers.clip_opt import GradientClipOptimizer
    assert self.optimizer is not None and self.learning_rate is not None
    optimizer = self.optimizer(self.learning_rate)
    if self.clip_threshold > 0:
      assert self.clip_method in ('norm', 'value', 'global_norm', 'avg_norm')
      optimizer = GradientClipOptimizer(
        optimizer, self.clip_threshold, method=self.clip_method)
    return optimizer

  # endregion : Public Methods

Config.register()
