import copy


class World:
    """ Represents the world """
    def __init__(self, atoms, sets):
        self.atoms = atoms
        self.sets = sets

    def models(self, expression):
        return expression.is_modeled_by(self)

    def apply(self, effect):
        # get deep copies of the atoms and sets for the new world
        new_atoms = copy.deepcopy(self.atoms)
        new_sets = copy.deepcopy(self.sets)

        # apply additions and deletions caused by the effect to atoms in new world
        changes = effect.get_changes(self)
        new_atoms = new_atoms.union(changes[0])
        new_atoms = new_atoms.difference(changes[1])

        return World(new_atoms, new_sets)


    def apply_relaxed(self, effect):
        # get deep copies of the atoms and sets for the new world
        new_atoms = copy.deepcopy(self.atoms)
        new_sets = copy.deepcopy(self.sets)

        # apply ONLY additions caused by the effect to atoms in new world
        changes = effect.get_changes(self)
        new_atoms = new_atoms.union(changes[0])

        return World(new_atoms, new_sets)


    def __str__(self):
        atoms_str = ", ".join("%s" % atom for atom in self.atoms)
        return atoms_str


class LogicalFormula:
    """ Base logical formula class """
    def is_modeled_by(self, world):
        return False

    def get_changes(self, world):
        return None

    def substitute(self, variable, value):
        return self


class Constant(LogicalFormula):
    def __init__(self, value):
        self.value = value

    def substitute(self, variable, value):
        if self.value == variable:
            return Constant(value)
        return self

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other

    def __hash__(self):
        return hash(self.value)


class VariableSpec:
    """ Represents a variable specification for universal and existential quantifiers """
    def __init__(self, elements):
        self.elements = elements

    def __str__(self):
        parameters = ", ".join(self.elements)
        return "VariableSpec(%s)" % parameters


class Atom(LogicalFormula):
    """ Represents an atom """
    def __init__(self, name, parameters):
        self.elements = []
        self.elements.append(name)
        self.elements.append(parameters)

    def is_modeled_by(self, world):
        return self in world.atoms

    def get_changes(self, world):
        additions = set()
        deletions = set()

        if not self.is_modeled_by(world):
            additions.add(self)

        return additions, deletions

    def substitute(self, variable, value):
        new_elements = []
        for i in range(len(self.elements[1])):
            new_elements.append(self.elements[1][i].substitute(variable, value))
        return Atom(self.elements[0], new_elements)

    def __str__(self):
        parameters = ", ".join("%s" % parameter for parameter in self.elements[1])
        return "%s(%s)" % (self.elements[0], parameters)

    __repr__ = __str__
    
    def __eq__(self, other):
        return self.elements[0] == other.elements[0] and \
               self.elements[1] == other.elements[1]

    def __hash__(self):
        return hash((self.elements[0], tuple(self.elements[1])))


class Or(LogicalFormula):
    """ Represents an or expression """
    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        result = False

        for operand in self.operands:
            if operand.is_modeled_by(world):
                result = True
                break

        return result

    def substitute(self, variable, value):
        new_operands = []
        for operand in self.operands:
            new_operands.append(operand.substitute(variable, value))
        return Or(new_operands)

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "or(%s)" % operands_str


class And(LogicalFormula):
    """ Represents an and expression """
    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        result = True

        for operand in self.operands:
            if not operand.is_modeled_by(world):
                result = False
                break

        return result

    def get_changes(self, world):
        additions = set()
        deletions = set()

        for this_operand in self.operands:
            changes = this_operand.get_changes(world)
            additions = additions.union(changes[0])
            deletions = deletions.union(changes[1])

        return additions, deletions

    def substitute(self, variable, value):
        new_operands = []
        for operand in self.operands:
            new_operands.append(operand.substitute(variable, value))
        return And(new_operands)

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "and(%s)" % operands_str


class Imply(LogicalFormula):
    """ Represents an imply expression """
    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        result = False

        # p -> q <=> ~p v q
        if not self.operands[0].is_modeled_by(world) or self.operands[1].is_modeled_by(world):
            result = True

        return result

    def substitute(self, variable, value):
        return Imply([self.operands[0].substitute(variable, value), self.operands[1].substitute(variable, value)])

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "imply(%s)" % operands_str


