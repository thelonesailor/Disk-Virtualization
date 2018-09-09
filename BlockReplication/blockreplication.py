from random import randint


class Block:
    blockId = -1
    data = None

    def __init__(self, blockId):
        self.blockId = blockId

    def read(self):
        return self.data

    def write(self, data):
        if len(str(data)) <= 100:
            self.data = data
            return True
        else:
            print("Writing excess data to block {}".format(self.blockId))
            return False


m = 1000 # 0 to m-1 blocks are available in physical disk
PhysicalDisk = [Block(i) for i in range(m)]
UnusedBlocks = [(m, (0, m-1))]


def reduce():
    while True:
        found = False
        t = len(UnusedBlocks)
        for i in range(t):
            li, (si, ei) = UnusedBlocks[i]
            for j in range(t):
                if i == j:
                    continue
                lj, (sj, ej) = UnusedBlocks[j]
                if ei+1 == sj:
                    found = True
                    if i<j:
                        UnusedBlocks.pop(i)
                        UnusedBlocks.pop(j-1)
                    else:
                        UnusedBlocks.pop(j)
                        UnusedBlocks.pop(i-1)
                    UnusedBlocks.append((li+lj, (si, ej)))
                    break
            if found:
                break
        if not found:
            break

    UnusedBlocks.sort(reverse=True)


def allocateBlocks(numblocks):
    blocks = [None]
    requiredblocks = numblocks
    n = len(UnusedBlocks)
    deletefromunused = []
    allocated = []
    for i in range(n):
        l, (s, e) = UnusedBlocks[i]
        # assert e - s + 1 == l

        if l == requiredblocks:
            for j in range(s, e+1):
                blocks.append(j)
            allocated.append((l, (s, e)))
            deletefromunused.append(i)
            break
        elif l > requiredblocks:
            for j in range(s, s+requiredblocks):
                blocks.append(j)
            allocated.append((requiredblocks, (s, s+requiredblocks-1)))
            deletefromunused.append(i)
            UnusedBlocks.append((l-requiredblocks, (s+requiredblocks, e)))
            break
        elif l < requiredblocks:
            for j in range(s, e+1):
                blocks.append(j)
            allocated.append((l, (s, e)))
            requiredblocks -= l
            deletefromunused.append(i)

    deletefromunused.sort()
    d = len(deletefromunused)
    for i in range(d):
        UnusedBlocks.pop(deletefromunused[i])
        for j in range(i+1,d):
            deletefromunused[j] -= 1

    UnusedBlocks.sort(reverse=True)
    return blocks, allocated

def allocateforErrorBlock():
    n = len(UnusedBlocks)
    l, (s, e) = UnusedBlocks[n-1]
    if l == 1:
        UnusedBlocks.pop(n-1)
        return e
    elif 1 < l:
        UnusedBlocks[n - 1] = (l-1,(s,e-1))
        return e
    else:
        print("Interval of length 0 in UnusedBlocks")


class Disk:
    diskId = -1
    numBlocks = 0
    blocks1 = []
    blocks2 = []
    allocated1 = []
    allocated2 = []

    def __init__(self, diskid, numblocks):
        self.diskId = diskid
        self.numBlocks = numblocks
        self.blocks1, self.allocated1 = allocateBlocks(numblocks)
        self.blocks2, self.allocated2 = allocateBlocks(numblocks)

    def readblock(self, blockid):
        if 0 < blockid <= self.numBlocks:
            r = randint(1, 100)
            # print(r)
            physicalblockid1 = self.blocks1[blockid]
            if r > 10:
                return PhysicalDisk[physicalblockid1].read()
            else:
                print("Error in physical block {}".format(physicalblockid1))

                for i in range(len(self.allocated1)):
                    l, (s, e) = self.allocated1[i]
                    if s <= physicalblockid1 <= e:
                        if l == 1:
                            break
                        else:
                            if s < physicalblockid1:
                                self.allocated1.append((physicalblockid1-s,(s,physicalblockid1-1)))
                            if physicalblockid1 < e:
                                self.allocated1.append((e-physicalblockid1,(physicalblockid1+1,e)))
                            self.allocated1.pop(i)
                            break

                newphysicalblock = allocateforErrorBlock()
                self.allocated1.append((1,(newphysicalblock,newphysicalblock)))

                physicalblockid2 = self.blocks2[blockid]
                data = PhysicalDisk[physicalblockid2].read()
                self.blocks1[blockid] = newphysicalblock
                PhysicalDisk[newphysicalblock].write(data)
                return data
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))

    def writeblock(self, blockid, data):
        if 0 < blockid <= self.numBlocks:
            physicalblockid1 = self.blocks1[blockid]
            physicalblockid2 = self.blocks2[blockid]
            return PhysicalDisk[physicalblockid1].write(data) and PhysicalDisk[physicalblockid2].write(data)
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))
            return False


disks = {}


def createDisk(diskid, numblocks):
    if diskid in disks:
        print("Disk with diskId={} already exists".format(diskid))
        return False
    else:
        disks[diskid] = Disk(diskid, numblocks)
        return True


def readDisk(diskid, blockid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        return disks[diskid].readblock(blockid)


def writeDisk(diskid, blockid, data):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        return disks[diskid].writeblock(blockid, data)


def deleteDisk(diskId):
    if diskId not in disks:
        print("Disk with diskId={} does not exist".format(diskId))
        return False
    else:
        global UnusedBlocks
        UnusedBlocks += disks[diskId].allocated1
        UnusedBlocks += disks[diskId].allocated2
        reduce()
        del disks[diskId].diskId
        del disks[diskId].blocks1
        del disks[diskId].blocks2
        del disks[diskId].allocated1
        del disks[diskId].allocated2
        del disks[diskId]
        return True


createDisk(1,100)
print(UnusedBlocks)
readDisk(1,5)
print(UnusedBlocks)
deleteDisk(1)
print(UnusedBlocks)
