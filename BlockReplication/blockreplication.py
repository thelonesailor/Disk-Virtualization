from random import randint, choice
import string

class Block:
    blockId = -1
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


m = 1000  # 0 to m-1 blocks are available in physical disk
PhysicalDisk = [Block(i) for i in range(m)]
UnusedBlocks = [(m, (0, m-1))]
errorBlocks = []

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


def allocateforerrorblock():
    n = len(UnusedBlocks)
    l, (s, e) = UnusedBlocks[n-1]
    if l == 1:
        UnusedBlocks.pop(n-1)
        return e
    elif 1 < l:
        UnusedBlocks[n - 1] = (l-1, (s, e-1))
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
        self.blocks1, self.allocated1 = allocateblocks(numblocks)
        self.blocks2, self.allocated2 = allocateblocks(numblocks)

    def printallocation(self):
        print("Disk {}: {}".format(self.diskId, self.allocated1))
        if len(str(self.diskId)) == 1:
            print("        {}".format(self.allocated2))
        elif len(str(self.diskId)) == 2:
            print("         {}".format(self.allocated2))
        else:
            print("          {}".format(self.allocated2))

    def readblock(self, blockid):
        if 0 < blockid <= self.numBlocks:
            r = randint(1, 100)
            # print(r)
            physicalblockid1 = self.blocks1[blockid]
            if r > 10:
                return PhysicalDisk[physicalblockid1].read()
            else:
                print("Error in physical block {}".format(physicalblockid1))
                errorBlocks.append(physicalblockid1)

                for i in range(len(self.allocated1)):
                    l, (s, e) = self.allocated1[i]
                    if s <= physicalblockid1 <= e:
                        if l == 1:
                            break
                        else:
                            if s < physicalblockid1:
                                self.allocated1.append((physicalblockid1-s, (s, physicalblockid1-1)))
                            if physicalblockid1 < e:
                                self.allocated1.append((e-physicalblockid1, (physicalblockid1+1, e)))
                            self.allocated1.pop(i)
                            break

                newphysicalblock = allocateforerrorblock()
                self.allocated1.append((1, (newphysicalblock, newphysicalblock)))

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


def printmemory():
    print("-------------------")
    for _, disk in disks.items():
        disk.printallocation()
    print("Unused: {}".format(UnusedBlocks))
    print("Errors: {}".format(errorBlocks))
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
        UnusedBlocks += disks[diskid].allocated1
        UnusedBlocks += disks[diskid].allocated2
        reduce()
        del disks[diskid].diskId
        del disks[diskid].blocks1
        del disks[diskid].blocks2
        del disks[diskid].allocated1
        del disks[diskid].allocated2
        del disks[diskid]
        print("Deleted disk {}".format(diskid))
        return True


def deletealldisks():
    global disks, UnusedBlocks, errorBlocks
    disks = {}
    UnusedBlocks = [(m, (0, m-1))]
    errorBlocks = []


def availableblocks():
    availabl = 0
    for a, (_, _) in UnusedBlocks:
        availabl += a
    return availabl


createdisk(1, 200)
printmemory()
createdisk(2, 100)
printmemory()
createdisk(3, 200)
printmemory()
deletedisk(2)
printmemory()
deletedisk(1)
printmemory()
deletedisk(3)
printmemory()
createdisk(1, 200)
printmemory()

print("Doing random disk reads and writes-----------------------")
diskId = 1
disklength = 200
errors = 0
for i in range(disklength//4):
    blockId = randint(1, disklength)
    length = randint(1, 100)
    # print("{}, {}, {}".format(i, blockId, length))
    dataWritten = ''.join(choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))
    success = writedisk(diskId, blockId, dataWritten)
    if success:
        dataRead = readdisk(diskId, blockId)
        # print("{}\n{}\n".format(dataWritten, dataRead))
        assert dataRead == dataWritten
    else:
        errors += 1
        print("Writing to block {} failed data={}".format(blockId, dataWritten))

print("Number of writing errors={}".format(errors))
print(errorBlocks)
printmemory()
deletedisk(1)
printmemory()


print("Doing random disk creates and deletes-----------------------")
curr = 1
for i in range(50):
    w = 0
    available = availableblocks()
    # print(available)
    if available//2 < 50:
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
        createdisk(curr, randint(50, available//2))
    printmemory()