class Equals(LogicalFormula):
    """ Represents an equals expression """
    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        result = False

        if self.operands[0] == self.operands[1]:
            result = True

        return result

    def substitute(self, variable, value):
        return Equals([self.operands[0].substitute(variable, value), self.operands[1].substitute(variable, value)])

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "equals(%s)" % operands_str


class When(LogicalFormula):
    """ Represents a when expression """
    def __init__(self, operands):
        self.operands = operands

    def apply(self, world):
        if self.operands[0].is_modeled_by(world):
            return world.apply(self.operands[1])
        return world

    def get_changes(self, world):
        additions = set()
        deletions = set()

        if self.operands[0].is_modeled_by(world):
            changes = self.operands[1].get_changes(world)
            additions = additions.union(changes[0])
            deletions = deletions.union(changes[1])

        return additions, deletions

    def substitute(self, variable, value):
        return When([self.operands[0].substitute(variable, value), self.operands[1].substitute(variable, value)])

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "when(%s)" % operands_str


class ForAll(LogicalFormula):
    """ Represents a universal quantifier expression """
    def __init__(self, operands):
        self.operands = operands

    def get_expanded_for_all(self, world):
        # get set name in variable spec and iterate
        set = world.sets[""]
        if len(self.operands[0].elements) == 3:
            set = world.sets[self.operands[0].elements[2]]

        # substitute variables in expression with values and add expanded expressions to the list
        expanded_list = []
        for value in set:
            expanded_list.append(self.operands[1].substitute(self.operands[0].elements[0], value))

        return And(expanded_list)

    def is_modeled_by(self, world):
        expanded_for_all = self.get_expanded_for_all(world)
        #print("expanded_for_all: %s" % expanded_for_all)
        return expanded_for_all.is_modeled_by(world)

    def get_changes(self, world):
        expanded_for_all = self.get_expanded_for_all(world)
        #print("expanded_for_all: %s" % expanded_for_all)
        return expanded_for_all.get_changes(world)

    def substitute(self, variable, value):
        return ForAll([self.operands[0], self.operands[1].substitute(variable, value)])

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "forall(%s)" % operands_str


class Exists(LogicalFormula):
    """ Represents a universal existential expression """
    def __init__(self, operands):
        self.operands = operands

    def is_modeled_by(self, world):
        # get set name in variable spec and iterate
        set = world.sets[""]
        if len(self.operands[0].elements) == 3:
            set = world.sets[self.operands[0].elements[2]]

        # substitute variables in expression with values and add expanded expressions to the list
        expanded_list = []
        for value in set:
            expanded_list.append(self.operands[1].substitute(self.operands[0].elements[0], value))

        exists_or_exp = Or(expanded_list)
        #print("exists_or_exp: %s" % exists_or_exp)

        return exists_or_exp.is_modeled_by(world)

    def substitute(self, variable, value):
        return ForAll([self.operands[0], self.operands[1].substitute(variable, value)])

    def __str__(self):
        operands_str = ", ".join("%s" % operand for operand in self.operands)
        return "exists(%s)" % operands_str


