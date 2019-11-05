import time
import pddl
import graph
import expressions
import pathfinding
import sys 


def merge_dictionaries(dict1, dict2):
    ''' Merge dictionaries and keep values of common keys in list'''
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and key in dict2:
            dict3[key] = [value, dict1[key]]
    return dict3


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
        return True

    '''
    domain[0] = pddl_types, domain[1] = pddl_constants, domain[2] = pddl_predicates, domain[3] = pddl_actions
    problem[0] = pddl_objects, problem[1] = pddl_init_exp, problem[2] = pddl_goal_exp
    '''
    world_sets = merge_dictionaries(domain[1], problem[0])
    all_objects = []
    print()
    #print("WORLD SETS: %s" % world_sets)
    for value in world_sets.values():
        all_objects.extend(value)
    world_sets[""] = all_objects
    #print("all_objects: %s" % all_objects)
    print("WORLD SETS: %s" % world_sets)

    world = expressions.World(problem[1], world_sets)

    # for each action in the domain
    for action in domain[3]:
        action_expresions = []

        # for each group of params of the same type for this action
        for parameter_type in action.parameters:
            print("Action: %s - Param Type: %s - Params: %s" % (action.name, parameter_type, action.parameters[parameter_type]))

            when_expression_list = ["when", action.precondition, action.effect]
            when_expression = expressions.make_expression(when_expression_list)
            print("when_expression: %s" % when_expression)

            # for each param in each group
            for i in range(len(action.parameters[parameter_type])):
                # for each ground param in each group
                for ground_param in world_sets[parameter_type]:
                    print("\tParam Type: %s, Ground Param: %s" % (action.parameters[parameter_type][i], ground_param))
                    when_expression = when_expression.substitute(action.parameters[parameter_type][i], ground_param)

            action_expresions.append(when_expression)

    print("action_expresions: %s" % action_expresions)
    start = graph.Node()
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