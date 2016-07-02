import time

def log(*args):
    tt = time.strftime(r'%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
    print(tt, *args)
# import hashlib
#
# a = hashlib.sha1('admin'.encode('utf-8')).hexdigest()
# print(a)
