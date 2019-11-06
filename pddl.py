import re
import sys
import expressions


class Action:
    """This class makes it easier to handle all possible Action parts"""
    def __init__(self, name):
        self.name = name
        self.parameters = {}
        self.precondition = None
        self.effect = None

    def __str__(self):
        predicate_str = "{NAME: %s, PARAMETERS: " % self.name
        predicate_str += ", ".join("%s: %s" % (k, v) for (k, v) in self.parameters.items())
        predicate_str += ", PRECONDITION: %s" % self.precondition
        predicate_str += ", EFFECT: %s}" % self.effect
        return predicate_str

    __repr__ = __str__


def get_stack_from_pddl(fname):
    """Builds and returns a stack after parsing a PDDL file"""
    stack = []
    list = []

    with open(fname) as file:
        # remove comment lines
        fileContentNoComments = re.sub(r';.*$', '', file.read(), flags=re.MULTILINE).lower()
        #print(fileContentNoComments)

        # tokenize
        for token in re.findall(r'[()]|[^\s()]+', fileContentNoComments):
            #print(token)
            if token == ")":
                list = []
                poppedToken = stack.pop()
                while poppedToken != "(":
                    list.append(poppedToken)
                    poppedToken = stack.pop()
                list.reverse()
                stack.append(list)
            else:
                stack.append(token)
    return stack


def process_parameters(parameters, store_order=False):
    """Generic method to parse parameters with types of the form '?param - type' and its variances"""
    parameters_map = {}
    param_of_type = []
    dash_found = False

    # traverse all parameters parts
    i = 0
    for param_part in parameters:
        # process type
        if dash_found:
            # if type is already defined, add param to existing list, if not, assign new list to the type
            if param_part in parameters_map:
                parameters_map[param_part].append(*param_of_type)
            else:
                parameters_map[param_part] = param_of_type
            param_of_type = []
            dash_found = False
            continue

        if param_part != "-":
            # this is a parameter, in some cases we want to keep the order info (like to print action names)
            if store_order:
                param_of_type.append([param_part, i])
                i += 1
            else:
                param_of_type.append(param_part)
        else:
            # a type is next
            dash_found = True

    # if there is no type associated with the last parameter(s)
    if len(param_of_type) > 0:
        parameters_map[""] = param_of_type

    return parameters_map


def parse_domain(fname):
    """
    Parses a PDDL domain file contained in the file fname
    
    The return value of this function is passed to planner.plan, and does not have to follow any particular format
    """
    stack = get_stack_from_pddl(fname)
    pddl_types = []
    pddl_constants = {}
    pddl_predicates = {}
    pddl_actions = []

    for element in stack:
        for subelement in element:
            if subelement[0] == ":types":
                pddl_types = process_parameters(subelement[1:])
            if subelement[0] == ":constants":
                pddl_constants = process_parameters(subelement[1:])
            if subelement[0] == ":predicates":
                for predicate_part in subelement[1:]:
                    pddl_predicates[predicate_part[0]] = process_parameters(predicate_part[1:])
            if subelement[0] == ":action":
                action = None
                parameters_found = False
                precondition_found = False
                effect_found = False
                for action_part in subelement[1:]:
                    # process data sections found on previous step
                    if parameters_found:
                        action.parameters = process_parameters(action_part, True)
                        parameters_found = False
                    elif precondition_found:
                        action.precondition = action_part
                        precondition_found = False
                    elif effect_found:
                        action.effect = action_part
                        effect_found = False

                    # this is the name of the action
                    if action_part == subelement[1]:
                        action = Action(action_part)
                    # look for named sections of the action and defer processing to next cycle step
                    elif action_part == ":parameters":
                        parameters_found = True
                    elif action_part == ":precondition":
                        precondition_found = True
                    elif action_part == ":effect":
                        effect_found = True

                # register processed action
                if action is not None:
                    pddl_actions.append(action)

        print("PDDL Types: %s" % pddl_types)
        print("PDDL Constants: %s" % pddl_constants)
        print("PDDL Predicates: %s" % pddl_predicates)
        print("PDDL Actions: %s" % pddl_actions)

    return pddl_types, pddl_constants, pddl_predicates, pddl_actions


def parse_problem(fname):
    """
    Parses a PDDL problem file contained in the file fname
    
    The return value of this function is passed to planner.plan, and does not have to follow any particular format
    """
    stack = get_stack_from_pddl(fname)
    pddl_objects = {}
    pddl_init_exp = []
    pddl_goal_exp = []

    for element in stack:
        for subelement in element:
            if subelement[0] == ":objects":
                pddl_objects = process_parameters(subelement[1:])
            if subelement[0] == ":init":
                pddl_init_exp = subelement[1:]
            if subelement[0] == ":goal":
                pddl_goal_exp = subelement[1]

    print("PDDL Objects: %s" % pddl_objects)
    print("PDDL Init: %s" % pddl_init_exp)
    print("PDDL Goal: %s" % pddl_goal_exp)

    return pddl_objects, pddl_init_exp, pddl_goal_exp
    
    
if __name__ == "__main__":
    print(parse_domain(sys.argv[1]))
    print(parse_problem(sys.argv[2]))

