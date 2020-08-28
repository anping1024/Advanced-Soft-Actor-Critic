# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: learner.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import ndarray_pb2 as ndarray__pb2
import pingpong_pb2 as pingpong__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='learner.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\rlearner.proto\x1a\rndarray.proto\x1a\x0epingpong.proto\"K\n\x10GetActionRequest\x12\x1a\n\x08obs_list\x18\x01 \x03(\x0b\x32\x08.NDarray\x12\x1b\n\trnn_state\x18\x03 \x01(\x0b\x32\x08.NDarray\"?\n\x06\x41\x63tion\x12\x18\n\x06\x61\x63tion\x18\x01 \x01(\x0b\x32\x08.NDarray\x12\x1b\n\trnn_state\x18\x03 \x01(\x0b\x32\x08.NDarray\"*\n\x0bNNVariables\x12\x1b\n\tvariables\x18\x01 \x03(\x0b\x32\x08.NDarray\"\xe7\x01\n\x11GetTDErrorRequest\x12\x1e\n\x0cn_obses_list\x18\x01 \x03(\x0b\x32\x08.NDarray\x12\x1b\n\tn_actions\x18\x02 \x01(\x0b\x32\x08.NDarray\x12\x1b\n\tn_rewards\x18\x03 \x01(\x0b\x32\x08.NDarray\x12\x1f\n\rnext_obs_list\x18\x04 \x03(\x0b\x32\x08.NDarray\x12\x19\n\x07n_dones\x18\x05 \x01(\x0b\x32\x08.NDarray\x12\x1c\n\nn_mu_probs\x18\x06 \x01(\x0b\x32\x08.NDarray\x12\x1e\n\x0cn_rnn_states\x18\x07 \x01(\x0b\x32\x08.NDarray\"%\n\x07TDError\x12\x1a\n\x08td_error\x18\x01 \x01(\x0b\x32\x08.NDarray2\x85\x02\n\x0eLearnerService\x12\x1f\n\x0bPersistence\x12\x05.Ping\x1a\x05.Pong(\x01\x30\x01\x12\'\n\tGetAction\x12\x11.GetActionRequest\x1a\x07.Action\x12*\n\x12GetPolicyVariables\x12\x06.Empty\x1a\x0c.NNVariables\x12*\n\nGetTDError\x12\x12.GetTDErrorRequest\x1a\x08.TDError\x12&\n\x0eGetNNVariables\x12\x06.Empty\x1a\x0c.NNVariables\x12)\n\x11UpdateNNVariables\x12\x0c.NNVariables\x1a\x06.Emptyb\x06proto3'
  ,
  dependencies=[ndarray__pb2.DESCRIPTOR,pingpong__pb2.DESCRIPTOR,])




_GETACTIONREQUEST = _descriptor.Descriptor(
  name='GetActionRequest',
  full_name='GetActionRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='obs_list', full_name='GetActionRequest.obs_list', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rnn_state', full_name='GetActionRequest.rnn_state', index=1,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=48,
  serialized_end=123,
)


_ACTION = _descriptor.Descriptor(
  name='Action',
  full_name='Action',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='action', full_name='Action.action', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rnn_state', full_name='Action.rnn_state', index=1,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=125,
  serialized_end=188,
)


_NNVARIABLES = _descriptor.Descriptor(
  name='NNVariables',
  full_name='NNVariables',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='variables', full_name='NNVariables.variables', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=190,
  serialized_end=232,
)


_GETTDERRORREQUEST = _descriptor.Descriptor(
  name='GetTDErrorRequest',
  full_name='GetTDErrorRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='n_obses_list', full_name='GetTDErrorRequest.n_obses_list', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='n_actions', full_name='GetTDErrorRequest.n_actions', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='n_rewards', full_name='GetTDErrorRequest.n_rewards', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='next_obs_list', full_name='GetTDErrorRequest.next_obs_list', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='n_dones', full_name='GetTDErrorRequest.n_dones', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='n_mu_probs', full_name='GetTDErrorRequest.n_mu_probs', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='n_rnn_states', full_name='GetTDErrorRequest.n_rnn_states', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=235,
  serialized_end=466,
)


_TDERROR = _descriptor.Descriptor(
  name='TDError',
  full_name='TDError',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='td_error', full_name='TDError.td_error', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=468,
  serialized_end=505,
)

