# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: evolver.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import ndarray_pb2 as ndarray__pb2
import pingpong_pb2 as pingpong__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='evolver.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\revolver.proto\x1a\rndarray.proto\x1a\x0epingpong.proto\"n\n\x16RegisterLearnerRequest\x12\x14\n\x0clearner_host\x18\x02 \x01(\t\x12\x14\n\x0clearner_port\x18\x03 \x01(\x05\x12\x13\n\x0breplay_host\x18\x04 \x01(\t\x12\x13\n\x0breplay_port\x18\x05 \x01(\x05\"3\n\x17RegisterLearnerResponse\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\x05\"\x8f\x01\n\x15RegisterActorResponse\x12\x11\n\tsucceeded\x18\x01 \x01(\x08\x12\x14\n\x0clearner_host\x18\x02 \x01(\t\x12\x14\n\x0clearner_port\x18\x03 \x01(\x05\x12\x13\n\x0breplay_host\x18\x04 \x01(\t\x12\x13\n\x0breplay_port\x18\x05 \x01(\x05\x12\r\n\x05noise\x18\x06 \x01(\x02\",\n\x1aPostRewardToEvolverRequest\x12\x0e\n\x06reward\x18\x01 \x01(\x02\x32\xdb\x01\n\x0e\x45volverService\x12\x1f\n\x0bPersistence\x12\x05.Ping\x1a\x05.Pong(\x01\x30\x01\x12\x44\n\x0fRegisterLearner\x12\x17.RegisterLearnerRequest\x1a\x18.RegisterLearnerResponse\x12/\n\rRegisterActor\x12\x06.Empty\x1a\x16.RegisterActorResponse\x12\x31\n\nPostReward\x12\x1b.PostRewardToEvolverRequest\x1a\x06.Emptyb\x06proto3'
  ,
  dependencies=[ndarray__pb2.DESCRIPTOR,pingpong__pb2.DESCRIPTOR,])




_REGISTERLEARNERREQUEST = _descriptor.Descriptor(
  name='RegisterLearnerRequest',
  full_name='RegisterLearnerRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='learner_host', full_name='RegisterLearnerRequest.learner_host', index=0,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='learner_port', full_name='RegisterLearnerRequest.learner_port', index=1,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='replay_host', full_name='RegisterLearnerRequest.replay_host', index=2,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='replay_port', full_name='RegisterLearnerRequest.replay_port', index=3,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
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
  serialized_end=158,
)


_REGISTERLEARNERRESPONSE = _descriptor.Descriptor(
  name='RegisterLearnerResponse',
  full_name='RegisterLearnerResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='RegisterLearnerResponse.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='RegisterLearnerResponse.id', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=160,
  serialized_end=211,
)


_REGISTERACTORRESPONSE = _descriptor.Descriptor(
  name='RegisterActorResponse',
  full_name='RegisterActorResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='succeeded', full_name='RegisterActorResponse.succeeded', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='learner_host', full_name='RegisterActorResponse.learner_host', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='learner_port', full_name='RegisterActorResponse.learner_port', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='replay_host', full_name='RegisterActorResponse.replay_host', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='replay_port', full_name='RegisterActorResponse.replay_port', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='noise', full_name='RegisterActorResponse.noise', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
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
  serialized_start=214,
  serialized_end=357,
)


_POSTREWARDTOEVOLVERREQUEST = _descriptor.Descriptor(
  name='PostRewardToEvolverRequest',
  full_name='PostRewardToEvolverRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='reward', full_name='PostRewardToEvolverRequest.reward', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
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
  serialized_start=359,
  serialized_end=403,
)

DESCRIPTOR.message_types_by_name['RegisterLearnerRequest'] = _REGISTERLEARNERREQUEST
DESCRIPTOR.message_types_by_name['RegisterLearnerResponse'] = _REGISTERLEARNERRESPONSE
DESCRIPTOR.message_types_by_name['RegisterActorResponse'] = _REGISTERACTORRESPONSE
DESCRIPTOR.message_types_by_name['PostRewardToEvolverRequest'] = _POSTREWARDTOEVOLVERREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

RegisterLearnerRequest = _reflection.GeneratedProtocolMessageType('RegisterLearnerRequest', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERLEARNERREQUEST,
  '__module__' : 'evolver_pb2'
  # @@protoc_insertion_point(class_scope:RegisterLearnerRequest)
  })
_sym_db.RegisterMessage(RegisterLearnerRequest)

RegisterLearnerResponse = _reflection.GeneratedProtocolMessageType('RegisterLearnerResponse', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERLEARNERRESPONSE,
  '__module__' : 'evolver_pb2'
  # @@protoc_insertion_point(class_scope:RegisterLearnerResponse)
  })
_sym_db.RegisterMessage(RegisterLearnerResponse)

RegisterActorResponse = _reflection.GeneratedProtocolMessageType('RegisterActorResponse', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERACTORRESPONSE,
  '__module__' : 'evolver_pb2'
  # @@protoc_insertion_point(class_scope:RegisterActorResponse)
  })
_sym_db.RegisterMessage(RegisterActorResponse)

PostRewardToEvolverRequest = _reflection.GeneratedProtocolMessageType('PostRewardToEvolverRequest', (_message.Message,), {
  'DESCRIPTOR' : _POSTREWARDTOEVOLVERREQUEST,
  '__module__' : 'evolver_pb2'
  # @@protoc_insertion_point(class_scope:PostRewardToEvolverRequest)
  })
_sym_db.RegisterMessage(PostRewardToEvolverRequest)



_EVOLVERSERVICE = _descriptor.ServiceDescriptor(
  name='EvolverService',
  full_name='EvolverService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=406,
  serialized_end=625,
  methods=[
  _descriptor.MethodDescriptor(
    name='Persistence',
    full_name='EvolverService.Persistence',
    index=0,
    containing_service=None,
    input_type=pingpong__pb2._PING,
    output_type=pingpong__pb2._PONG,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='RegisterLearner',
    full_name='EvolverService.RegisterLearner',
    index=1,
    containing_service=None,
    input_type=_REGISTERLEARNERREQUEST,
    output_type=_REGISTERLEARNERRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='RegisterActor',
    full_name='EvolverService.RegisterActor',
    index=2,
    containing_service=None,
    input_type=ndarray__pb2._EMPTY,
    output_type=_REGISTERACTORRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='PostReward',
    full_name='EvolverService.PostReward',
    index=3,
    containing_service=None,
    input_type=_POSTREWARDTOEVOLVERREQUEST,
    output_type=ndarray__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_EVOLVERSERVICE)

DESCRIPTOR.services_by_name['EvolverService'] = _EVOLVERSERVICE

# @@protoc_insertion_point(module_scope)
