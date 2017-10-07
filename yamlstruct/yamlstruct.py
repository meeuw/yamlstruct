#!/usr/bin/env python3
import yaml
import struct
from builtins import super
from collections import OrderedDict

# https://stackoverflow.com/a/21912744/200071
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


class UInt8(object):
    def __init__(self, key):
        self.key = key


    def packfmt(self):
        return 'B'


    def rank_match(self, value):
        return False


    def unpack(self, value):
        return {self.key: value}


    def pack(self, value):
        return value


    @staticmethod
    def definedas(value):
        return value == 'UInt8'


class FixedUInt8(UInt8):
    def __init__(self, key, value):
        super().__init__(key)
        self.value = value


    def rank_match(self, value):
        return self.value == value


    @staticmethod
    def definedas(value):
        return isinstance(value, int)


class Bit(UInt8):
    def __init__(self, keys, values):
        self.keys = keys
        value = 0
        for i, flag in enumerate(values):
            value += flag << i
        self.value = value


    def unpack(self, value):
        result = {}
        for i, key in enumerate(self.keys):
            bitvalue = (1 << i)
            result[key] = value & bitvalue == bitvalue
        return result


    def pack(self, values):
        result = 0
        for i, value in enumerate(values):
            result += (value << i)
        return result


    @staticmethod
    def definedas(value):
        return isinstance(value, bool) or value == 'Bit'


class Enum(UInt8):
    def __init__(self, key, value):
        self.key = key
        self.enumeration = value["Enum"]


    def unpack(self, value):
        for k, v in self.enumeration.items():
            if value == v:
                return {self.key: k}
        print("{} {} not found".format(self.key, value))


    def pack(self, value):
        return self.enumeration[value]


    @staticmethod
    def definedas(value):
        return isinstance(value, dict) and "Type" in value and value["Type"] == "Enum"


class FixedString(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value["Value"]


    def unpack(self, value):
        return {self.key: self.value}


    def pack(self, value):
        return value


    def packfmt(self):
        return '{}s'.format(len(self.value))


    def rank_match(self, value):
        return False


    @staticmethod
    def definedas(value):
        return isinstance(value, dict) and "Type" in value and value["Type"] == "FixedString"

class YamlStruct:
    def __init__(self, name, f):
        self.fields = []
        self.fieldnames = []
        self.name = name
        self.yamlstruct = ordered_load(f, yaml.SafeLoader)
        flagkeys = []
        flagvalues = []
        for key, value in self.yamlstruct.items():
            self.fieldnames.append(key)
            if Bit.definedas(value):
                flagkeys.append(key)
                if value != 'Bit': flagvalues.append(value)
                if len(flagkeys) == 8:
                    self.fields.append(Bit(flagkeys, flagvalues))
                    flagkeys = []
                    flagvalues = []
            elif FixedUInt8.definedas(value):
                self.fields.append(FixedUInt8(key, value))
            elif UInt8.definedas(value):
                self.fields.append(UInt8(key))
            elif Enum.definedas(value):
                self.fields.append(Enum(key, value))
            elif FixedString.definedas(value):
                self.fields.append(FixedString(key, value))
            else:
                assert False, "unknown {} {} {}".format(name, key, value)
        self.packfmt = "".join(field.packfmt() for field in self.fields)


    def unpack_rank(self, data):
        if struct.calcsize(self.packfmt) != len(data):
            return 0
        score = 0
        for i, value in enumerate(struct.unpack(self.packfmt, data)):
            if self.fields[i].rank_match(value): score += 1
        return score


    def unpack(self, data):
        result = {}
        values = struct.unpack(self.packfmt, data)
        for i, field in enumerate(self.fields):
            d = field.unpack(values[i])
            if d is None:
                print(self.name, field)
            result.update(d)
        return result


    def pack_rank(self, data):
        score = 0
        flagvalues = []
        values = []
        i = 0
        for key, value in self.yamlstruct.items():
            if not key in data:
                return 0
            if value == 'Bit':
                flagvalues.append(data[key])
                if len(flagvalues) == 8:
                    values.append(self.fields[i].pack(flagvalues))
                    flagvalues = []
                    i += 1
            else:
                values.append(self.fields[i].pack(data[key]))
                i += 1
        for i, value in enumerate(values):
            if self.fields[i].rank_match(value): score += 1
        return score


    def pack(self, data):
        flagvalues = []
        values = []
        i = 0
        for key, value in self.yamlstruct.items():
            if value == 'Bit':
                flagvalues.append(data[key])
                if len(flagvalues) == 8:
                    values.append(self.fields[i].pack(flagvalues))
                    flagvalues = []
                    i += 1
            elif FixedString.definedas(value):
                values.append(value["Value"].encode('utf8'))
                i += 1
            elif FixedUInt8.definedas(value):
                values.append(value)
                i += 1
            else:
                values.append(self.fields[i].pack(data[key]))
                i += 1
        return struct.pack(self.packfmt, *values)


    def __str__(self):
        return "YamlStruct {}".format(self.name)


    def calcsize(self):
        return struct.calcsize(self.packfmt)


class YamlStructs:
    def __init__(self):
        self.yamlstructs = {}


    def best_unpack(self, data):
        best_score = -1
        best_yamlstruct = None
        for name, yamlstruct in self.yamlstructs.items():
            score = yamlstruct.unpack_rank(data)
            if score > best_score:
                best_score = score
                best_yamlstruct = yamlstruct
        if best_score == 0:
            return None
        else:
            return best_yamlstruct


    def pack(self, values):
        best_score = -1
        best_yamlstruct = None
        for name, yamlstruct in self.yamlstructs.items():
            score = yamlstruct.pack_rank(values)
            if score > best_score:
                best_score = score
                best_yamlstruct = yamlstruct
        assert score != 0, "score 0"
        return best_yamlstruct.pack(values)


    def append(self, yamlstruct):
        self.yamlstructs[yamlstruct.name] = yamlstruct


if __name__ == '__main__':
    import tst
