class Block:
    blockId = -1
    data = "uninitialised"

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


class Disk:
    diskId = -1
    numBlocks = 0
    c = 0
    blocks = []
    allocated = []
    changed = []

    def __init__(self, diskid, numblocks):
        self.diskId = diskid
        self.numBlocks = numblocks
        self.c = 1
        blocks, allocated = allocateBlocks(numblocks)
        self.blocks.append(blocks)
        self.allocated.append(allocated)
        self.changed = [False]*(numblocks+1)
        print(self.blocks)

    def readblock(self, blockid):
        if 0 < blockid <= self.numBlocks:
            physicalblockid = self.blocks[self.c-1][blockid]
            return PhysicalDisk[physicalblockid].read()
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))

    def writeblock(self, blockid, data):
        if 0 < blockid <= self.numBlocks:
            # print(data)
            physicalblockid = self.blocks[self.c-1][blockid]
            success = PhysicalDisk[physicalblockid].write(data)
            if success:
                self.changed[blockid] = True
            return success
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))
            return False

    def newcheckpoint(self):
        if self.c == 1:
            blocks, allocated = allocateBlocks(self.numBlocks)
            self.c += 1
            self.blocks.append(blocks)
            self.allocated.append(allocated)

            for i in range(1,self.numBlocks+1):
                if self.changed[i]:
                    data = PhysicalDisk[self.blocks[0][i]].read()
                    PhysicalDisk[self.blocks[1][i]].write(data)

            self.changed = [False]*(self.numBlocks+1)
            print(self.blocks)
            return 0
        else:
            changes = 0
            newblocks = [None]*(self.numBlocks+1)
            for i in range(1, self.numBlocks+1):
                if not self.changed[i]:
                    newblocks[i] = self.blocks[self.c-1][i]
                    self.blocks[self.c-1][i] = self.blocks[self.c-2][i]
                else:
                    changes += 1

            # print(changes)
            k = 1
            blocks, allocated = allocateBlocks(changes)
            for i in range(1, self.numBlocks+1):
                if self.changed[i]:
                    newblocks[i] = blocks[k]
                    data = PhysicalDisk[self.blocks[self.c-1][i]].read()
                    PhysicalDisk[newblocks[i]].write(data)
                    k += 1

            self.blocks.append(newblocks)
            self.allocated.append(allocated)
            self.c += 1
            print(self.blocks)
            return self.c-2

    def rollback(self, checkpointid):
        if checkpointid >= self.c:
            print("Invalid checkpointid")
            return False

        global UnusedBlocks
        for i in range(self.c-1, checkpointid, -1):
            UnusedBlocks += self.allocated[i]
            self.blocks.pop(i)
            self.allocated.pop(i)
        self.c = checkpointid + 1
        self.changed = [False]*(self.numBlocks+1)
        reduce()
        return True


disks = {}


def createDisk(diskid, numblocks):
    if diskid in disks:
        print("Disk with diskId={} already exists".format(diskid))
        return False
    else:
        disks[diskid] = Disk(diskid, numblocks)
        print("created disk {}".format(diskid))
        return True


def checkpointDisk(diskid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        checkpointid = disks[diskid].newcheckpoint()
        print("created checkpoint {} for disk {}".format(checkpointid, diskid))
        return checkpointid


def rollbackDisk(diskid, checkpointid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        success = disks[diskid].rollback(checkpointid)
        if success:
            print("Rolled back disk {} to checkpoint {}".format(diskid,checkpointid))
        return success


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
        for i in range(disks[diskId].c):
            UnusedBlocks += disks[diskId].allocated[i]
        reduce()
        del disks[diskId].diskId
        for i in range(disks[diskId].c):
            del disks[diskId].blocks[i]
            del disks[diskId].allocated[i]
        del disks[diskId].c
        del disks[diskId]
        return True


createDisk(1, 5)
for i in range(1, 6):
    writeDisk(1, i, i+2)
s = ""
for i in range(1, 6):
    s += str(readDisk(1, i))+","
print(s)

writeDisk(1, 2, 1729)
writeDisk(1, 1, 17)
s = ""
for i in range(1, 6):
    s += str(readDisk(1, i))+","
print(s)

a = checkpointDisk(1)

writeDisk(1, 3, 'lmao')
s = ""
for i in range(1, 6):
    s += str(readDisk(1, i))+","
print(s)
b = checkpointDisk(1)
rollbackDisk(1, a)
s = ""
for i in range(1, 6):
    s += str(readDisk(1, i))+","
print(s)