class Not(LogicalFormula):
    """ Represents a not expression """
    def __init__(self, operand):
        self.operand = operand

    def is_modeled_by(self, world):
        return not self.operand.is_modeled_by(world)

    def get_changes(self, world):
        additions = set()
        deletions = set()

        if self.operand.is_modeled_by(world):
            deletions.add(self.operand)
        else:
            additions.add(self.operand)

        return additions, deletions

    def substitute(self, variable, value):
        return Not(self.operand.substitute(variable, value))

    def __str__(self):
        return "not(%s)" % self.operand


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
    expression = None
    #print("AST: ", ast)

    if isinstance(ast, (tuple, list)):
        # process each possible expression where each operand can be an expression on its own
        if ast[0] == "or":
            expression = Or([make_expression(ast[i]) for i in range(1, len(ast))])
        elif ast[0] == "and":
            expression = And([make_expression(ast[i]) for i in range(1, len(ast))])
        elif ast[0] == "imply":
            expression = Imply([make_expression(ast[1]), make_expression(ast[2])])
        elif ast[0] == "=":
            expression = Equals([make_expression(ast[1]), make_expression(ast[2])])
        elif ast[0] == "when":
            expression = When([make_expression(ast[1]), make_expression(ast[2])])
        elif ast[0] == "forall":
            expression = ForAll([make_expression(ast[1]), make_expression(ast[2])])
        elif ast[0] == "exists":
            expression = Exists([make_expression(ast[1]), make_expression(ast[2])])
        elif ast[0].startswith("?"):
            expression = VariableSpec([ast[i] for i in range(len(ast))])
        elif ast[0] == "not":
            expression = Not(make_expression(ast[1]))
        else:
            expression = Atom(ast[0], [make_expression(ast[i]) for i in range(1, len(ast))])
    else:
        return Constant(ast)

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
    return expression.substitute(variable, value)


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
    print("*********** START OF my_tests ***********")

    # OR and Atom TESTS
    expOr = make_expression(("or", "a", "b"))
    print("\nExpression expOr: %s" % expOr)
    expOn = make_expression(("on", "a", "b"))
    print("\nExpression expOn: %s" % expOn)

    # original
    exp = make_expression(("or", ("on", "a", "b"), ("on", "a", "d")))
    print("\nExpression exp: %s" % exp)

    # World and Models TESTS
    # original test
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

    # NOT TESTS
    expNot = make_expression(("not", "asd"))
    print("\nExpression expNot: %s" % expNot)
    print("Models expNot (%s): %s" % (expNot, models(world, expNot)))

    expNot2 = make_expression(("not", ("on", "a", "b")))
    print("\nExpression expNot2: %s" % expNot2)
    print("Models expNot2: %s" % models(world, expNot2))

    expNot3 = make_expression(("not", ("on", "a", "e")))
    print("\nExpression expNot3: %s" % expNot3)
    print("Models expNot3: %s" % models(world, expNot3))

    # original test
    print("\n*** exp: %s" % exp)
    print("models(world, exp)")
    print("Should be True: ", end="")
    print(models(world, exp))

    # APPLY TESTS
    change = make_expression(("not", ("on", "a", "b")))
    print("\nExpression change: %s" % change)
    print("World: %s" % world)
    new_world = apply(world, change)
    print("New World: %s" % new_world)
    print("World: %s" % world)

    for atom in new_world.atoms:
        atom.elements = ["x", "y"]
    print("New World: %s" % new_world)
    print("World: %s" % world)

    change = make_expression(("on", "a", "d"))
    print("\nExpression change: %s" % change)
    print("World: %s" % world)
    new_world = apply(world, change)
    print("New World: %s" % new_world)
    print("World: %s" % world)

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

    # IMPLY TESTS
    expImply = make_expression(("imply", "a", "b"))
    print("\nExpression expImply: %s" % expImply)

    expImply2 = make_expression(("imply", ("on", "a", "b"), ("on", "a", "d")))
    print("\nExpression expImply2: %s" % expImply2)
    print("Models expImply2 (%s): %s" % (expImply2, models(world, expImply2)))

    expImply3 = make_expression(("imply", ("on", "a", "d"), ("on", "a", "b")))
    print("\nExpression expImply3: %s" % expImply3)
    print("Models expImply3 (%s): %s" % (expImply3, models(world, expImply3)))

    # EQUALS TESTS
    expEquals = make_expression(("=", "a", "b"))
    print("\nExpression expEquals: %s" % expEquals)
    print("Expression expEquals: %s" % expEquals.is_modeled_by(world))

    expEquals2 = make_expression(("=", "a", "a"))
    print("\nExpression expEquals: %s" % expEquals2)
    print("Expression expEquals2: %s" % expEquals2.is_modeled_by(world))

    # WHEN TESTS
    expWhen = make_expression(("when", "a", "b"))
    print("\nExpression expWhen: %s" % expWhen)

    expWhen2 = make_expression(("when", ("on", "a", "b"), ("on", "a", "d")))
    print("\nExpression expWhen2: %s" % expWhen2)
    print("world: %s" % world)
    print("expWhen2 (%s) world: %s" % (expWhen2, expWhen2.apply(world)))

    expWhen3 = make_expression(("when", ("on", "b", "b"), ("on", "a", "d")))
    print("\nExpression expWhen3: %s" % expWhen3)
    print("world: %s" % world)
    print("expWhen3 (%s) world: %s" % (expWhen3, expWhen3.apply(world)))

    # FORALL TESTS
    world = make_world([("at", "store", "mickey"), ("at", "airport", "minny")],
                       {"Locations": ["home", "park", "store", "airport", "theater"],
                        "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]})

    world2 = make_world([("at", "home", "mickey"), ("at", "park", "mickey"), ("at", "store", "mickey"), ("at", "airport", "mickey"), ("at", "theater", "mickey")],
                       {"Locations": ["home", "park", "store", "airport", "theater"],
                        "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]})
    print("\nworld: %s" % world)
    print("\nworld2: %s" % world2)

    expForAll = make_expression(("forall", ("?l", "-", "Locations"), (("at", "?l", "mickey"))))
    print("\nExpression expForAll: %s" % expForAll)
    print("expForAll.is_modeled_by(world2): %s" % expForAll.is_modeled_by(world2))

    expForAll2 = make_expression(("forall", ("?l", "-", "Locations"), ("imply", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForAll2: %s" % expForAll2)
    print("expForAll2.is_modeled_by(world): %s" % expForAll2.is_modeled_by(world))

    expForAllAnd = make_expression(("forall", ("?l", "-", "Locations"), ("and", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForAllAnd: %s" % expForAllAnd)
    print("expForAllAnd.is_modeled_by(world): %s" % expForAllAnd.is_modeled_by(world))

    expForAllOr = make_expression(("forall", ("?l", "-", "Locations"), ("or", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForAllOr: %s" % expForAllOr)
    print("expForAllOr.is_modeled_by(world): %s" % expForAllOr.is_modeled_by(world))

    holmes_world = make_world([("knows", "holmes", "watson")], \
                   {"people": ["holmes", "watson", "moriarty", "adler"],
                    "stories": ["signoffour", "scandalinbohemia"],
                    "": ["holmes", "watson", "moriarty", "adler", "signoffour", "scandalinbohemia"]})
    print("\nholmes_world: %s" % holmes_world)

    expForAllVar1 = make_expression(("forall", ("?s", "-", "stories"), ("knows", "holmes", "?s")))
    print("\nExpression expForAllVar1: %s" % expForAllVar1)
    print("expForAllVar1.is_modeled_by: %s" % expForAllVar1.is_modeled_by(holmes_world))

    expForAllVar1Apply = make_expression(("forall", ("?s", "-", "stories"), ("knows", "holmes", "?s")))
    print("\nExpression expForAllVar1Apply: %s" % expForAllVar1Apply)
    new_holmes_world = holmes_world.apply(expForAllVar1Apply)
    print("new_holmes_world: %s" % new_holmes_world)

    expForAllVar2 = make_expression(("forall", ("?s",), ("knows", "holmes", "?s")))
    print("\nExpression expForAllVar1: %s" % expForAllVar2)
    print("expForAllVar2.is_modeled_by: %s" % expForAllVar2.is_modeled_by(holmes_world))

    # EXISTS TESTS
    expForExists = make_expression(("exists", ("?l", "-", "Locations"), (("at", "?l", "mickey"))))
    print("\nExpression expForExists: %s" % expForExists)
    print("expForExists.is_modeled_by(world): %s" % expForExists.is_modeled_by(world))

    expForExists2 = make_expression(("exists", ("?l", "-", "Locations"), ("imply", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForExists2: %s" % expForExists2)
    print("expForExists2.is_modeled_by(world): %s" % expForExists2.is_modeled_by(world))

    expForExistsAnd = make_expression(("exists", ("?l", "-", "Locations"), ("and", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForExistsAnd: %s" % expForExistsAnd)
    print("expForExistsAnd.is_modeled_by(world): %s" % expForExistsAnd.is_modeled_by(world))

    expForExistsOr = make_expression(("exists", ("?l", "-", "Locations"), ("or", ("at", "?l", "mickey"), ("at", "?l", "minny"))))
    print("\nExpression expForExistsOr: %s" % expForExistsOr)
    print("expForExistsOr.is_modeled_by(world): %s" % expForExistsOr.is_modeled_by(world))

    expForExistsVar1 = make_expression(("exists", ("?s", "-", "stories"), ("knows", "holmes", "?s")))
    print("\nExpression expForExistsVar1: %s" % expForExistsVar1)
    print("expForExistsVar1.is_modeled_by: %s" % expForExistsVar1.is_modeled_by(holmes_world))

    expForExistsVar2 = make_expression(("exists", ("?s",), ("knows", "holmes", "?s")))
    print("\nExpression expForExistsVar2: %s" % expForExistsVar2)
    print("expForExistsVar2.is_modeled_by: %s" % expForExistsVar2.is_modeled_by(holmes_world))

    # Testing SUBSTITUTE
    expAndSubstitute = make_expression(("and", ("at", "?l", "mickey"), ("at", "?l", "minny")))
    expAndSubstitute2 = substitute(expAndSubstitute, "?l", "home")
    print("\nExpression expAndSubstitute: %s" % expAndSubstitute)
    print("Expression expAndSubstitute2: %s" % expAndSubstitute2)

    expOrSubstitute = make_expression(("or", ("at", "?l", "mickey"), ("at", "?l", "minny")))
    expOrSubstitute2 = substitute(expOrSubstitute, "?l", "home")
    print("\nExpression expOrSubstitute: %s" % expOrSubstitute)
    print("Expression expOrSubstitute2: %s" % expOrSubstitute2)

    expNotSubstitute = make_expression(("not", ("at", "?l", "mickey")))
    expNotSubstitute2 = substitute(expNotSubstitute, "?l", "home")
    print("\nExpression expNotSubstitute: %s" % expNotSubstitute)
    print("Expression expNotSubstitute2: %s" % expNotSubstitute2)

    print("mickey/minny example")
    world = make_world([("at", "store", "mickey"), ("at", "airport", "minny")],
                       {"Locations": ["home", "park", "store", "airport", "theater"],
                        "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]})
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

    print("world: %s" % world)
    print("exp: %s" % exp)
    print("Should be True: ", end="")
    print(models(world, exp))

    become_friends = make_expression(("friends", "mickey", "minny"))
    print("\nbecome_friends: %s" % become_friends)
    friendsworld = apply(world, become_friends)
    print("friendsworld: %s" % friendsworld)
    print("exp: %s" % exp)
    print("Should be False: ", end="")
    print(models(friendsworld, exp))

    move_minny = make_expression(("and", ("at", "store", "minny"), ("not", ("at", "airport", "minny"))))
    print("\nmove_minny: %s" % move_minny)
    movedworld = apply(friendsworld, move_minny)
    print("movedworld: %s" % movedworld)
    print("exp: %s" % exp)
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
    print("\nmove_both_cond: %s" % move_both_cond)
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

    print("\nmovedworld: %s" % movedworld)
    print("move_both_cond: %s" % move_both_cond)
    print("apply(movedworld, move_both_cond): %s" % apply(movedworld, move_both_cond))
    print("exp1: %s" % exp1)

    print("Should be True: ", end="")
    print(models(apply(movedworld, move_both_cond), exp1))

    print("\napply(friendsworld, move_both_cond): %s" % apply(friendsworld, move_both_cond))
    print("exp1: %s" % exp1)
    print("Should be False: ", end="")
    print(models(apply(friendsworld, move_both_cond), exp1))

    print("\n*********** END OF my_tests ***********\n")

if __name__ == "__main__":
    # ALL OF MY DIRTY TESTS ARE HERE
    my_tests()

    # ALL OF MARKUS CLEAN TESTS ARE HERE
    exp = make_expression(("or", ("on", "a", "b"), ("on", "a", "d")))
    world = make_world([("on", "a", "b"), ("on", "b", "c"), ("on", "c", "d")], {})

    print("Should be True: ", end="")
    print(models(world, exp))
    change = make_expression(["and", ("not", ("on", "a", "b")), ("on", "a", "c")])

    print("Should be False: ", end="")
    print(models(apply(world, change), exp))

    print("mickey/minny example")
    world = make_world([("at", "store", "mickey"), ("at", "airport", "minny")],
                       {"Locations": ["home", "park", "store", "airport", "theater"],
                        "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]})
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