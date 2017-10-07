# yamlstruct

This library allows you to create struct definitions in YAML files and pack/unpack from/to python ordered dicts. In other words, it allows you to encode / decode binary data using a YAML specification.

example yaml file:
```
type: 0x01
value1: UInt8
value2: UInt8
```

example Python code:
```
import yamlstruct.yamlstruct
yamlstructs = yamlstruct.yamlstruct.YamlStructs()
p = b'\x01\x02\x03'
with open("example.yaml") as f:
    yamlstructs.append(yamlstruct.yamlstruct.YamlStruct("Example", f)
y = yamlstructs.best_unpack(p)
print(y.unpack(p))
```

# data types

You can use the following data types:
- Bit
- UInt8
- FixedInt8 (just use a number)
- FixedString (see type definition)
- Enum

# Bit

This field should be repeated eight times like this:
```
bit1: Bit
bit2: Bit
bit3: Bit
bit4: Bit
bit5: Bit
bit6: Bit
bit7: Bit
bit8: Bit
```

# UInt8

This specifies a 8 bit byte:
```
value: UInt8
```

# FixedInt8
This also specifies a 8 bit byte which is always the same for this structure.

```
value: 0xde
```

# FixedString

This field specifies a fixed size string:
```
message:
    Type: String
    Value: "Hello World"
```

# Enum

This field specifies an enum:
```
Color:
    Type: Enum
    Enum:
        Black: 0x00
        Red: 0x01
        Green: 0x20
        Blue: 0x22
        White: 0xFF
```
