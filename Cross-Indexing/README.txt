Cross Indexing Rust
Oliver Otcasek 



The purpose of this project was to create a cross-indexing program. This project uses dwarfdump information to build an html page that displays the source code of 
an object file given a compiled object file.

The main program, cross_indexing.py, first creates a dwarfdump and an objectdump file for a given object file compiled by the
Rust compiler. Then, it uses the "compilation unit" information in the dwarfdump file to determine the name and path of the source code file. After it has determinedd this, dwarfdump --debug-line is used to get the line numbers of every line of code used in the input program, and it is parsed (using the file name) to only include information relevant to
the source file. Finally, it parses the line numbers for the source code file, and matches the adresses given by the
dwarfdump file with the objectdump file to determine which lines of source code go with which lines of assembly. Then,
an html file is created and this information is written down in a table. A homepage (home.html) is also included and
has additional information about wwhen the program cross_indexing.py was run and where it was run.

All of the product html files are in the "cross_indexing" directory.

This project was created using llvm dwarfdump 10.0.1. Importantly, the version of llvm
and Dwarf can affect the way this project works. If for example the ordering of elements in the dwarfdump file
were different, it could conceivably crash or produce incorrect results. It is recommended this version is used.


to run this project, compile a Rust file using the Rustc compiler and the -g flag (Rusts -g hello.rs) and run cross_indexing.py 
by running "python cross_indexing.py <objfile>". The html results will appear in the cross_indexing directory.


cross_index.py must be run from the root directory of the project, as otherwise the cross_indexing directory will not be found.


How to run:

first, compile your Rust file with debugging information:
"rustc -g example.rs"
then run cross_indexing.py:
"python cross_indexing.py example"
Look in the cross_indexing directory for the html results.

Thank you,
Please do not use this work dishonestly.
