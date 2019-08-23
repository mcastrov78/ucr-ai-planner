class World:
    __atoms = set()

    def add_atom(self, atom):
        self.__atoms.add(atom)

    def atoms(self):
        return self.__atoms


class LogicalFormula:
    def is_modeled_by(self, world):
        return False


class Constant(LogicalFormula):
    __value = None

    def __init__(self, value):
        self.__value = value

    def value(self):
        return self.__value

    def __str__(self):
        return self.__value


class Atom(LogicalFormula):
    __atom = None

    def __init__(self, name, parameters):
        self.__atom = []
        self.__atom.append(name)
        self.__atom.append(parameters)
        print("Atom: ", self.__atom)

    def is_modeled_by(self, world):
        return self.__atom in world.atoms

    def __str__(self):
        parameters = ", ".join(self.__atom[1])
        return "%s(%s)" % (self.__atom[0], parameters)


class Or(LogicalFormula):
    operands = []

    def __init__(self, operands):
        self.__operands = operands

    def is_modeled_by(self, world):
        result = False

        for operand in self.__operands:
            if operand:
                result = True
                break

        return result

    def __str__(self):
        operands = ""
        for operand in self.__operands:
            operands += str(operand) + " "
        return "or(%s)" % operands


def make_expression(ast):
    """
    This function receives a sequence (list or tuple) representing the abstract syntax tree of a logical expression and returns an expression object suitable for further processing.
    
    In the Abstract Syntax Tree, the first element of the sequence is the operator (if applicable), with the subsequent items being the arguments to that operatior. The possible operators are:
    
       - "and" with *arbitrarily many parameters*
       - "or" with *arbitrarily many parameters*
       - "not" with exactly one parameter 
       - "=" with exactly two parameters which are variables or constants
       - "imply" with exactly two parameters 
       - "when" with exactly two parameters 
       - "exists" with exactly two parameters, where the first one is a variable specification
       - "forall" with exactly two parameters, where the first one is a variable specification
    
    Unless otherwise noted parameters may be, in turn, arbitrary expressions. Variable specifications are sequences of one or three elements:
       - A variable specification of the form ("?s", "-", "Stories") refers to a variable with name "?s", which is an element of the set "Stories"
       - A variable specification of the form ("?s",) refers to a variable with name "?s" with no type 
       
    If the first element of the passed sequence is not a parameter name, it can be assumed to be the name of a predicate in an atomic expression. In this case, 
    the remaining elements are the parameters, which may be constants or variables.
    
    An example for an abstract syntax tree corresponding to the expression 
          "forall s in stories: (murdermystery(s) imply (at(sherlock, bakerstreet) and not at(watson, bakerstreet) and at(body, crimescene)))" 
    would be (formatted for readability):
    
        ("forall", ("?s", "-", "Stories"), 
                   ("imply", 
                         ("murdermystery", "?s"),
                         ("and", 
                              ("at", "sherlock", "bakerstreet"),
                              ("not", 
                                   ("at", "watson", "bakerstreet")
                              ),
                              ("at", "body", "crimescene")
                         )
                   )
        )
    
    The return value of this function can be an arbitrary python object representing the expression, which will later be passed to the functions listed below. For notes on the "when" operator, 
    please refer to the documentation of the function "apply" below. Hint: A good way to represent logical formulas is to use objects that mirror the abstract syntax tree, e.g. an "And" object with 
    a "children" member, that then performs the operations described below.
    """
    expression = None;
    print("AST: ", ast)
    #print("len(", ast, "): ", len(ast))

    if len(ast) == 1:
        return Constant(ast[0])
    else:
        if ast[0] == "or":
            operands = []
            for i in range(1, len(ast)):
                operands.append(make_expression(ast[i]))
            expression = Or(operands)
        else:
            parameters = []
            for i in range(1, len(ast)):
                parameters.append(ast[i])
            expression = Atom(ast[0], parameters)

    return expression

    
def make_world(atoms, sets):
    """
    This function receives a list of atomic propositions, and a dictionary of sets and returns an object representing a logical world.
    
    The format of atoms passed to this function is identical to the atomic expressions passed to make_expression above, i.e. 
    the first element specifies the name of the predicate and the remaining elements are the parameters. For example 
       ("on", "a", "b") represents the atom "at(a, b)"
       
    The sets are passed as a dictionary, with the keys defining the names of all available sets, each mapping to a sequence of strings. 
    For example: {"people": ["holmes", "watson", "moriarty", "adler"], 
                  "stories": ["signoffour", "scandalinbohemia"], 
                  "": ["holmes", "watson", "moriarty", "adler", "signoffour", "scandalinbohemia"]}
                  
    The entry with the key "" contains all possible constants, and can be used if a variable is not given any particular domain.
    
    The world has to store these sets in order to allow the quantifiers forall and exists to use them. When evaluated, the forall operator from the 
    example above would look up the set "stories" in the world, and use the values found within to expand the formula.
    
    Similar to make_expression, this function returns an arbitrary python object that will only be used to pass to the functions below. Hint: It may be beneficial 
    to store the atoms in a set using the same representation as for atomic expressions, and the set dictioary as-is.
    """
    return None


