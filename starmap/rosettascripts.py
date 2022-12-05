#!/bin/env python
#
# Copyright (c) 2013-2022 by the Universitätsklinikum Hamburg-Eppendorf (UKE)
# Written by Wolfgang Lugmayr <w.lugmayr@uke.de>
#
"""
PyParsing definition of the Rosetta scripts xml structure and the
corresponding handler.
"""

# -----------------------------------------------------------------------------
import sys
from pyparsing import Literal, QuotedString, Word, Group, ZeroOrMore, Forward, OneOrMore, alphanums, ParseException

# -----------------------------------------------------------------------------
grammar = """
Tag := < Name Option* > Tag* </Name > | <Name Option* />
Option := Name + Value
Name := (string without whitespace)
Value := (string without whitespace) | "(string with whitespace)"
"""

# basic definitions
startLiteral = Literal("<").suppress()
endLiteral = Literal(">").suppress()
slashLiteral = Literal("/").suppress()
equalsLiteral = Literal("=") #.suppress()
qString = QuotedString(quoteChar='"', multiline=False)

# simple definitions
name = Word(alphanums + "_")
v = Word(alphanums + "_" + "." + "%") | qString
option = Group(name + equalsLiteral + v)
optionStar = ZeroOrMore(option)

# complex recursive tags
tagStar = Forward()
longTag = startLiteral + name + optionStar + endLiteral + ZeroOrMore(tagStar) + startLiteral + slashLiteral + name + endLiteral
shortTag = startLiteral + name + optionStar + slashLiteral + endLiteral
tagStar << Group(longTag | shortTag)
script = OneOrMore(longTag | shortTag)


# -----------------------------------------------------------------------------
# global variables
scriptStr = ""
subTags = []
valueList = []
tagName = ""
tagList = []



# -----------------------------------------------------------------------------
def reset():
    """Reset the values to initial value"""
    global scriptStr, subTags, valueList, tagName
    scriptStr = ""
    subTags = []
    valueList = []
    tagName = ""


# -----------------------------------------------------------------------------
def cleanupList(l):
    """Removes empty list entries"""
    l[:] = [t for t in l if t]
    for t in l:
        if isinstance(t, list):
            cleanupList(t)


# -----------------------------------------------------------------------------
def appendOption(optList):
    """Reorder options in list"""
    if len(optList) == 3 and optList[1] == '=':
        return " " + optList[0] + optList[1] + '"' + optList[2] + '"'
    return ""


# -----------------------------------------------------------------------------
def asTabbedList(l, indent=0):
    """Print as characters list with tab intends"""
    for t in l:
        if isinstance(t, str):
            print('\t' * indent + str(t))
        elif len(t) == 3 and t[1] == '=':
            print('\t' * indent + appendOption(t))
        elif isinstance(t, list):
            asTabbedList(t, indent+1)


# -----------------------------------------------------------------------------
def asXmlList(l, hasOptions=False, indent=0):
    """Print as characters list with XML and space intends"""
    global scriptStr
    endNameTag = ""
    printedTag = 0
    closeTag = False

    for t in l:
        # <tag></tag>
        if isinstance(t, str) and l.count(t) == 2:
            if printedTag < 1:
                if not hasOptions:
                    scriptStr += '\t' * indent + "<" + str(t) + ">\n"
                else:
                    scriptStr += '\t' * indent + "<" + str(t)
                    closeTag = True
            elif printedTag < 2:
                scriptStr += '\t' * indent + "</" + str(endNameTag) + ">\n"
            endNameTag = t
            printedTag += 1
        elif isinstance(t, str) and l.count(t) == 1:
            scriptStr += '\t' * indent + "<" + str(t)
        elif len(t) == 3 and t[1] == '=':
            scriptStr += appendOption(t)
        elif closeTag:
            scriptStr += ">\n"
            closeTag = False
            hasOptions = False
            if isinstance(t, list) and (len(t) >= 2 and t[1][1] == '='):
                asXmlList(t, True, indent+1)
            else:
                asXmlList(t, False, indent+1)
        elif isinstance(t, list) and (len(t) >= 2 and t[1][1] == '='):
            asXmlList(t, True, indent+1)
        else:
            asXmlList(t, False, indent+1)

    if hasOptions:
        scriptStr += "/>\n"

    return scriptStr


# -----------------------------------------------------------------------------
def removeXmlTagByName(l, tagName):
    """Removes the given XML tag by its name tag"""
    for t in l:
        if isinstance(t, str) and t == tagName:
            # print(l[:])
            # FastRelax relax must always be in the XML file for torsion refinement
            if t == 'FastRelax' and len(l) == 6:
                return
            del l[:]
        elif isinstance(t, list):
            removeXmlTagByName(t, tagName)


