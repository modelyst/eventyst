import hashlib
import io

import avro.io
from avro import schema

# Define a schema for a parent object that has a list of children

# Define a schema for the child objects
child_schema = schema.parse(
    '''
{
    "type": "record",
    "name": "Child",
    "namespace": "my.namespace",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "name", "type": "string"}
    ]
}
'''
)
parent_schema = schema.parse(
    '''
{
    "type": "record",
    "name": "Parent",
    "namespace": "my.namespace.foo",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "children", "type": {"type": "array", "items":{
    "type": "record",
    "name": "Test",
    "namespace": "my.namespace",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "name", "type": "string"}
    ]
}}}
    ]
}

'''
)


# Create some data to encode
parent_data = {
    "id": "parent-1",
    "children": [{"id": "child-2", "name": "Alice"}, {"id": "child-2", "name": "Bob"}],
}

# Create an Avro writer that uses the parent schema
writer = avro.io.DatumWriter(parent_schema)

# Encode the data using the writer
bytes_writer = io.BytesIO()
encoder = avro.io.BinaryEncoder(bytes_writer)
writer.write(parent_data, encoder)
encoded_data = bytes_writer.getvalue()

# Create an Avro reader that uses the parent schema
reader = avro.io.DatumReader(parent_schema)

# Decode the data using the reader
bytes_reader = io.BytesIO(encoded_data)

decoder = avro.io.BinaryDecoder(bytes_reader)
decoded_data = reader.read(decoder)

# Print the decoded data
print(decoded_data)

# Print the hash of the encoded data
print(hashlib.sha256(encoded_data).hexdigest())
