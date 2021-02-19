import os


def find_files(directory=os.getcwd()):
    for file in os.listdir(directory):
        path = os.path.join(directory,file)
        if os.path.isfile(path):
            yield path
        elif os.path.isdir(path):
            yield from find_files(path)

def lines_of_code():
    count = 0
    for file in find_files():
        with open(file, 'r') as f:
            try:
                lines = f.readlines()
                count += len(lines)
            except:
                pass
    return count

def adv_dir(obj, dep=0, ignore=set()):
    for attr in dir(obj):
        value = getattr(obj, attr)
        if not attr.startswith('_'):
            yield ' '.join([
                ' - ' * dep,
                attr,
                str(value),
                str(type(value))
            ])
            if type(value) not in ignore:
                ignore.add(type(value))
                yield from adv_dir(value, dep+1, ignore)


