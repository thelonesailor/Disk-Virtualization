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


m = 1000  # 0 to m-1 blocks are available in physical disk
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
                if sj <= si and ei <= ej:
                    found = True
                    UnusedBlocks.pop(i)
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
        for j in range(i+1, d):
            deletefromunused[j] -= 1

    UnusedBlocks.sort(reverse=True)
    return blocks, allocated


def printblocks(lst, diskid):
    s = "Blocks used by disk {} :[".format(diskid)
    for i in range(len(lst)-1):
        s += str(lst[i][1:])+","
    s += str(lst[len(lst)-1][1:])+"]"
    print(s)


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
        blocks, allocated = allocateblocks(numblocks)
        self.blocks.append(blocks)
        self.allocated.append(allocated)
        self.changed = [False]*(numblocks+1)
        # print(self.blocks)

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
            blocks, allocated = allocateblocks(self.numBlocks)
            self.c += 1
            self.blocks.append(blocks)
            self.allocated.append(allocated)

            for i in range(1, self.numBlocks+1):
                if self.changed[i]:
                    data = PhysicalDisk[self.blocks[0][i]].read()
                    PhysicalDisk[self.blocks[1][i]].write(data)

            self.changed = [False]*(self.numBlocks+1)
            return 0
        else:
            changes = 0
            newblocks = [None]*(self.numBlocks+1)
            newallocated = []
            for i in range(1, self.numBlocks+1):
                if not self.changed[i]:
                    newblocks[i] = self.blocks[self.c-1][i]
                    self.blocks[self.c-1][i] = self.blocks[self.c-2][i]
                    newallocated.append((1, (newblocks[i], newblocks[i])))
                else:
                    changes += 1

            k = 1
            blocks, allocated = allocateblocks(changes)
            for i in range(1, self.numBlocks+1):
                if self.changed[i]:
                    newblocks[i] = blocks[k]
                    data = PhysicalDisk[self.blocks[self.c-1][i]].read()
                    PhysicalDisk[newblocks[i]].write(data)
                    k += 1

            allocated += newallocated
            self.blocks.append(newblocks)
            self.allocated.append(allocated)
            self.c += 1
            self.changed = [False]*(self.numBlocks+1)
            return self.c-2

    def rollback(self, checkpointid):
        if checkpointid >= self.c-1:
            print("Invalid checkpointid")
            return False

        global UnusedBlocks
        for i in range(self.c-1, checkpointid+1, -1):
            UnusedBlocks += self.allocated[i]
            self.blocks.pop(i)
            self.allocated.pop(i)
        self.c = checkpointid + 2
        reduce()

        needtoallocate = 0
        for i in range(1, self.numBlocks + 1):
            # print("{},{}".format(self.c,checkpointid))
            if self.blocks[self.c-2][i] == self.blocks[self.c-1][i]:
                needtoallocate += 1

        self.changed = [False]*(self.numBlocks+1)
        if needtoallocate > 0:
            blocks, allocated = allocateblocks(needtoallocate)
            self.allocated[self.c-1] += allocated

        k = 1
        for i in range(1, self.numBlocks + 1):
            if self.blocks[self.c-2][i] == self.blocks[self.c-1][i]:
                self.blocks[self.c-1][i] = blocks[k]
                k += 1

        for i in range(1, self.numBlocks + 1):
            data = PhysicalDisk[self.blocks[self.c-2][i]].read()
            PhysicalDisk[self.blocks[self.c-1][i]].write(data)
        return True


disks = {}


def createdisk(diskid, numblocks):
    if diskid in disks:
        print("Disk with diskId={} already exists".format(diskid))
        return False
    else:
        disks[diskid] = Disk(diskid, numblocks)
        print("created disk {}".format(diskid))
        return True


def checkpointdisk(diskid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        checkpointid = disks[diskid].newcheckpoint()
        print("created checkpoint {} for disk {}: {}".format(checkpointid, diskid, returndiskdata(diskid)))
        printblocks(disks[diskid].blocks, diskid)
        print("Unused blocks :{}".format(UnusedBlocks))
        print("-----------------------------------")
        return checkpointid


def rollbackdisk(diskid, checkpointid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        success = disks[diskid].rollback(checkpointid)
        if success:
            print("Rolled back disk {} to checkpoint {}: {}".format(diskid, checkpointid, returndiskdata(diskid)))
            printblocks(disks[diskid].blocks, diskid)
            print("Unused blocks :{}".format(UnusedBlocks))
            print("-----------------------------------")
        return success


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
        for i in range(disks[diskid].c):
            UnusedBlocks += disks[diskid].allocated[i]
        reduce()
        del disks[diskid].diskId
        for i in range(disks[diskid].c):
            del disks[diskid].blocks[i]
            del disks[diskid].allocated[i]
        del disks[diskid].c
        del disks[diskid]
        print("deleted disk {}".format(diskid))
        return True


def returndiskdata(diskid):
    if diskid not in disks:
        print("Disk with diskId={} does not exist".format(diskid))
        return False
    else:
        nb = disks[diskid].numBlocks
        data = ""
        for i in range(1, nb):
            data += str(readdisk(1, i)) + ","
        data += str(readdisk(1, nb))
        return data


createdisk(1, 5)
for i in range(1, 6):
    writedisk(1, i, i+2)
a = checkpointdisk(1)
writedisk(1, 2, 8)
b = checkpointdisk(1)
writedisk(1, 1, 9)
c = checkpointdisk(1)
writedisk(1, 3, 10)
d = checkpointdisk(1)

rollbackdisk(1, d)
rollbackdisk(1, c)

writedisk(1, 4, 11)
e = checkpointdisk(1)

rollbackdisk(1, e)
rollbackdisk(1, c)
rollbackdisk(1, b)
rollbackdisk(1, a)
