import time
import pddl
import graph
import expressions
import pathfinding
import sys
import copy
import logging
import logging.config

# initialize logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class ExpandedExpression:
    """ This class is to hold expanded expressions for the actions, the action names and the grounded parameters """
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression
        self.parameters = []

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def get_expanded_exp_name(self):
        return self.name + "(" + ", ".join(self.parameters) + ")"

    def __str__(self):
        return self.get_expanded_exp_name() + " - EXP: " + str(self.expression)


def merge_dictionaries(dict1, dict2):
    """ Merge dictionaries and keep values of common keys in list """
    dict3 = {**dict1, **dict2}
    for key, value in dict3.items():
        if key in dict1 and key in dict2:
            dict3[key] = [value, dict1[key]]
    return dict3


def get_all_child_objects(subtypes, world_sets, types):
    """ Get all child objects for these subtypes and their child subtypes recursively """
    child_objects = []
    for subtype in subtypes:
        if subtype in world_sets:
            # reached a leaf subtype with child objects
            child_objects.extend(world_sets[subtype])
        else:
            # reached a non-leaf subtype, get all child subtypes and their objects recursively
            child_objects.extend(get_all_child_objects(types[subtype], world_sets, types))
    return child_objects


def complete_hierarchy(world_sets, types):
    """ Complete World Sets hierarchy with all child objects for types and their subtypes """
    for type, subtypes in types.items():
        # don't do this for the "" types set, its items are not supertypes
        if len(type) > 0:
            # get all child objects for this type and its subtypes recursively
            all_child_objects = get_all_child_objects(subtypes, world_sets, types)
            logger.debug("Type: %s - Subtype: %s - Children: %s" % (type, subtypes, all_child_objects))
            # if type is already defined in world sets, add new objects found, otherwise expand existing list
            if type in world_sets:
                world_sets[type].extend(all_child_objects)
            else:
                world_sets[type] = all_child_objects
    return world_sets


