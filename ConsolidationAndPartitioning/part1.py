from random import randint, choice
import string


class Block:
    blockId = 0
    data = None

    def __init__(self, blockid):
        self.blockId = blockid

    def read(self):
        return self.data

    def write(self, data):
        if len(str(data)) <= 100:
            self.data = data
            return True
        else:
            print("Writing excess data to block {}".format(self.blockId))
            return False


A = [Block(i) for i in range(0, 201)]
B = [Block(i) for i in range(0, 301)]


def readblock(blockid):
    if 0 < blockid < 201:
        return A[blockid].read()
    elif 200 < blockid < 501:
        return B[blockid-200].read()
    else:
        print("Trying to read with Invalid blockId")
        return False


def writeblock(blockid, data):
    if 0 < blockid < 201:
        return A[blockid].write(data)
    elif 200 < blockid < 501:
        return B[blockid-200].write(data)
    else:
        print("Trying to write to Invalid blockId")
        return False


errors = 0
for i in range(1000):
    blockId = randint(1, 500)
    length = randint(1, 100)
    # print("{}, {}, {}".format(i, blockId, length))
    dataWritten = ''.join(choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))
    success = writeblock(blockId, dataWritten)
    if success:
        dataRead = readblock(blockId)
        print("{}\n{}\n".format(dataWritten, dataRead))
        assert dataRead == dataWritten
    else:
        errors += 1
        print("Writing to block {} failed data={}".format(blockId, dataWritten))

print("Number of writing errors={}".format(errors))