def models(world, condition):
    """
    This function takes a world and a logical expression, and determines if the expression holds in the given world, i.e. if the world models the condition.
    
    The semantics of the logical operators are the usual ones, i.e. a world models an "and" expression if it models every child of the "and" expression, etc.
    For the quantifiers, when the world is constructed it is passed all possible sets, and the quantifiers will use this dictionary to determine their domain. 
    
    The special "when" operator is only used by the "apply" function (see below), and no world models it.
    
    The return value of this function should be True if the condition holds in the given world, and False otherwise.
    """
    return False

    
def substitute(expression, variable, value):
    """
    This function takes an expression, the name of a variable (usually starting with a question mark), and a constant value, and returns a *new* expression with all occurences of the variable 
    replaced with the value
    
    Do *not* replace the variable in-place, always return a new expression object. When you implement the quantifiers, you should use this same functionality to expand the formula to all possible 
    replacements for the variable that is quantified over.
    """
    return expression


def apply(world, effect):
    """
    This function takes a world, and an expression, and returns a new world, with the expression used to change the world. 
    
    For the effect you can assume the following restrictions:
       - The basic structure of the effect is a conjunction ("and") of modifications.
       - Each modification may be a literal (atom, or negation of an atom), a forall expression, or a when expression 
       - In the world produced by the application, positive literals should be added to the atoms of the world, and negative literals should be removed 
       - Forall expressions should be expanded by substituting the variable and processed recursively in the same way (the inner expression will only contain a conjunction of 
             literals, forall expressions, and when expressions as well)
       - "when" expressions have two parameters: A condition (which may be an arbitrary expression), and an effect, which follows the same restrictions (conjunction of literals, forall expressions and when expressions)
             The way "when" expressions are applied to a world depends on the condition: If the world models the condition (i.e. models(world, condition) is true, the effect is applied to the world. Otherwise, nothing happens.
             "when" expressions provide a nice, succinct way to define conditional effects, e.g. if someone is trying to open a door, the door will only open if it is unlocked.
             
    If an effect would cause the same atom to be set to true and to false, it should be set to false, i.e. removed from the set.
             
    The result of this function should be a *new* world, with the changes defined by the effect applied to the atoms, but with the same definition of sets as the original world. 
    
    Hint: If your world stores the atoms in a set, you can determine the change of the effect as two sets: an add set and a delete set, and get the atoms for the new world using basic set operations.
    """
    return world


if __name__ == "__main__":

    exp = make_expression(("or", "a", "b"))
    print("Expression 1: %s\n" % exp)
    exp = make_expression(("on", "a", "b"))
    print("Expression 2: %s\n" % exp)

    exp = make_expression(("or", ("on", "a", "b"), ("on", "a", "d")))
    print("Expression 3: %s\n" % exp)

    '''
    world = make_world([("on", "a", "b"), ("on", "b", "c"), ("on", "c", "d")], {})
    
    print("Should be True: ", end="")
    print(models(world, exp))
    change = make_expression(["and", ("not", ("on", "a", "b")), ("on", "a", "c")])
    
    print("Should be False: ", end="")
    print(models(apply(world, change), exp))
    
    print("mickey/minny example")
    world = make_world([("at", "store", "mickey"), ("at", "airport", "minny")], {"Locations": ["home", "park", "store", "airport", "theater"], "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]})
    exp = make_expression(("and", 
        ("not", ("at", "park", "mickey")), 
        ("or", 
              ("at", "home", "mickey"), 
              ("at", "store", "mickey"), 
              ("at", "theater", "mickey"), 
              ("at", "airport", "mickey")), 
        ("imply", 
                  ("friends", "mickey", "minny"), 
                  ("forall", 
                            ("?l", "-", "Locations"),
                            ("imply",
                                    ("at", "?l", "mickey"),
                                    ("at", "?l", "minny"))))))
                                    
    print("Should be True: ", end="")
    print(models(world, exp))
    become_friends = make_expression(("friends", "mickey", "minny"))
    friendsworld = apply(world, become_friends)
    print("Should be False: ", end="")
    print(models(friendsworld, exp))
    move_minny = make_expression(("and", ("at", "store", "minny"), ("not", ("at", "airport", "minny"))))
    
    movedworld = apply(friendsworld, move_minny)
    print("Should be True: ", end="")
    print(models(movedworld, exp))

    move_both_cond = make_expression(("and", 
                                           ("at", "home", "mickey"), 
                                           ("not", ("at", "store", "mickey")), 
                                           ("when", 
                                                 ("at", "store", "minny"), 
                                                 ("and", 
                                                      ("at", "home", "minny"), 
                                                      ("not", ("at", "store", "minny"))))))

    print("Should be True: ", end="")
    print(models(apply(movedworld, move_both_cond), exp))
    
    print("Should be False: ", end="")
    print(models(apply(friendsworld, move_both_cond), exp))
    
    exp1 = make_expression(("forall", 
                            ("?l", "-", "Locations"),
                            ("forall",
                                  ("?l1", "-", "Locations"),
                                  ("imply", 
                                       ("and", ("at", "?l", "mickey"),
                                               ("at", "?l1", "minny")),
                                       ("=", "?l", "?l1")))))
                                       
    print("Should be True: ", end="")
    print(models(apply(movedworld, move_both_cond), exp1))
    
    print("Should be False: ", end="")
    print(models(apply(friendsworld, move_both_cond), exp1))
    '''