def build_world_sets(constants, objects, types):
    """ Build the sets variable required to make an initial world """
    # merge domain constants and problem objects dictionaries
    world_sets = merge_dictionaries(constants, objects)
    logger.debug("Initial WORLD SETS: %s" % world_sets)
    # complete constants and objects lists based on types hierarchy
    world_sets = complete_hierarchy(world_sets, types)

    # create and add the "all objects" set with key "" to World Sets
    all_objects = []
    for value_list in world_sets.values():
        for value in value_list:
            if value not in all_objects:
                all_objects.append(value)
    world_sets[""] = all_objects

    logger.debug("Final WORLD SETS: %s" % world_sets)
    return world_sets


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
    '''
    domain[0] = pddl_types, domain[1] = pddl_constants, domain[2] = pddl_predicates, domain[3] = pddl_actions
    problem[0] = pddl_objects, problem[1] = pddl_init_exp, problem[2] = pddl_goal_exp
    '''
    def heuristic(state, action):
        """Calculates a heuristic following some basic principles of Fast-Forward algorithm"""
        # initial state is a neighbor of a previous state that A* needs to evaluate
        props_layer = state
        # relaxed plan has layers, each with and action layer and a propositions layer
        relaxed_plan_graph = [[[], props_layer]]

        # extend one action layer and proposition layer at a time while goal is not reached
        while not isgoal(props_layer):
            # next action layer: get "relaxed" neighbors whose Add Lists have a real effect and ignoring Delete Lists
            actions_layer = props_layer.get_neighbors(True)
            # next props layer: start with propositions in current layer and add new ones generated by each new action
            next_props_layer = copy.deepcopy(props_layer.world.atoms)
            for next_action in actions_layer:
                next_props_layer = next_props_layer.union(next_action.target.world.atoms)

            # stop if next propositions layer did not add any new propositions, otherwise continue in the loop
            if props_layer.world.atoms.issuperset(next_props_layer):
                break

            # new propositional layer
            new_world = expressions.World(next_props_layer, props_layer.world.sets)
            props_layer = graph.ExpressionNode(new_world, props_layer.actions, props_layer.preceding_action)
            # add new actions and props layer to relaxed plan
            relaxed_plan_graph.append([actions_layer, props_layer])
        
        # extract relaxed plan size and return it as the heuristic value
        return extract_plan_size(relaxed_plan_graph)

    def extract_plan_size(rpg):
        """Extract relaxed plan size based on the number of actions required to complete it"""
        goal = expressions.make_expression(problem[2])
        final_state = rpg[len(rpg) - 1][1]

        # if the world in final proposition layer does not contain the goal, return magic large number as h ...
        if not isgoal(final_state):
            return 1000

        # find the layer where each sub-goal appears for the first time on the relaxed planning graph
        first_goal_levels = get_first_goal_levels(rpg, goal, {})
        # obtain maximum level number where a goal was found
        first_goal_levels_max = max(first_goal_levels.keys())

        # backtrack starting on the last proposition layer we need to consider
        for i in range(first_goal_levels_max, 0, -1):
            logger.debug("BACKTRACKING i: %s" % i)
            # if there is at least one sub-goal on level i
            if i in first_goal_levels:
                first_goal_levels = get_first_action_levels(rpg, first_goal_levels, i)

        h = 0
        for layer, actions in first_goal_levels.items():
            h += len(actions)

        return h

    def get_first_goal_levels(rpg, goal, first_goal_levels):
        """Find the layer where each sub-goal appears for the first time on the relaxed planning graph"""
        # handle special case when the goal is not a conjunction of atoms, but one atom
        if isinstance(goal, expressions.Atom):
            goal = expressions.And([goal])

        # for each sub-goal in goal
        for sub_goal in goal.operands:
            level = 0
            # for each layer in relaxed planning graph
            for layer in rpg:
                # if the world in this propositional layer models this sub-goal, add sub-goal to that level
                if layer[1].world.models(sub_goal):
                    if level in first_goal_levels:
                        first_goal_levels[level] = first_goal_levels[level].union({sub_goal})
                    else:
                        first_goal_levels[level] = {sub_goal}
                    # break to guarantee we always only use only the first appearance
                    break
                level += 1

        logger.debug("\tGoal Levels: %s" % first_goal_levels)
        return first_goal_levels

    def get_first_action_levels(rpg, first_goal_levels, layer):
        """Find the layer where each action whose effect is a sub-goal appears for the first time on the relaxed
        planning graph. Then consider its preconditions as new sub-goals and add them to preceding layers of
        first_goal_levels that will eventually be reached by the backtracking process to also process their
        preconditions"""
        for sub_goal in first_goal_levels[layer]:
            level = 0
            # for each layer in the relaxed planning graph
            for layer_index in range(len(rpg)):
                # for each action on this layer of the relaxed planning graph
                for action in rpg[layer_index][0]:
                    # determine if this action introduces sub_goal for the first time
                    previous_props_layer = rpg[layer_index - 1][1]
                    next_props_layer = action.target
                    if next_props_layer.world.models(sub_goal) and not previous_props_layer.world.models(sub_goal):
                        # each precondition must now be considered a sub-goal
                        preconditions = action.target.preceding_action.expression.operands[0]
                        logger.debug("\tACTION: %s" % action.name)
                        logger.debug("\tPRECONS: %s" % preconditions)
                        # find the layer where each sub-goal appears for the first time on the relaxed planning graph
                        first_goal_levels = get_first_goal_levels(rpg, preconditions, first_goal_levels)
                        # break to guarantee we always only use only the first appearance
                        break
                level += 1
        return first_goal_levels
        
    def isgoal(state):
        """Check is goal is reached"""
        goal = expressions.make_expression(problem[2])
        return state.world.models(goal)

    # get the sets variable required to make a n initial world
    world_sets = build_world_sets(domain[1], problem[0], domain[0])

    # get all expanded expressions for all actions
    expanded_expressions = []

    # for each action in the domain
    for action in domain[3]:
        substitutions_per_action = []
        # for each group of params of the same type for this action
        for parameter_type in action.parameters:
            logger.debug("Action: %s - Param Type: %s - Params: %s" % (action.name, parameter_type, action.parameters[parameter_type]))
            # for each param in each group of params of the same type for this action
            for parameter in action.parameters[parameter_type]:
                substitutions_per_param = []
                # for each ground param as taken from world_sets based on type
                for ground_param in world_sets[parameter_type]:
                    logger.debug("\tParam: %s, Ground Param: %s" % (parameter, ground_param))
                    substitutions_per_param.append([parameter, ground_param])
                substitutions_per_action.append(substitutions_per_param)
        # expand the action with all possible substitutions
        expanded_expressions.extend(expand_action(action, substitutions_per_action))

    # create the initial world with pddl_init_exp and world_sets and the start node for astar
    world = expressions.make_world(problem[1], world_sets)
    start = graph.ExpressionNode(world, expanded_expressions, None)

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