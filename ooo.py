import queue
from collections import deque
# pylint: disable=trailing-whitespace
# pylint: disable=global-variable-not-assigned
# pylint: disable=invalid-name
# pylint: disable=consider-using-enumerate  
# pylint: disable=missing-function-docstring
# pylint: disable=superfluous-parens
# pylint: disable=line-too-long

#opening the file and putting all the instructions in an array
with open('ex1.txt') as f:
    content=[line.split(",") for line in f]
    instrmatrix = content[1:]
    line1 = content[0]
    
PREGCOUNT = int(line1[0])
WIDTH = int(line1[1])

instrsDict = {i//WIDTH: instrmatrix[i:i+WIDTH] for i in range(0, len(instrmatrix), WIDTH)}
cycles = []
for i in range(0, (len(instrmatrix)+1)):
    cycles.append(i)
decodeQ = queue.Queue()
renameQ = queue.Queue()
dispatchQ = queue.Queue()
issueQ = queue.Queue()
ROB = queue.Queue()
wbQ = queue.Queue()
commitQ = queue.Queue()

mapTable = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10, 11:11, 12:12, 13:13, 14:14, 15:15, 16:16, 17:17, 18:18, 19:19, 20:20, 21:21, 22:22, 23:23, 24:24, 25:25, 26:26, 27:27, 28:28, 29:29, 30:30, 31:31}
freeList = deque()
issueDict= {}
for i in range(32, ((PREGCOUNT)+1)):
    freeList.append(i)

readyTable = {key: True for key in freeList}

fetchCounter = 0
cycle = [0,0,0,0,0,0,0]
cycles = []
t = 0

for i in range(len(instrmatrix)):
    cycles.append(cycle)

commitedInsts = 0

def fetch(instrsDict):
    global fetchCounter 
    global decodeQ
    instructions = instrsDict[fetchCounter] #instruction(s) in cycle. e.g.: [[L,2,80,4],[L,3,64,5]]
    decodeQ.put(instructions) #push the instruction into decode q. e.g.: deodeQ = [[[L,2,80,4],[L,3,64,5]]]
    fetchCounter+=1
    

def decode():
    global decodeQ
    global renameQ
    global cycles
    global t


    empty_decode = decodeQ.get() #empties decode q
    renameQ.put(empty_decode) #pushes intruciotn(s) than was in decode q into rename q
    #save correspoding key+1

    cycles[t][1] +=1

def rename():
    global renameQ
    global dispatchQ
    global mapTable
    global freeList
    global readyTable
    global t

    instructions = renameQ.get() #empties rename q

    i = 0
    instr = 0
    while(instr < WIDTH):
        if instructions[i][0] == 'L': # check if L instruction
            #rename src reg
            instructions[i][3] = mapTable[int(instructions[i][3])] # renames arch reg to phys reg from mapTable

            #rename dest reg
            instructions[i][1] = freeList[0] # renames arch reg to phys reg from freeList
            mapTable[int(instructions[i][1])] = freeList[0]  #updates mapTable dict
            freeList.popleft() #removes that phys reg from the freeList
            
           
        elif instructions[i][0] == 'R': # check if R instruction
            #rename src2 reg
            instructions[i][3] = freeList[int(instructions[i][3])] 

            #rename src1 reg
            instructions[i][2] = mapTable[int(instructions[i][2])] 

            #rename dest reg
            instructions[i][1] = freeList[0] # renames arch reg to phys reg from freeList
            mapTable[int(instructions[i][1])] = freeList[0]  #updates mapTable dict
            freeList.popleft() #removes that phys reg from the freeList
            
        
        elif instructions[i][0] == 'I': # check if I instruction
            #rename src reg
            instructions[i][2] = mapTable[int(instructions[i][2])] 

            #rename dest reg
            instructions[i][1] = freeList[0] # renames arch reg to phys reg from freeList
            mapTable[int(instructions[i][1])] = freeList[0]  #updates mapTable dict
            freeList.popleft() #removes that phys reg from the freeList
            

        elif instructions[i][0] == 'S': # check if S instruction
            #rename src reg
            instructions[i][1] = mapTable[int(instructions[i][1])] # renames arch reg to phys reg from freeList

            #rename src reg
            instructions[i][3] = freeList[int(instructions[i][3])] 
            
        i+=1
        instr+=1

    dispatchQ.put(instructions) #pushes renamed intruciotn(s) into dispatch q
    cycles[t][2] +=1


