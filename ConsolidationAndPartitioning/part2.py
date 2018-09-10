from random import randint, choice
import string

lenA = 600
lenB = 400
A = [None]*lenA
B = [None]*lenB


class Block:
    blockId = -1

    def __init__(self, blockid):
        self.blockId = blockid

    def read(self):
        if 0 <= self.blockId < lenA:
            return A[self.blockId]
        elif lenA <= self.blockId < lenA + lenB:
            return B[self.blockId-lenA]

    def write(self, data):
        if len(str(data)) <= 100:
            if 0 <= self.blockId < lenA:
                A[self.blockId] = data
            elif lenA <= self.blockId < lenA + lenB:
                B[self.blockId - lenA] = data
            return True
        else:
            print("Writing excess data to block {}".format(self.blockId))
            return False


m = lenA + lenB  # 0 to m-1 blocks are available in physical disk
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
                    if i < j:
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


def allocateblocks(numblocks):
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
            requiredblocks = 0
            break
        elif l > requiredblocks:
            for j in range(s, s+requiredblocks):
                blocks.append(j)
            allocated.append((requiredblocks, (s, s+requiredblocks-1)))
            deletefromunused.append(i)
            UnusedBlocks.append((l-requiredblocks, (s+requiredblocks, e)))
            requiredblocks = 0
            break
        elif l < requiredblocks:
            for j in range(s, e+1):
                blocks.append(j)
            allocated.append((l, (s, e)))
            requiredblocks -= l
            deletefromunused.append(i)

    if requiredblocks > 0:
        print("Not enough space to allocate {} blocks".format(numblocks))
        print("Instead allocating {} blocks".format(numblocks-requiredblocks))

    deletefromunused.sort()
    d = len(deletefromunused)
    for i in range(d):
        UnusedBlocks.pop(deletefromunused[i])
        for j in range(i+1, d):
            deletefromunused[j] -= 1

    UnusedBlocks.sort(reverse=True)
    return blocks, allocated


class Disk:
    diskId = -1
    numBlocks = 0
    blocks = []
    allocated = []

    def __init__(self, diskid, numblocks):
        self.diskId = diskid
        self.numBlocks = numblocks
        self.blocks, self.allocated = allocateblocks(numblocks)

    def printallocation(self):
        print("Disk {}: {}".format(self.diskId, self.allocated))

    def readblock(self, blockid):
        if 0 < blockid <= self.numBlocks:
            physicalblockid = self.blocks[blockid]
            return PhysicalDisk[physicalblockid].read()
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))

    def writeblock(self, blockid, data):
        if 0 < blockid <= self.numBlocks:
            physicalblockid = self.blocks[blockid]
            return PhysicalDisk[physicalblockid].write(data)
        else:
            print("Block {} does not exist on disk {}".format(blockid, self.diskId))
            return False


disks = {}


def printmemory():
    print("-------------------")
    for _, disk in disks.items():
        disk.printallocation()
    print("Unused: {}".format(UnusedBlocks))
    print("-------------------")


def createdisk(diskid, numblocks):
    if diskid in disks:
        print("Disk with diskId={} already exists".format(diskid))
        return False
    else:
        disks[diskid] = Disk(diskid, numblocks)
        print("Created disk {}".format(diskid))
        return True


def readdisk(diskid, blockid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        return disks[diskid].readblock(blockid)


def writedisk(diskid, blockid, data):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        return disks[diskid].writeblock(blockid, data)


def deletedisk(diskid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        global UnusedBlocks
        UnusedBlocks += disks[diskid].allocated
        reduce()
        del disks[diskid].diskId
        del disks[diskid].blocks
        del disks[diskid].allocated
        del disks[diskid]
        print("Deleted disk {}".format(diskid))
        return True


def deletealldisks():
    global disks, UnusedBlocks
    disks = {}
    UnusedBlocks = [(m, (0, m-1))]


def availableblocks():
    availabl = 0
    for a, (_, _) in UnusedBlocks:
        availabl += a
    return availabl


createdisk(1, 300)
printmemory()
createdisk(2, 200)
printmemory()
createdisk(3, 400)
printmemory()
deletedisk(2)
printmemory()
deletedisk(1)
printmemory()
createdisk(1, 200)
printmemory()

diskId = 1
disklength = 200
errors = 0
for i in range(2*disklength):
    blockId = randint(1, disklength)
    length = randint(1, 100)
    # print("{}, {}, {}".format(i, blockId, length))
    dataWritten = ''.join(choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
                          for _ in range(length))
    success = writedisk(diskId, blockId, dataWritten)
    if success:
        dataRead = readdisk(diskId, blockId)
        # print("{}\n{}\n".format(dataWritten, dataRead))
        assert dataRead == dataWritten
    else:
        errors += 1
        print("Writing to block {} failed data={}".format(blockId, dataWritten))

print("Number of writing errors={}".format(errors))


deletealldisks()
print("Doing random disk creates and deletes")
curr = 1
for i in range(50):
    w = 0
    available = availableblocks()
    if available < 50:
        w = 1
    else:
        w = 2
    if w == 1:
        # print(list(disks.keys()))
        diskid = choice(list(disks.keys()))
        deletedisk(diskid)
    else:
        diskid = curr
        curr += 1
        createdisk(curr, randint(50, available))
    printmemory()
