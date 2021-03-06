# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: scanner.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='scanner.proto',
  package='scan',
  syntax='proto3',
  serialized_options=b'\242\002\004SCAN',
  serialized_pb=b'\n\rscanner.proto\x12\x04scan\x1a\x1cgoogle/protobuf/struct.proto\"\x1e\n\x0bScanRequest\x12\x0f\n\x07sess_id\x18\x01 \x01(\t\"0\n\x0bReadRequest\x12\x0f\n\x07sess_id\x18\x01 \x01(\t\x12\x10\n\x08img_path\x18\x02 \x01(\t\"W\n\x0cScanResponse\x12\x0f\n\x07sess_id\x18\x01 \x01(\t\x12\x10\n\x08img_path\x18\x02 \x01(\t\x12$\n\x03\x65rr\x18\x03 \x01(\x0b\x32\x17.google.protobuf.Struct2k\n\x07Scanner\x12/\n\x04Scan\x12\x11.scan.ScanRequest\x1a\x12.scan.ScanResponse\"\x00\x12/\n\x04Read\x12\x11.scan.ReadRequest\x1a\x12.scan.ScanResponse\"\x00\x42\x07\xa2\x02\x04SCANb\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_struct__pb2.DESCRIPTOR,])




_SCANREQUEST = _descriptor.Descriptor(
  name='ScanRequest',
  full_name='scan.ScanRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='sess_id', full_name='scan.ScanRequest.sess_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=53,
  serialized_end=83,
)


_READREQUEST = _descriptor.Descriptor(
  name='ReadRequest',
  full_name='scan.ReadRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='sess_id', full_name='scan.ReadRequest.sess_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='img_path', full_name='scan.ReadRequest.img_path', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=85,
  serialized_end=133,
)


_SCANRESPONSE = _descriptor.Descriptor(
  name='ScanResponse',
  full_name='scan.ScanResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='sess_id', full_name='scan.ScanResponse.sess_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='img_path', full_name='scan.ScanResponse.img_path', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='err', full_name='scan.ScanResponse.err', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=135,
  serialized_end=222,
)

_SCANRESPONSE.fields_by_name['err'].message_type = google_dot_protobuf_dot_struct__pb2._STRUCT
DESCRIPTOR.message_types_by_name['ScanRequest'] = _SCANREQUEST
DESCRIPTOR.message_types_by_name['ReadRequest'] = _READREQUEST
DESCRIPTOR.message_types_by_name['ScanResponse'] = _SCANRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ScanRequest = _reflection.GeneratedProtocolMessageType('ScanRequest', (_message.Message,), {
  'DESCRIPTOR' : _SCANREQUEST,
  '__module__' : 'scanner_pb2'
  # @@protoc_insertion_point(class_scope:scan.ScanRequest)
  })
_sym_db.RegisterMessage(ScanRequest)

ReadRequest = _reflection.GeneratedProtocolMessageType('ReadRequest', (_message.Message,), {
  'DESCRIPTOR' : _READREQUEST,
  '__module__' : 'scanner_pb2'
  # @@protoc_insertion_point(class_scope:scan.ReadRequest)
  })
_sym_db.RegisterMessage(ReadRequest)

ScanResponse = _reflection.GeneratedProtocolMessageType('ScanResponse', (_message.Message,), {
  'DESCRIPTOR' : _SCANRESPONSE,
  '__module__' : 'scanner_pb2'
  # @@protoc_insertion_point(class_scope:scan.ScanResponse)
  })
_sym_db.RegisterMessage(ScanResponse)


DESCRIPTOR._options = None

_SCANNER = _descriptor.ServiceDescriptor(
  name='Scanner',
  full_name='scan.Scanner',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=224,
  serialized_end=331,
  methods=[
  _descriptor.MethodDescriptor(
    name='Scan',
    full_name='scan.Scanner.Scan',
    index=0,
    containing_service=None,
    input_type=_SCANREQUEST,
    output_type=_SCANRESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='Read',
    full_name='scan.Scanner.Read',
    index=1,
    containing_service=None,
    input_type=_READREQUEST,
    output_type=_SCANRESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_SCANNER)

DESCRIPTOR.services_by_name['Scanner'] = _SCANNER

# @@protoc_insertion_point(module_scope)
