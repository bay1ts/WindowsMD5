__author__ = 'noway'

import hashlib
import os
import shelve
import time

#byte size
CHUNK_SIZE = 4096


def md5(file_name):
#Compute md5 of file CONTENTS
#   file_name - path to file (ex. /Users/123/Desktop/file.txt)
#Result:
#   128-bit hex string = md5 hash

    hash_md5 = hashlib.md5()
    with open(file_name) as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), ''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def update_hash_names(path):
#Produce SHELVE-database with dictionary [HASH:PATH]
#   path - path to the dictionary where all files and subdir should be hashed
#Result:
#   Database named 'names_db'
    names_db = shelve.open('names_db')
    for root, dirs, files in os.walk(path):
        for name in files:
            file = root + "\\" + name
            hash_name = hashlib.md5(file).hexdigest()
            if not names_db.has_key(hash_name):
                names_db[hash_name] = file
    names_db.close()


def compute_dir_hash(path, progress_bar=False):
#Produce SHELVE-database with dictionary [HASH1:HASH2]
#Where HASH1 is hash of path to file, HASH2 is hash of file contents
#   path - path to the directory to be hashed
#   (optional)progress_bar - set True if you want to see
#       approximate progress (MAY USE ADDITIONAL TIME)
#Result:
#   Database named [path to directory]_db
    print "Updating hash:path table... ",
    update_hash_names(path)
    print "Done"
    counter = 0
    counter_saved = 0
    if progress_bar:
        print "Computing all files in directory " + path + " and subdir..."
        for root, dirs, files in os.walk(path):
            for name in files:
                counter += 1
        print "There are " + str(counter) + " files to be aggregated"
        counter_saved = counter
        counter = 0

    print "Hashing directory " + path + " and all subdir contents"
    dir_db = shelve.open(str(path + '_db').replace(":", '').replace("\\", ''))

    for root, dirs, files in os.walk(path):
        for name in files:
            if progress_bar:
                counter += 1
                print "\r{0} of {1} completed".format(counter, counter_saved),

            #file_path = root + "/" + name        #MAC OS
            file_path = root + "\\" + name      #WIN

            hash_name = hashlib.md5(file_path).hexdigest()

            try:
                hash_value = md5(file_path)
            except IOError:
                print "Permission Denied to compute md5 hash of " + file_path
            else:
                if not hash_name in dir_db:
                    dir_db[hash_name] = hash_value
    dir_db.close()


def get_path(hash):
    names_db = shelve.open('names_db')
    if hash in names_db:
        ret = names_db[hash]
    else:
        ret = "MISS FILE PATH"
    names_db.close()
    return ret


#Return True if should be excluded
#Return False if should be printed
def verify(path):
    if "Windows\ServiceProfiles\LocalService\AppData\Local\Temp" in path or \
    "Windows\System32\config\systemprofile\AppData\Local\Microsoft\Windows\Temporary Internet Files" in path or \
    "Windows\winsxs\Temp" in path or \
    "Windows\System32\LogFiles" in path or \
    "Windows\System32\WDI\LogFiles" in path or \
    "Windows\System32\winevt\Logs" in path or \
    "Windows\SoftwareDistribution\DataStore\Logs" in path or \
    "Windows\System32\wfp" in path or \
    "Windows\ServiceProfiles" in path or \
    ".log" in path.lower():
        return True
    else:
        return False


def check_backup(path):
    if "C:\Windows\winsxs\Backup" in path:
        return True
    else:
        return False


def diff_db(old_db_name, new_db_name, log_path, use_mask=False):
    f = open(log_path, 'w')
    old_db = shelve.open(old_db_name)
    new_db = shelve.open(new_db_name)
    backup_data = ""
    if cmp(old_db, new_db) == 0:
        print "\nNo changes in the directory"
    else:
        print "\nThere are some changes in the directory"
        for key in old_db.keys():
            path = get_path(key)
            if use_mask and verify(path):
                new_db[key] = 0
                continue
            if not key in new_db:
                result = "The file " + path + " was removed\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
            elif old_db[key] != new_db[key]:
                result = "The file " + path + " was updated\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
                new_db[key] = 0
            else:
                new_db[key] = 0
                continue

        for key in new_db.keys():
            if not new_db[key] == 0:
                result = "The file " + path + " was created\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
                new_db[key] = 0
        f.write("\nChanges in backup folder:\n" + backup_data)


def speed_test(path):
    timer = time.time()
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = root + "\\" + name
            hash_value = md5(file_path)
    print str(time.time() - timer)
compute_dir_hash('C:\Windows', progress_bar=True)
#compute_dir_hash('/Users/pontifik/Desktop/Work', progress_bar=True)
diff_db('CWindowsold_db', 'CWindows_db', 'log.txt', use_mask=True)
#speed_test('C:\Python27')
print "DONE"
