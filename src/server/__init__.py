"""Neighborhood Library Service — gRPC server package.

The `library.v1` package (compiled protobuf/gRPC stubs) lives alongside this
one under src/ and is installed as its own top-level package (see
pyproject.toml), so `from library.v1 import book_pb2` etc. resolves
directly via the editable install — no sys.path manipulation needed.
Regenerate stubs with scripts/generate_proto.py.
"""
