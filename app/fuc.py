import json
import os


def noneToInt(num):
    if num is None:
        return 0
    return num


def noneToNull(num):
    if num is None:
        return ''
    return num


def extendedInfoToArray(extended_info):
    if extended_info is None:
        return []
    return extended_info.split(',')


def extendedInfoArrayAdd(extended_info, value):
    arr = extendedInfoToArray(extended_info)
    if value not in arr:
        arr.append(value)
    return ','.join(arr)


def extendedInfoToDic(extended_info):
    dic = {}
    if extended_info is not None:
        dic = json.loads(extended_info)
    return dic


def extendedInfoAdd(extended_info, key, value):
    json_dic = extendedInfoToDic(extended_info)
    json_dic[key] = value
    return json.dumps(json_dic)


def safe_copy(out_dir, name, form):
    if not os.path.exists(os.path.join(out_dir, name)):
        form.file.data.save(os.path.join(out_dir, name))
    else:
        base, extension = os.path.splitext(name)
        i = 1
        while os.path.exists(os.path.join(out_dir, '{}_{}{}'.format(base, i, extension))):
            i += 1
        form.file.data.save(os.path.join(out_dir, '{}_{}{}'.format(base, i, extension)))