_GETACTIONREQUEST.fields_by_name['obs_list'].message_type = ndarray__pb2._NDARRAY
_GETACTIONREQUEST.fields_by_name['rnn_state'].message_type = ndarray__pb2._NDARRAY
_ACTION.fields_by_name['action'].message_type = ndarray__pb2._NDARRAY
_ACTION.fields_by_name['rnn_state'].message_type = ndarray__pb2._NDARRAY
_NNVARIABLES.fields_by_name['variables'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_obses_list'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_actions'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_rewards'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['next_obs_list'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_dones'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_mu_probs'].message_type = ndarray__pb2._NDARRAY
_GETTDERRORREQUEST.fields_by_name['n_rnn_states'].message_type = ndarray__pb2._NDARRAY
_TDERROR.fields_by_name['td_error'].message_type = ndarray__pb2._NDARRAY
DESCRIPTOR.message_types_by_name['GetActionRequest'] = _GETACTIONREQUEST
DESCRIPTOR.message_types_by_name['Action'] = _ACTION
DESCRIPTOR.message_types_by_name['NNVariables'] = _NNVARIABLES
DESCRIPTOR.message_types_by_name['GetTDErrorRequest'] = _GETTDERRORREQUEST
DESCRIPTOR.message_types_by_name['TDError'] = _TDERROR
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

GetActionRequest = _reflection.GeneratedProtocolMessageType('GetActionRequest', (_message.Message,), {
  'DESCRIPTOR' : _GETACTIONREQUEST,
  '__module__' : 'learner_pb2'
  # @@protoc_insertion_point(class_scope:GetActionRequest)
  })
_sym_db.RegisterMessage(GetActionRequest)

Action = _reflection.GeneratedProtocolMessageType('Action', (_message.Message,), {
  'DESCRIPTOR' : _ACTION,
  '__module__' : 'learner_pb2'
  # @@protoc_insertion_point(class_scope:Action)
  })
_sym_db.RegisterMessage(Action)

NNVariables = _reflection.GeneratedProtocolMessageType('NNVariables', (_message.Message,), {
  'DESCRIPTOR' : _NNVARIABLES,
  '__module__' : 'learner_pb2'
  # @@protoc_insertion_point(class_scope:NNVariables)
  })
_sym_db.RegisterMessage(NNVariables)

GetTDErrorRequest = _reflection.GeneratedProtocolMessageType('GetTDErrorRequest', (_message.Message,), {
  'DESCRIPTOR' : _GETTDERRORREQUEST,
  '__module__' : 'learner_pb2'
  # @@protoc_insertion_point(class_scope:GetTDErrorRequest)
  })
_sym_db.RegisterMessage(GetTDErrorRequest)

TDError = _reflection.GeneratedProtocolMessageType('TDError', (_message.Message,), {
  'DESCRIPTOR' : _TDERROR,
  '__module__' : 'learner_pb2'
  # @@protoc_insertion_point(class_scope:TDError)
  })
_sym_db.RegisterMessage(TDError)



_LEARNERSERVICE = _descriptor.ServiceDescriptor(
  name='LearnerService',
  full_name='LearnerService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=508,
  serialized_end=769,
  methods=[
  _descriptor.MethodDescriptor(
    name='Persistence',
    full_name='LearnerService.Persistence',
    index=0,
    containing_service=None,
    input_type=pingpong__pb2._PING,
    output_type=pingpong__pb2._PONG,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetAction',
    full_name='LearnerService.GetAction',
    index=1,
    containing_service=None,
    input_type=_GETACTIONREQUEST,
    output_type=_ACTION,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetPolicyVariables',
    full_name='LearnerService.GetPolicyVariables',
    index=2,
    containing_service=None,
    input_type=ndarray__pb2._EMPTY,
    output_type=_NNVARIABLES,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetTDError',
    full_name='LearnerService.GetTDError',
    index=3,
    containing_service=None,
    input_type=_GETTDERRORREQUEST,
    output_type=_TDERROR,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetNNVariables',
    full_name='LearnerService.GetNNVariables',
    index=4,
    containing_service=None,
    input_type=ndarray__pb2._EMPTY,
    output_type=_NNVARIABLES,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='UpdateNNVariables',
    full_name='LearnerService.UpdateNNVariables',
    index=5,
    containing_service=None,
    input_type=_NNVARIABLES,
    output_type=ndarray__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_LEARNERSERVICE)

DESCRIPTOR.services_by_name['LearnerService'] = _LEARNERSERVICE

# @@protoc_insertion_point(module_scope)
