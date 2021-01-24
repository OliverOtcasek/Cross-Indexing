import os
import re
import sys
from subprocess import call
import subprocess
from time import perf_counter
import datetime

def check_args():
    #Make sure the number of arguments are correct.
    if(len(sys.argv) != 2):
        raise Exception("Error: 2 arguments expected")



def create_dump_files():
    #create objdump and dwarfdump files.
    f = open('objdump.txt', 'w')
    call(["objdump", "-d", sys.argv[1]], stdout=f)
    f.close()
    f = open('dwarfdump.txt', 'w')
    call(["llvm-dwarfdump", sys.argv[1]], stdout=f)
    f.close()



def alter_dwarfdump():
    #change dwarfdump.txt to the --debug-line version.
    f = open("dwarfdump.txt", "w")
    call(["llvm-dwarfdump", "--debug-line", sys.argv[1]], stdout=f)
    f.close()



def find_source_files():
    #trace the source files from the compilation unit in the dwarfdump file.
    ret = set([])
    f = open("dwarfdump.txt", "r")
    lines = f.readlines()
    compile_unit = False
    for line in range(len(lines)):
        if re.search(r"DW_TAG_compile_unit", lines[line]) is not None:
            line = line + 3
            name = lines[line].split()[1]
            
            address = lines[line+2].split()[1][2:-2] + "/" + name[2:-2]
            ret.add((name, address))

    f.close()
    return ret


def trim_dwarfdump(source_files):
    #Cut out dwarfdump info irrelevant to the source files.
    f = open("dwarfdump.txt", "r+")
    blocks = f.read().split("\n\n")
    output = []
    take = False
    for source_file in source_files:
        for block in blocks:
            if take:
                take = False
                output.append(block)
            
            if re.search(source_file[0], block) is not None:
                output.append(block)
                take = True
            
    
    f.close()
    os.remove("dwarfdump.txt")
    f = open ("dwarfdump.txt", "w")
    for out in output:
        f.write(out)
    f.close()



def process_objdump():
    #This function reads the objdump file into a map indexed by adress that returns the appropriate assembly code.
    #{<adress>, <assembly code>}
    assm = {}
    head_regex = re.compile("(\d|a|b|c|d|e|f){16} <.+>:")
    body = False
    previous_pc = -1
    objdump_file = open('objdump.txt', 'r')
    lines = objdump_file.readlines()
    for line in lines:

        if head_regex.match(line):
            body = True

        elif body is True:
            if line == '\n':
                body = False
                assm[previous_pc][2] = True

            else:
                removed_tabs = re.split('\t', line)

                #extract counter value and convert to decimal integer.
                pc = int(re.sub("[ :]", "", removed_tabs[0]), 16)

                #in the instance of multiple tabs
                if len(removed_tabs) == 3:
                    instr = removed_tabs[2]
                    instr = re.split('\s+', instr)

                    #get possible op code tail
                    if len(instr) < 3:
                        instr = instr[:1]
                    else:
                        instr = instr[:2]


                    assm[pc] = [instr, removed_tabs[1] ,False]
                    previous_pc = pc

    objdump_file.close()
    return assm

def process_modified_dwarfdump():
    #This is the function that processes the previously modified dwarfdump file
    #into a map indexed by adress, that returns the source code and other information.

    #{<pc> : [<file id> : [<line_no>], [<tags>]}
    key_map_source = {}

    head_regex = re.compile("^0x")
    f = open('dwarfdump.txt', 'r')
    lines = f.readlines()

    for line in lines:
        inside = re.search(head_regex, line)
        if inside:
            pc = int(line.split()[0], 0)
            line_no = int(line.split()[1])
            split = line.split()
            if pc in key_map_source:
                if(len(split) == 6):
                    key_map_source[pc][1].append((line_no,))
                elif(len(split) == 7):
                    key_map_source[pc][1].append((line_no, split[6]))
                elif(len(split) == 8):
                    key_map_source[pc][1].append((line_no, split[6], split[7]))
            else:
                if(len(split) == 6):
                    key_map_source[pc] = [(line_no,)]
                elif(len(split) == 7):
                    key_map_source[pc] = [(line_no, split[6])]
                elif(len(split) == 8):
                    key_map_source[pc] = [(line_no, split[6], split[7])]
                
                
    return key_map_source



