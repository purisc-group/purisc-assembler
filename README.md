purisc-assembler
================

Python assembler for resolving subleq assembly into addresses

Usage
----

python assembler.py [-i inputfile] [-o outputfile [outputfile2]] [-d dataMemoryOffset] [-p programMemoryOffset] [-f] [-v]

* -i to specify the input file
* -o to specify the output file. Specify two if you want the program and data memory to be in separate files, the program memory coming in the first file
* -d to specify the initial data memory location. The default is 1000
* -p to specify the initial program memory location. The default is 1
* -f to format the output with the three operands on the same line. Omit -f to force each operand to have its own line


Input
-----
Example: 

>PROGRAM_MEM:  
>//Program memory  
>//C styled comments are ok  
>//For literal memory locations use # before the number, anything else is considered a label  
>top:    a0      a0      NEXT  
>        counter a0      NEXT  
>        one     neg      NEXT  
>        counter counter #12  //adfadsfasdf  
>15:     a0      counter NEXT  /*324234234  
>dfasdfasdfasdfasd*/  
>12:     a0      a0      top  
>  
>  
>  
>  
>DATA_MEM:  
>/* Some initial values for data memory - the assembler will convert these to 
>   numerical addresses. You can specify a numerical label to tell the assembler
>   to use that specific address for your value.*/  
>zero:   #0  
>one:    #1  
>two:    #2  
>four:   #4  
>eight:  #8  
>sixteen: #16  
>a0:     #0  
>a1:     #0  
>a2:     #0  
>a3:     #0  
>counter:#0  
>output: #0  
>neg: #-1  
