import time
import pddl
import graph
import expressions
import pathfinding
import sys 


class ExpandedExpression:
    """ This class is to hold expanded expressions for the actions, the action names and the grounded paramters """
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        self.parameters = []

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def get_expanded_exp_name(self):
        return self.name + "(" + ", ".join(self.parameters) + ")"

    def __str__(self):
        return self.get_expanded_exp_name() + " - EXP: " + self.expression.__str__()


def merge_dictionaries(dict1, dict2):
    """ Merge dictionaries and keep values of common keys in list """
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and key in dict2:
            dict3[key] = [value, dict1[key]]
    return dict3


def expand_expressions(substitution_per_action, expressions_to_expand):
    """ Expands each action as many times as parameters expand_action() has to process """
    expanded_expressions = []
    # for each param in action

    for substitution_per_param in substitution_per_action:
        for expanded_expression in expressions_to_expand:
            param_name = substitution_per_param[0][0]
            param_order = substitution_per_param[0][1]
            value = substitution_per_param[1]

            # create a new WHEN expression with the substitutions
            new_when_expression = expanded_expression.expression.substitute(param_name, value)
            # create new ExpandedExpression for the new WHEN expression
            new_expanded_expression = ExpandedExpression(expanded_expression.name, new_when_expression)
            # add existing processed parameters and the new being processed on this round of substitutions
            new_expanded_expression.parameters.extend(expanded_expression.parameters)
            new_expanded_expression.parameters.insert(param_order, value)
            expanded_expressions.append(new_expanded_expression)
    return expanded_expressions


def expand_action(action, substitutions_per_action):
    """ Expands each action as many times as parameters it has to process for it """
    expressions_to_expand = []

    # create and initial WHEN expression to expand and wrap it in ExpandedExpression
    when_expression_list = ["when", action.precondition, action.effect]
    when_expression = expressions.make_expression(when_expression_list)
    expanded_expression = ExpandedExpression(action.name, when_expression)
    expressions_to_expand.append(expanded_expression)

    # expand each expression in expressions_to_expand as many times as parameters we have for the action
    for substitution_per_action in substitutions_per_action:
        expressions_to_expand = expand_expressions(substitution_per_action, expressions_to_expand)

    return expressions_to_expand


def plan(domain, problem, useheuristic=True):
    """
    Find a solution to a planning problem in the given domain 
    
    The parameters domain and problem are exactly what is returned from pddl.parse_domain and pddl.parse_problem. If useheuristic is true,
    a planning heuristic (developed in task 4) should be used, otherwise use pathfinding.default_heuristic. This allows you to compare 
    the effect of your heuristic vs. the default one easily.
    
    The return value of this function should be a 4-tuple, with the exact same elements as returned by pathfinding.astar:
       - A plan, which is a sequence of graph.Edge objects that have to be traversed to reach a goal state from the start. Each Edge object represents an action, 
         and the edge's name should be the name of the action, consisting of the name of the operator the action was derived from, followed by the parenthesized 
         and comma-separated parameter values e.g. "move(agent-1,sq-1-1,sq-2-1)"
       - distance is the number of actions in the plan (i.e. each action has cost 1)
       - visited is the total number of nodes that were added to the frontier during the execution of the algorithm 
       - expanded is the total number of nodes that were expanded (i.e. whose neighbors were added to the frontier)
    """
    def heuristic(state, action):
        return pathfinding.default_heuristic
        
    def isgoal(state):
        goal = expressions.make_expression(problem[2])
        return state.world.models(goal)

    '''
    domain[0] = pddl_types, domain[1] = pddl_constants, domain[2] = pddl_predicates, domain[3] = pddl_actions
    problem[0] = pddl_objects, problem[1] = pddl_init_exp, problem[2] = pddl_goal_exp
    '''
    # merge domain constants and problem objects
    world_sets = merge_dictionaries(domain[1], problem[0])

    # add the "all objects" set with key "" to world_sets
    all_objects = []
    for value in world_sets.values():
        all_objects.extend(value)
    world_sets[""] = all_objects
    print("WORLD SETS: %s" % world_sets)

    # get all expanded expressions for all actions
    expanded_expressions = []

    # for each action in the domain
    for action in domain[3]:
        substitutions_per_action = []
        # for each group of params of the same type for this action
        for parameter_type in action.parameters:
            #print("Action: %s - Param Type: %s - Params: %s" % (action.name, parameter_type, action.parameters[parameter_type]))
            # for each param in each group of params of the same type for this action
            for parameter in action.parameters[parameter_type]:
                substitutions_per_param = []
                # for each ground param as taken from world_sets based on type
                for ground_param in world_sets[parameter_type]:
                    #print("\tParam: %s, Ground Param: %s" % (parameter, ground_param))
                    substitutions_per_param.append([parameter, ground_param])
                substitutions_per_action.append(substitutions_per_param)

        # expand the action with all possible substitutions
        print("substitutions_per_action: %s" % substitutions_per_action)
        expanded_expressions.extend(expand_action(action, substitutions_per_action))

    #print()
    #for expression in expanded_expressions:
    #    print("EXP: %s" % expression)

    # create the initial world with pddl_init_exp and world_sets and the start node for astar
    world = expressions.make_world(problem[1], world_sets)
    start = graph.ExpressionNode(world, expanded_expressions)

    return pathfinding.astar(start, heuristic if useheuristic else pathfinding.default_heuristic, isgoal)


def main(domain, problem, useheuristic):
    t0 = time.time()
    (path,cost,visited_cnt,expanded_cnt) = plan(pddl.parse_domain(domain), pddl.parse_problem(problem), useheuristic)
    print("visited nodes:", visited_cnt, "expanded nodes:",expanded_cnt)
    if path is not None:
        print("Plan found with cost", cost)
        for n in path:
            print(n.name)
    else:
        print("No plan found")
    print("needed %.2f seconds"%(time.time() - t0))
    

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "-d" not in sys.argv)