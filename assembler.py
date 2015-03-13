import random
import re
import sys, getopt
import struct

#Usage:
#       python assembler.py [-i inputfile] [-o outputfile] [-d dataMemoryOffset] [-p programMemoryOffset] [-f] [-v] [-r]

#if -r flag is not set, it will output as a binary file. There is a 8 byte header. The first 4 bytes corresponding to a 32 bit integer representing the number of lines (groups of 3 operands) in the program memory (comes first) and the last 4 bytes corresponding to the number of data memory values.

reservedKeywords = {"OFLAG": 1337,"OREG":1338}

def main(argv):

    dataOffset = 3000;
    bootloaderLength = 32;
    localmemory = 8192; #8k
    outputFileName = "";
    inputFileName = "input.slq";
    formatMachineCode = False;
    verbose = False;
    formatAsBinary = False;
    multiFile = False;

    usage = "Usage: python" + sys.argv[0] + "[-i inputfile] [options]\n\
    -o, --outputfile <outputfile>         specify the output file, defaults to the input file with .subleq as the extension\n\
    -d, --data <dataMemoryOffset>         specify the number of memory locations between program memory and data memory, dafult 3000\n\
    -b, --bootloader <bootloadLength>     the length of the bootloader for each computer group, default 32\n\
    -l, --localmemory <localmemory>       size of total local memory, default 8k\n\
    -r, --binary                          output as binary\n\
    -f                                    format output in groups of 3\n\
    -v                                    print output to the terminal\n\
    -m                                    print the output in multiple files"

#Command line arguments
    try:
        opts, args = getopt.getopt(argv, "i:o:d:b:l:rfvhm")
    except getopt.GetoptError:
        print usage
        sys.exit(2);

    for opt, arg in opts:
        if opt in ("-i", "--infile"):
            inputFileName = arg;

        elif opt in ("-o", "--outfile"):
            outputFileNames = arg;

        elif opt in ("-d", "--data"):
            dataOffset = int(arg,0);

        elif opt in ("-b", "--bootloader"):
            bootloaderLength = int(arg,0);

        elif opt in ("-l", "--localmemory"):
            localmemory = int(arg,0);
        
        elif opt in ("-r", "--binary"):
            formatAsBinary = True;
                
        elif opt == "-f":
            formatMachineCode = True;
                
        elif opt == "-v":
            verbose = True;

        elif opt in ("-h", "--help"):
            print usage
            sys.exit(0);

        elif opt == "-m":
            multiFile = True;

    #if don't specify output file, set it to the inputfile with .machine extension
    if outputFileName == "":
        extIndex = inputFileName.rfind(".");
        if extIndex == -1:
            extIndex = len(inputFileName);
        outputFileName = inputFileName[:extIndex] + ".machine"
        
    inputFile = open(inputFileName,"r");
    inputText = inputFile.read();
    inputFile.close();