def dispatch():
    global dispatchQ
    global issueQ
    global renameQ 
    global readyTable
    global ROB
    global dc

    instructions = dispatchQ.get() 
    for j in range(WIDTH):
        if instructions[j][0] == "L":
            readyTable[instructions[j][1]] = False
        elif instructions[j][0] == "R":
            readyTable[instructions[j][1]] = False
        elif instructions[j][0] == "I":
            readyTable[instructions[j][1]] = False
    issueQ.put(instructions) 

    cycles[t][3] +=1

def issue():
    global issueQ
    global wbQ
    global dispatchQ
    global readyTable
    global ic
    #check if src1 and src2 == True, then push into wbQ,then update dest reg in readyTable to True
    instructions = issueQ.get()
    for j in range(len(instructions)):
        if instructions[j][0] == "L" and readyTable[int(instructions[j][3])] == False:
            readyTable[int(instructions[j][3])] == True

        elif instructions[j][0] == "R" and (readyTable[int(instructions[j][2])] == False or readyTable[int(instructions[j][3])] == False):
            readyTable[int(instructions[j][2])] = True 
            readyTable[int(instructions[j][3])] == True 
               
        elif instructions[j][0] == "I" and readyTable[int(instructions[j][1])] == False:
            readyTable[int(instructions[j][1])] == True

        elif instructions[j][0] == "S" and (readyTable[int(instructions[j][1])] == False or readyTable[int(instructions[j][3])] == False):
            readyTable[int(instructions[j][1])] = True 
            readyTable[int(instructions[j][3])] = True

    wbQ.put(instructions)
    cycles[t][4] +=1


def WB():
    global issueQ
    global wbQ
    global dispatchQ
    global readyTable
    global ROB
    global cycles

    instructions = wbQ.get()

    for j in range(WIDTH):
        if instructions[j][0] == "L" and readyTable[int(instructions[j][3])] == True:
            readyTable.append(int(instructions[j][1])) 
            commitQ.put(instructions)

        elif instructions[j][0] == "R" and (readyTable[int(instructions[j][2])] == True and readyTable[int(instructions[j][3])] == True):
            readyTable.append(int(instructions[j][3]))
            readyTable.append(int(instructions[j][2])) 
            commitQ.put(instructions)
               
        elif instructions[j][0] == "I" and readyTable[int(instructions[j][1])] == True:
            readyTable.append(instructions[j][1])
            commitQ.put(instructions)
    
    ROB.put(instructions)
    cycles[t][5] +=1



def commit():
    global wbQ
    global commitQ
    global ROB
    global cycles

    instructions = commitQ.get()

    for j in range(WIDTH):
        if instructions[j][0] == "L" and readyTable[int(instructions[j][3])] == False:
            freeList.append(int(instructions[j][1]))

        elif instructions[j][0] == "R" and (readyTable[int(instructions[j][2])] == False or readyTable[int(instructions[j][3])] == False):
            freeList.append(int(instructions[j][3]))
            freeList.append(int(instructions[j][2])) 
               
        elif instructions[j][0] == "I" and readyTable[int(instructions[j][1])] == False:
            freeList.append(int(instructions[j][1]))
        cycles[t][5] +=1
t+=1


#commit()
# Open a new file in write mode
with open('out.txt', 'w') as f:
    # Write a line to the file
    f.write(str(cycles))




    


