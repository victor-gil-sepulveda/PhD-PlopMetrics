## Author: Victor Gil Sepulveda
## Started: 17/09/10
## First release: 19/Sep/2010
## Version: 1.0
##
## Description:
## ------------
## This file includes some functions to work with plop generated trajectory files. Its main aim is to allow the user
## to select and write the different models of the trajectory using a simple but powerful selection languaje.


##-------------------------------------------
## genSingleTraj(name,records,selection)
##-------------------------------------------
## This function will write a single file which name will be 'name' (where you can also define a local or global path)
## using the records stored in 'selection'. The 'records' parameter will be the list obtained when using processDir.
##
##
##-------------------------------------------
## genMetricsFile(name, metrics, selection)
##-------------------------------------------
## This function will write a single file with the metrics in 'metrics' in colums. 'name' and 'selection' are the file
## name to write and the selected records.


import sys
import os
import numpy
import re

def toNumber(n):
    """
    Converts a string (n) into a float or integer.
    """
    try:
	    return float(n)
    except:
	    try:
		    return int(n)
	    except:
		    return 0

def processDir(directory, file_name_commnon_part=""):
    """
    This function will create a list of metric records (which are dictionaries) from the trajectory files in a given
    directory 'dir'.
    You can also specify the common part of the name of the files, or nothing if you want to parse ALL the files inside
    the folder.

    Examples:

    records = processDir("f","traj")

    This sentence will return an array of records (stored in 'records') for all the metrics in all the files in the 'f'
    directory where 'traj' is PART OF its name (this means it will also parse traj.01.pdb, traj.02.pdb... but also
    mytraj.pdb, atrajh.pdb...)

    records = processDir("f")

    In this case it will parse ALL the files inside the 'f' folder.
    """
    dirList = []
    allList=os.listdir(directory)
    for n in allList:
        if file_name_commnon_part in n:
            dirList.append(n)

    records = []
    for i, fname in enumerate(dirList):
        print "Processing %s ( %d of %d )" %(fname, i+1, len(dirList))
        processFile(os.path.join(directory,fname), records)
    return records

def processREMARK(record_line):
    """
    Processes a "REMARK key value" line in order to extract the key (using lower case letters).
    If the key has one or more spaces, it will change it by underscores "_". e.g.

    #REMARK  L1 Binding Ene    -81.535  => li_binding_ene
    #REMARK  L1  Binding Ene    -81.535 => li_binding_ene too

    Returns the key and value for that remark
    """

    parts = record_line.split()
    record_key = "_".join(parts[1:-1])
    # special case
    if '|' in record_key[-1]:
        # Then is a remark of type
        #REMARK  TOTALE            -8690.283
        #REMARK  Steps|              626.000
        #REMARK  L1  Binding Ene|    -81.535
        record_key = record_key[0:-1]

    return record_key.lower(), toNumber(parts[-1])

def processFile(filename, records):
    """
    Reads a file and extracts the information written in the REMARKS.
    """
    file_handler = open(filename)

    record = None
    last_was_remark = False
    line_number = 0
    for l in file_handler:
        if l[0:6] == "REMARK":
            if not last_was_remark:
                if record is  not None:
                    # Store record
                    del record["body"][1:-1]
                    records.append(record)
                # Create a new record
                record = {"file":filename,"body":[]}
            key, value = processREMARK(l)
            record[key] = value			
            last_was_remark = True
        else:
            record["body"].append(line_number)
            last_was_remark = False
        line_number += 1
    file_handler.close()

def process_tag(tag):
    """
    Changes spaces by underscores exactly like in the 'processREMARK' function. Then
    removes the single quotes.
    """  
    return ("_".join( tag.split()))

def filterRecords(expression, records):
    """
    Given a boolean expression written in 'expression', it will choose and return a subset of the 'records' list parameter
    with all the records that fulfill 'expression'

    Examples:

    Think that you have this metrics stored inside your .traj files : 'energy', 'totale', 'metrop', 'proc';
    and you want to know which models in processor 1 have energy below -26759. Just use this function like this:

    selection = filterRecords("Proc == 1 and Energy<-26759",records)

    In your boolean expression write any python-compliant sentence and it will do the trick. It's also case-insensitive.

    Do you want to extract models with energy between two values globally declared? you can!:

    X = -10000
    Y = -20000
    selection = filterRecords("(Energy<X and Energy>Y)",records)

    And in general you can use any complex expression using boolean operators and parentheses.
    """

    ## Format the string
    tags = ["not","and","or",">","<","==","+","-","(",")"]
    expression = expression.lower()
    assert not ">=" in expression and not "<=" in expression, "You cannot use '>=' or '<=' in your expressions."
    
    ## Identify metrics in expression
    tags = re.findall(r"'(.*?)'", expression)
    
    # Substitute keys by the p keys
    for tag in set(tags):
        expression = expression.replace("'%s'"%tag, "r['%s']"%process_tag(tag))
    #print expression
    
    selection = []
    for r in records:
        if eval(expression):
            selection.append(r)

    return selection


def regenerate_remarks(record, file_handler):
    """
    Creates new remarks with the keys. At this point it is not possible to get the original
    remarks again (it would be with some more effort, but it is worthless).
    """
    for key in record:
        if not key in ["body","filename"]:
             file_handler.write("REMARK %s %s\n"%(key, record[key]))

def copyChunck(origin, to, start,end):
	to.writelines(open(origin,"r").readlines()[start:end+1])

def copyChunck2(origin, to, start,end):
    from_file = open(origin)
    for i, line in enumerate(from_file):
        if i >=  start and i <= end:
            to.write(line)
    from_file.close()

def genSingleTraj(name, records, selection):
    """
    Copies the contents of the models of interest (in selection) into another file.
    """
    out_handler = open(name,"w")

    for record in selection:
        regenerate_remarks(record, out_handler)
        copyChunck2(record['file'], out_handler, record['body'][0],record['body'][1])

    out_handler.close()

def genMetricsFile(name, metrics, selection):
	numpy.savetxt(name, genMetrics(metrics, selection))

def genMetrics(metrics, selection):
	filtered_metrics = []
	for r in selection:
		this_metrics = []
		for m in metrics:
			try:
				this_metrics.append(r[process_tag(m.lower())])
			except KeyError:
				this_metrics.append(0)
		filtered_metrics.append(this_metrics)
	return numpy.array(filtered_metrics)

