import assign  #from assign import Assign
from .variables import *
from .armadillo import *
from ..configure import frontend, datatypes
import matlab2cpp

Declare = "struct %(name)s"

def Counter(node):
    return "%(name)s = %(value)s"

#def Fvar(node): #defined in variables.py
#    return "%(name)s.%(value)s"
    
# NOTE: The default implementation of Fget in variables.py doesn't produce
# correct code e.g:
# m:   prmStr.Pilots(:,1:numSym,1:numTx);
# cpp: prmStr.Pilots(m2cpp::span<uvec>(0, prmStr.n_rows-1)) ;
#                                               | -> prmStr.Pilots
# TO BE FIXED?

# NF_DEBUG: Take the default (in variables.py) for now
#def Fget(node):
#    # NF_DEBUG: original code was returning None -> BANG!
#    return "%(name)s.%(value)s(", ", ", ")"
#    pass

def SFget(node):
    name = "%(name)s[(%(0)s) - 1].%(value)s"
    # Interpolation
    name = name % node.properties()

    # Creating a temporary node in order to use the "Get" properties 
    structs = node.program[3]
    struct = structs[structs.names.index(node.name)]
    t = struct[struct.names.index(node.value)]

    tmp = matlab2cpp.collection.Get(node,
                                    name, 
                                    cur=node.cur,
                                    code=node.code)
    # Set the tentative type
    tmp.declare = t
    for i in node.children[1:-1]:
        tmp.children.append(i)
        i.parent = tmp

    # resolve the type
    frontend.loop(tmp, True)
    frontend.loop(tmp, True)

    tmp.translate(only=False)
    s = tmp
    node.children.pop();
    for i in node.children[1:]:
        i.parent = node

    return "/*SFget*/" + str(s)

def SFset(node):
    name = "%(name)s[(%(0)s) - 1].%(value)s"
    # Interpolation
    name = name % node.properties()

    # Creating a temporary node in order to use the "Get" properties 
    structs = node.program[3]
    struct = structs[structs.names.index(node.name)]
    t = struct[struct.names.index(node.value)]

    tmp = matlab2cpp.collection.Set(node,
                                    name, 
                                    cur=node.cur,
                                    code=node.code)
    # Set the tentative type
    tmp.declare = t
    for i in node.children[1:-1]:
        tmp.children.append(i)

    # resolve the type
    frontend.loop(tmp, True)
    frontend.loop(tmp, True)

    tmp.translate(only=True)
    s = tmp
    node.children.pop();

    node.type = tmp.type

    return "/*SFset*/" + str(s)

def Fset(node):
    return "%(name)s.%(value)s[", ", ", "-1]"

def Matrix(node):
    if node.backend == "structs":
        if node[0].cls == "Vector":
            if len(node[0]) == 1:
                return "%(0)s"
    return "[", ", ", "]"

def Assign(node):
    return assign.Assign(node) # Default

    lhs, rhs = node
    print('here')
    # assign a my_var = [a.val], a is a structs, my_var should be a vec
    if node[1].cls == "Matrix" and node[1].backend == "structs":
        element = rhs[0][0]
        if element.backend == "structs":
            size = rhs.str
            var = lhs.name
            name = element.name
            value = element.value

            declares = node.func[0]
            if "_i" not in declares:
                declare = matlab2cpp.collection.Var(declares, "_i")
                declare.type = "int"
                declare.backend = "int"
                declares.translate()
            
            string = var + ".resize(" + size + ") ;\n" +\
                "for (_i=0; _i<" + size + "; ++_i)\n  "+\
                var + "[_i] = " + name + "[_i]." + value + " ;"

            return string

    return "%(0)s = %(1)s"