def combine(file_address, dd_map, assembly):
    keys = list(assembly.keys())
    lines = {}
    dmapkeys = list(dd_map.keys())
    f = open(file_address, 'r')
    code = f.readlines()

    #sorting map by line number
    dd_map = {k: v for k, v in sorted(dd_map.items(), key=lambda item: item[0])}

    
    
    dd_and_src = []

    for pc in range(len(keys)):

        if keys[pc] in dd_map:
            
            if (pc < len(keys)):
                for i in range(len(dd_map[keys[pc]])):
                    dd_and_src.append((code[dd_map[keys[pc]][i][0]-1], assembly[keys[pc]], keys[pc]))

            

                old_pc = pc
                pc += 1

                while(keys[pc] not in dd_map):

                    for i in range(len(dd_map[keys[old_pc]])):
                        dd_and_src.append((code[dd_map[keys[old_pc]][i][0]-1], assembly[keys[pc]], keys[pc]))
                    pc += 1

                if(dmapkeys[len(dmapkeys)-1] == keys[pc]):
                    while(pc < len(keys) and not assembly[keys[pc]][2]):
                        for i in range(len(dd_map[keys[old_pc]])):
                            dd_and_src.append((code[dd_map[keys[old_pc]][i][0]-1], assembly[keys[pc]], keys[pc]))
                        pc += 1
                    break
    return dd_and_src


        
def make_html(as_src_combo):
    cross_indexing = open("XREF/cross_indexing.html", "w+")
    cross_indexing.write("""
        <!DOCTYPE html>
            <html>
                <title>CSC_254 A4</title>
                <style type="text/css">

                = {
                    font-family: monospace;
                    line-height: 1.Sem;
                }

                table {
                    font-family: arial, sans-serif;
                    
                    
                }

                td, th {
                    border: 1px solid #dddddd;
                    width: 400px;
                    padding: 2px;

                div.a {
                    text-align: center;
                }

                div.b {
                    text-align: right;
                }

                .grey {
                    color: #888
                }

            </style>
        </head>
        <body>
            <table>""")

    control_transfer = ["jmp", "je", "jne", "jz", "jg", "jge", "jl", "jle", "callq"]

    lines_seen = []

    old_line = -1 #the line numbere of the previous line

    
    for i in range(len(as_src_combo)):
        cross_indexing.write("<table><tr><td>")

        color = "\"color:black;\""

        line_no = -1
        if as_src_combo[i][2] in dd_map:
            line_no = dd_map[as_src_combo[i][2]][0][0]
        #print(line_no)

        if line_no in lines_seen:
            color = "\"color:gray;\""
        elif line_no != old_line and old_line != -1 and line_no != -1:
            lines_seen.append(line_no)

        
        pc = hex(as_src_combo[i][2])[2:].lstrip('0') #back to adress
        cross_indexing.write("<div id=\""+pc+"\">")
        
        cross_indexing.write("<a href = \"#"+pc+"\">")
        cross_indexing.write(pc+"\t")
        cross_indexing.write("</a>")
        cross_indexing.write("</td>")
        control_trans = False

        if as_src_combo[i][1][0][0] in control_transfer:
            control_trans = True
        
        for l in range(len(as_src_combo[i][1][0])):

            cross_indexing.write("<td>")

            if control_trans and l != 0:
                cross_indexing.write("<a href = \"#"+as_src_combo[i][1][0][l]+"\">")
                cross_indexing.write("<p style = "+color +">" + as_src_combo[i][1][0][l]+"\t</p>")
                cross_indexing.write("</a>")
        
            else:
                cross_indexing.write("<p style = "+color + ">" + as_src_combo[i][1][0][l]+"\t</p>")

            cross_indexing.write("</td>")

        cross_indexing.write("<td>")

        if line_no >= 0 and line_no != old_line:
            cross_indexing.write("<p style = "+color+"> Source line: " + str(line_no) + ": ")
            cross_indexing.write("\"" + as_src_combo[i][0] + "\" </p>")
            

        cross_indexing.write("</td>")
        cross_indexing.write("</tr></table>")
        cross_indexing.write("</div>")
        old_line = line_no
    
    cross_indexing.close()



def create_homepage(time, runtime):
    loc = os.path.dirname(os.path.realpath(__file__))
    index = open("XREF/home.html", "w+")
    index.write("""
        <!DOCTYPE html>
        <html>
            <head>
                <title> Rust Cross-Indexing </title>
                <h1> Rust Cross-Indexing </h1>
            </head>

            <body>
                <h1> Cross-Indexing </h1>
                <h2> by Oliver Otcasek (ootcasek) </h2>
                <br><br>
                <strong> XREF Path: """+loc+"""</strong><br>
                <strong> XREF Time Ran: """ + str(time) + """</strong><br>
                <strong> XREF Run Time: """ + str(runtime) + """</strong><br>
                <a href = "cross_indexing.html"> Link to cross-indexed output. </a> <br>
                <a href= "cross_indexing.html#main"> Link to main location in the cross-indexed file </a>
            </body>
        </html>
        """)

            
# This program eliminates the extraneous info in the dwarfdump file and creates a more appropriate dwarfdump file for this project.

time = str(datetime.datetime.now())
runtime = perf_counter()
check_args()
create_dump_files()
srcs = find_source_files()
alter_dwarfdump()
trim_dwarfdump(srcs)
assembly = process_objdump()
dd_map = process_modified_dwarfdump()
c = combine(srcs.pop()[1], dd_map, assembly)
make_html(c)
runtime -= perf_counter()
runtime *= -1
create_homepage(time, runtime)

