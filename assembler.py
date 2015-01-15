import random
import re
import sys, getopt
import struct

#Usage:
#       python assembler.py [-i inputfile] [-o outputfile] [-d dataMemoryOffset] [-p programMemoryOffset] [-f] [-v] [-r]

#if -r flag is not set, it will output as a binary file. There is a 8 byte header. The first 4 bytes corresponding to a 32 bit integer representing the number of lines (groups of 3 operands) in the program memory (comes first) and the last 4 bytes corresponding to the number of data memory values.

def main(argv):

    dataMemOffset = 1000;
    programMemOffset = 0;
    outputFileNames = ["program_memory.mem", "data_memory.mem"];
    inputFileName = "input.slq";
    formatMachineCode = False;
    verbose = False;
    formatAsBinary = True;

#Command line arguments
    try:
        opts, args = getopt.getopt(argv, "i:o:d:p:fvr",["inputFile=", "outputFile="])
    except getopt.GetoptError:
        print "Usage: python",sys.argv[0],"[-i inputfile] [-o outputfile] [-d dataMemoryOffset] [-p programMemoryOffset] [-f] [-v] [-r];
        sys.exit(2);

    for opt, arg in opts:
        if opt in ("-i", "--infile"):
            inputFileName = arg;

        elif opt in ("-o", "--outfile"):
            outputFileNames = re.split(ur"[\s]+",arg);

        elif opt in ("-d", "--dataOffset"):
            dataMemOffset = int(arg);

        elif opt in ("-p", "--programOffset"):
            programMemOffset = arg;
                
        elif opt == "-f":
            formatMachineCode = True;
                
        elif opt == "-v":
            verbose = True;
        elif opt in ("-r", "--readable"):
            formatAsBinary = False;

    inputFile = open(inputFileName,"r");
    inputText = inputFile.read();
    inputFile.close();


#parse program and data memory
    memoryArray = parseInput(inputText);
    programMemString = memoryArray[0];
    dataMemString = memoryArray[1];

#create initial program memory
    programMem = re.findall("\S+:\s*#?\S+|#?\S+|NEXT", programMemString); 

    if len(programMem) > dataMemOffset:
        print "Warning:\n Initial data memory location collides with program memory, setting initial data memory to: " + len(programMem)
        dataMemOffset = len(programMem);

#create initial data memory        
    nextDataMem = dataMemOffset;
    rawDataStrings = re.findall("\S+:\s*#[-1]?\d*", dataMemString);
    dataMem = {};

    for raw in rawDataStrings:
        variableName = re.findall("\S*(?=:)", raw)[0];
        value = re.findall("(?<=#)[-1]?\d*", raw)[0];
        dataMem[variableName] = [nextDataMem, value];
        nextDataMem += 1;


#resolve labels in program memory
    for i,val in enumerate(programMem):

        if re.match("\S+:", val):
            label = re.findall("\S+(?=:)", val)[0];
            programMem[i] = re.findall("(?<=:)\s*\S+", val)[0];
            programMem[i] = re.sub("\s*","",programMem[i]);

            for j,value in enumerate(programMem):
                if value == label:
                    programMem[j] = "#" + str(i + programMemOffset);

    
#resolve NEXT keyword
    for i,val in enumerate(programMem):
            
        if val == "NEXT":
            programMem[i] = "#" + str(i+1);            
  
#resolve variables into addresses
    for i,val in enumerate(programMem):

        if val in dataMem:
            programMem[i] = str(dataMem[val][0]);

        elif re.match("#",val):
            programMem[i] = val[1:];

        else:
            dataMem[val] = [nextDataMem, "0"]; #initialize data to 0
            programMem[i] = str(nextDataMem);                        
            nextDataMem += 1;
  

#output results
    outputFile = open(outputFileNames[0], "w");
    
    #add header to the binary file if necessary
    if formatAsBinary:
        outputFile.write(struct.pack('<i',len(programMem)/3)
        if len(outputFileNames == 2):
            outputFile.write(struct.pack('<i',0)
        else:
            outputFile.write(struct.pack('<i',len(dataMem))
    outputString = "";

    for index, val in enumerate(programMem):
        outputFile.write(formatValue(val,formatAsBinary));
        outputString += str(val);
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

    #switch to second output file if its name was given
    if(len(outputFileNames) == 2):
        outputFile.close();
        outputFile = open(outputFileNames[1], "w");
        #add header to the binary file if necessary
        if formatAsBinary:
            outputFile.write(struct.pack("<i",0)
            outputFile.write(struct.pack("<i",len(dataMem))
            
    #if there is only one memory file, offset the data memory with zero pad
    if (len(outputFileNames) == 1):
        for i in range(len(programMem), dataMemOffset):
            outputFile.write(formatValue("0",formatAsBinary))
            outputFile.write(formatValue("\n",formatAsBinary));
            outputString += "0\n";
    
    
    #sort the data memory by address so the cpu can use it
    sortedDataMem = [[]]*len(dataMem);
    for key in dataMem:
        address = dataMem[key][0];
        value = dataMem[key][1];
        sortedDataMem[address-dataMemOffset] = [address, value];
    
    for address in range(sortedDataMem[0][0], sortedDataMem[len(sortedDataMem)-1][0]+1):
        value = sortedDataMem[address-dataMemOffset][1];
        if(len(outputFileNames) == 1):
            outputFile.write(formatValue(value,formatAsBinary));
            outputString += str(value);
        # in the two file case, the program needs to know data addresses
        elif(len(outputFileNames) == 2):
            outputFile.write(formatValue(address,formatAsBinary))
            outputFile.write(formatValue(" ",formatAsBinary))
            outputFile.write(formatValue(value,formatAsBinary));
            outputString += str(address) + " " + str(value);
        outputFile.write(formatValue("\n",formatAsBinary));
        outputString += "\n";
    
    outputFile.close();
    
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

    #Order of program memory and data memory doesn't matter
    programMem = re.findall("(?<=PROGRAM_MEM:).*(?=DATA_MEM:)", inputText, re.DOTALL);
    if len(programMem) == 0:
            programMem = re.findall("(?<=PROGRAM_MEM:).*", inputText, re.DOTALL);
    programMem = programMem[0];

    dataMem = re.findall("(?<=DATA_MEM:).*(?=PROGRAM_MEM:)", inputText, re.DOTALL);
    if len(dataMem) == 0:
            dataMem = re.findall("(?<=DATA_MEM:).*", inputText, re.DOTALL);
    dataMem = dataMem[0];


    programMem = filterComments(programMem);
    dataMem = filterComments(dataMem);

    return [programMem, dataMem];



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
            return struct.pack('<i',int(value))
    else:
        return value

if __name__ == '__main__':
    main(sys.argv[1:])
