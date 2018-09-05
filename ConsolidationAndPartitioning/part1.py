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
        else:
            print("Writing excess data to block {}".format(self.blockId))


A = [Block(i) for i in range(0, 201)]
B = [Block(i) for i in range(0, 301)]


def readblock(blockid):
    if 0 < blockid < 201:
        return A[blockid].read()
    elif 200 < blockid < 501:
        return B[blockid].read()
    else:
        print("Trying to read with Invalid blockId")


def writeblock(blockid, data):
    if 0 < blockid < 201:
        return A[blockid].write(data)
    elif 200 < blockid < 501:
        return B[blockid].write(data)
    else:
        print("Trying to write to Invalid blockId")