#parse program and data memory
    memoryArray = parseInput(inputText);
    programMemsString = memoryArray[0];
    dataMemsString = memoryArray[1];
    numProgs = len(programMemsString);

    memory = range(0,8*1024);
    for i in memory:
        memory[i] = 0;


    for i in range(len(programMemsString)):
        programMemString = programMemsString[i];
        dataMemString = dataMemsString[i];

        programMemOffset = localmemory*i / numProgs + bootloaderLength;
        dataMemOffset = programMemOffset + dataOffset;

        #create initial data memory        
        nextDataMem = dataMemOffset;
        rawDataStrings = re.findall("\S+:\s*\S+", dataMemString);
        dataMem = {};

        for raw in rawDataStrings:
            variableName = re.findall("\S*(?=:)", raw)[0];
            value = re.findall("(?<=#)[-]?\d+|NEXT|&\S+", raw)[0];
            if variableName.strip() in reservedKeywords:
                dataMem[variableName] = [reservedKeywords[variableName],value]
            else:
                #points to the next memory location
                if value == "NEXT":
                    value = nextDataMem + 1;

                #pointers
                if re.match("&",value):
                    var = value[1:];

                    if var not in dataMem:
                        print "error - pointing to a location that does not exist"
                        sys.exit(2);
                    else:
                        value = dataMem[var][0];

                #data
                dataMem[variableName] = [nextDataMem, str(value)];

                nextDataMem += 1;
                while isReservedKeyword(nextDataMem):
                    nextDataMem += 1;

    #create initial program memory
        programMem = re.findall("\S+:\s*#?[^\s,]+|#?[^\s,]+|NEXT", programMemString); 

        if len(programMem) > dataMemOffset:
            print "Warning:\n Initial data memory location collides with program memory, setting initial data memory to: " + len(programMem)
            dataMemOffset = len(programMem);


    #resolve labels in program memory
        for i,val in enumerate(programMem):

            if re.match("\S+:", val):
                #get the label from the operand
                label = re.findall("\S+(?=:)", val)[0]; 
                
                #remove the label and whitespace
                programMem[i] = re.findall("(?<=:)\s*\S+", val)[0];
                programMem[i] = re.sub("\s*","",programMem[i]);

                #iterate through the program memory, replace the label with the appropriate line 
                #address
                for j,value in enumerate(programMem):
                    if value == label:
                        programMem[j] = "#" + str(i + programMemOffset);

    #resolve NEXT keyword
        for i,val in enumerate(programMem):
                
            if val == "NEXT":
                programMem[i] = "#" + str(i+1+programMemOffset);          
      
    #resolve variables into addresses
        for i,val in enumerate(programMem):
            #variable already added in datamemory
            if val in dataMem:
                programMem[i] = str(dataMem[val][0]);

            #offset required
            elif re.match(".*\+",val):
                end = val.find("+");
                if val[:end] in dataMem:
                    base = val[:end];
                    offset = val[end+1:];
                    if re.match("#",offset): #literal
                        programMem[i] = str(dataMem[base][0] + int(offset[1:]));
                    else:
                        programMem[i] = str(dataMem[base][0] + dataMem[offset][0]);


            #"variable" is a literal address
            elif re.match("#",val):
                programMem[i] = val[1:];

            else:
                dataMem[val] = [nextDataMem, "0"]; #initialize data to 0
                programMem[i] = str(nextDataMem);                        
                nextDataMem += 1;

        #put memory into the giant memory list (represents localmemory)
        memory[programMemOffset:programMemOffset+len(programMem)] = programMem;

        #walk through data memory and put it into the memory list
        for i in dataMem:
            location = int(dataMem[i][0]);
            val = dataMem[i][1];
            memory[location] = val;

    
    outputString = "";
    outputFiles = [];

    if not multiFile:
        bootloaderLength = 0;
        outputFiles.append(open(outputFileName,'w'));
        outputFile = outputFiles[0];

    else:
        for i in range(0,numProgs):
            extIndex = inputFileName.rfind(".");
            if extIndex == -1:
                extIndex = len(inputFileName);
            outputFiles.append(open(inputFileName[:extIndex] + str(i) +  ".machine",'w'))


    for i in range(0,numProgs):
        if multiFile:
            outputFile = outputFiles[i];
        for j in range(8*1024*i/numProgs + bootloaderLength,8*1024*(i+1)/numProgs):
            mem = memory[j];
            outputFile.write(formatValue(mem,formatAsBinary));
            outputString += str(mem);
            if (formatMachineCode):
                if (index + 1) % 3 == 0:
                    outputFile.write(formatValue("\n",formatAsBinary));
                    outputString += "\n";
                        
                else:
                    outputFile.write(formatValue(" ",formatAsBinary));
                    outputString += " ";
            else:
                outputFile.write(formatValue("\n",formatAsBinary));
                outputString += "\n";


    for out in outputFiles:
        out.close();

    if verbose: 
        print outputString;


def randomInsult():
    insults = [
        "you cunt",
        "you dick",
        "motherfucker",
        "father fister",
        "you eater of broken meat",
        "twat",
        "it's no wonder your parents don't love you",
        "you worthless piece of shit",
        "you failure",
        "idiot",
        "eat shit and die"]

    return insults[random.randrange(0,9)];

def parseInput(inputText):
#Pass the raw code from the input
#Return an array containing the program memory and data memory strings
#The program memory comes first

    programMems = re.findall("(?<=PROGRAM_MEM_)\d:[\s\S]*?(?=DATA_MEM)|(?<=PROGRAM_MEM_)\d+:[\s\S]*?$",inputText);
    for i,mem in enumerate(programMems):
        mem = filterComments(mem);
        programMems[i] = re.sub("\d+:","",mem);

    dataMems = re.findall("(?<=DATA_MEM_)\d:[\s\S]*?(?=PROGRAM_MEM)|(?<=DATA_MEM_)\d+:[\s\S]*?$",inputText);

    for i,mem in enumerate(dataMems):
        dataMems[i] = re.sub("^\d+:","",mem);
        mem = filterComments(mem);
        

    if len(dataMems) != len(programMems):
        print "error - program memory - data memory imbalance"
        sys.exit(2);

    return [programMems, dataMems];



def filterComments(string):
    multiLinePattern = re.compile("\\/\\*.*\\*\\/", re.DOTALL);
    singleLinePattern = re.compile("\\/\\/.*");

    string = multiLinePattern.sub("", string, re.DOTALL);
    string = singleLinePattern.sub("", string);

    return string;
        
def formatValue(value,formatAsBinary):
    if formatAsBinary:
        if (value == "\n" or value == " "):
            return ""
        else:
            return struct.pack('>i',int(value))
    else:
        return str(value)
        
def isReservedKeyword(address):
    for key,value in reservedKeywords.iteritems():
        if value == address:
            return True
            
    return False

def maxReservedAddress():
    maxAddr = -1;
    for key,value in reservedKeywords.iteritems():
        if value > maxAddr:
            maxAddr = value
    return maxAddr
    
if __name__ == '__main__':
    main(sys.argv[1:])