# -----------------------------------------------------------------------------
def removeXmlTagByValueName(l, valueName):
    """Removes the given XML tag by its value tag"""
    global tagName, tagList
    for t in l:
        if isinstance(t, str) and t == valueName and l[0] == "name":
            #print "tag=" + tagName + " value=" + t
            del tagList[:]
        elif isinstance(t, list):
            tagName = l[0]
            tagList = l
            removeXmlTagByValueName(t, valueName)


# -----------------------------------------------------------------------------
def removeMoverByName(l, nameList):
    """Removes a Rosetta script mover by its name tag"""
    for t in l:
        if isinstance(t, list) and len(t) == 2:
            if isinstance(t[0], str) and t[0] == "Add":
                #print t
                if len(t[1]) == 3 and t[1][1] == '=' and t[1][0] == "mover":
                    if t[1][2] == nameList:
                        #print t[1][2]
                        del t[:]
        elif isinstance(t, list):
            removeMoverByName(t, nameList)


# -----------------------------------------------------------------------------
def removeTagAndMoverByTagName(l, tag):
    """Removes a Rosetta script mover and the given XML tag by its name tag"""
    reset()
    getTagsByTagName(l, tag)
    #print subTags
    getValueList(subTags, "name")
    #print valueList
    removeXmlTagByName(l, tag)
    for i in range(len(valueList)):
        removeMoverByName(l, valueList[i])
    return


# -----------------------------------------------------------------------------
def removeTagAndMoverByValueName(l, valueName):
    """Removes a Rosetta script mover and the given XML tag by its value tag"""
    reset()
    removeXmlTagByValueName(l, valueName)
    removeMoverByName(l, valueName)
    cleanupList(l)
    return


# -----------------------------------------------------------------------------
def getTagsByTagName(l, tag):
    """Returns all tags with the given name"""
    for t in l:
        if isinstance(t, str) and t == tag:
            global subTags
            subTags.append(l[:])
        elif isinstance(t, list):
            getTagsByTagName(t, tag)


# -----------------------------------------------------------------------------
def getValueList(l, name):
    """Returns all values with the given name"""
    for t in l:
        if len(t) == 3 and t[1] == '=' and t[0] == name:
            global valueList
            valueList.append(t[2])
        elif isinstance(t, list):
            getValueList(t, name)


# -----------------------------------------------------------------------------
def stripTagToNameValue(l, tag):
    """Removes all value entries except the name value of a given tag"""
    for t in l:
        #print t
        if isinstance(t, list) and len(t) > 1:
            if isinstance(t[0], str) and t[0] == tag:
                for i in range(1, len(t)):
                    if t[i][0] != "name":
                        #print t[i]
                        del t[i]
            stripTagToNameValue(t, tag)
        elif isinstance(t, list):
            stripTagToNameValue(t, tag)

    return


# -----------------------------------------------------------------------------
def replaceUserDefinedRebuildingValues(l, tag, residues):
    """Replaces Rosetta script values by the given ones"""
    for t in l:
        if isinstance(t, str) and t == tag:
            c = 0
            for x in l:
                if isinstance(x, list):
                    c += 1
                    if len(x) == 3 and x[0] == "strategy" and x[2] == "user":
                        #x[2] = "user"
                        l.append(['residues', '=', residues])
                    elif len(x) == 3 and x[0] == "residues":
                        x[2] = residues
        elif isinstance(t, list):
            replaceUserDefinedRebuildingValues(t, tag, residues)


# -----------------------------------------------------------------------------
def doRefinementOnly(l):
    """Removes the movers to do Rosetta refinement only"""
    removeTagAndMoverByTagName(l, "CartesianSampler")
    cleanupList(l)
    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    #from __future__ import print_function

    if not len(sys.argv) > 1:
        print(__doc__)
        sys.exit(1)

    infileName = sys.argv[1]
    try:
        parsedScript = script.parseFile(infileName)
        #print parsedScript
        #print(asXmlList(parsedScript.asList()))

        tmpList = parsedScript.asList()
        #doRefinementOnly(tmpList)
        #doUserDefinedRebuilding(tmpList, "22A-36A,56B-77B")
        #removeXmlTagByValueName(tmpList, "reportFSC")
        #cleanupList(tmpList)
        #print tmpList
        removeTagAndMoverByTagName(tmpList, "FastRelax")
        cleanupList(tmpList)

        #print asTabbedList(tmpList)
        print(asXmlList(tmpList))

    except ParseException as err:
        print(err.line)
        print(" "*(err.column-1) + "^")
        print(err)
