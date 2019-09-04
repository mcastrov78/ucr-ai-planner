class World:

    def __init__(self, atoms, sets):
        self.atoms = atoms
        self.sets = sets

    def models(self, expression):
        return expression.is_modeled_by(self)

    def apply(self, effect):
        new_atoms = self.atoms
        new_sets = self.sets

        #print("effect: %s" % effect)
        changes = effect.get_changes(self)

        new_atoms = new_atoms.union(changes[0])
        new_atoms = new_atoms.difference(changes[1])
        new_world = World(new_atoms, new_sets)

        return new_world

    def __str__(self):
        atoms_str = ", ".join("%s" % atom for atom in self.atoms)
        return atoms_str


class LogicalFormula:
    def is_modeled_by(self, world):
        return False


class Constant(LogicalFormula):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Atom(LogicalFormula):

    def __init__(self, name, parameters):
        self.elements = []
        self.elements.append(name)
        self.elements.append(parameters)
        #print("Atom: ", self.elements)

    def is_modeled_by(self, world):
        return self in world.atoms

    def __str__(self):
        parameters = ", ".join(self.elements[1])
        return "%s(%s)" % (self.elements[0], parameters)

    def __eq__(self, other):
        return self.elements[0] == other.elements[0] and \
               self.elements[1] == other.elements[1]

    def __hash__(self):
        return hash((self.elements[0], tuple(self.elements[1])))


class Or(LogicalFormula):

    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        result = False

        for operand in self.operands:
            if operand.is_modeled_by(world):
                result = True
                break

        return result

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "OR(%s)" % operands_str


class And(LogicalFormula):

    def __init__(self, operands):
        self.operands = operands
        self.additions = set()
        self.deletions = set()

    def is_modeled_by(self, world):
        result = True

        for operand in self.operands:
            if not operand.is_modeled_by(world):
                result = False
                break

        return result

    def get_changes(self, world):
        for this_operand in self.operands:
            if isinstance(this_operand, Not):
                if not this_operand.is_modeled_by(world):
                    self.deletions.add(this_operand.operand)
            else:
                if not this_operand.is_modeled_by(world):
                    self.additions.add(this_operand)

        return self.additions, self.deletions

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "AND(%s)" % operands_str


class Not(LogicalFormula):

    def __init__(self, operand):
        self.operand = operand

    def is_modeled_by(self, world):
        return not self.operand.is_modeled_by(world)

    def __str__(self):
        return "NOT(%s)" % self.operand


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
    #print("AST: ", ast)

    # CHECK THIS ==1 !!!
    if len(ast) == 1:
        return Constant(ast[0])
    else:
        if ast[0] == "or":
            # process OR expression
            operands = []
            for i in range(1, len(ast)):
                # each operand can be an expression on its own
                operands.append(make_expression(ast[i]))
            expression = Or(operands)
        elif ast[0] == "and":
            # process AND expression
            operands = []
            for i in range(1, len(ast)):
                # each operand can be an expression on its own
                operands.append(make_expression(ast[i]))
            expression = And(operands)
        elif ast[0] == "not":
            # process NOT expression
            # each operand can be an expression on its own
            expression = Not(make_expression(ast[1]))
        else:
            # process atom
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
    expressions = set()
    for atom in atoms:
        expressions.add(make_expression(atom))

    return World(expressions, sets)


def models(world, condition):
    """
    This function takes a world and a logical expression, and determines if the expression holds in the given world, i.e. if the world models the condition.
    
    The semantics of the logical operators are the usual ones, i.e. a world models an "and" expression if it models every child of the "and" expression, etc.
    For the quantifiers, when the world is constructed it is passed all possible sets, and the quantifiers will use this dictionary to determine their domain. 
    
    The special "when" operator is only used by the "apply" function (see below), and no world models it.
    
    The return value of this function should be True if the condition holds in the given world, and False otherwise.
    """
    return world.models(condition)

    
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
    return world.apply(effect)

def my_tests():
    expOr = make_expression(("or", "a", "b"))
    print("\nExpression expOr: %s" % expOr)
    expOn = make_expression(("on", "a", "b"))
    print("\nExpression expOn: %s" % expOn)

    # original
    exp = make_expression(("or", ("on", "a", "b"), ("on", "a", "d")))
    print("\nExpression exp: %s" % exp)

    # original
    world = make_world([("on", "a", "b"), ("on", "b", "c"), ("on", "c", "d")], {})
    print("\nWorld: %s" % world)
    print("Models exp (%s): %s" % (exp, models(world, exp)))
    print("Models expOn (%s): %s" % (expOn, models(world, expOn)))

    expOn2 = make_expression(("on", "a", "d"))
    print("\nExpression expOn2: %s" % expOn2)
    print("Models expOn2: %s" % models(world, expOn2))

    expAnd = make_expression(("and", "a", "b"))
    print("\nExpression expAnd: %s" % expAnd)

    expAnd2 = make_expression(("and", ("on", "a", "b"), ("on", "a", "d")))
    print("Expression expAnd2: %s" % expAnd2)
    print("Models expAnd2: %s" % models(world, expAnd2))

    expNot = make_expression(("not", "a"))
    print("\nExpression expNot: %s" % expNot)
    print("Models expNot (%s): %s" % (expNot, models(world, expNot)))

    expNot2 = make_expression(("not", ("on", "a", "b")))
    print("\nExpression expNot2: %s" % expNot2)
    print("Models expNot2: %s" % models(world, expNot2))

    expNot3 = make_expression(("not", ("on", "a", "e")))
    print("\nExpression expNot3: %s" % expNot3)
    print("Models expNot3: %s" % models(world, expNot3))

    # original
    print("\n*** exp: %s" % exp)
    print("models(world, exp)")
    print("Should be True: ", end="")
    print(models(world, exp))

    change = make_expression(["and", ("not", ("on", "a", "b")), ("on", "a", "c")])
    print("\nExpression change: %s" % change)
    print("World: %s" % world)
    new_world = apply(world, change)
    print("New World: %s" % new_world)
    print("World: %s" % world)

    # original
    print("\n*** models(apply(world, change), exp)")
    print("world: %s" % world)
    print("change: %s" % change)
    print("exp: %s" % exp)
    print("Should be False: ", end="")
    print(models(apply(world, change), exp))
    print("world: %s" % world)


if __name__ == "__main__":
    my_tests()
    '''
    exp = make_expression(("or", ("on", "a", "b"), ("on", "a", "d")))
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