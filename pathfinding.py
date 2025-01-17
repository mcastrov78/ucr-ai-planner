import graph
import heapq
import logging
import logging.config
import math

# initialize logger
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


def default_heuristic(n, edge):
    """
    Default heuristic for A*. Do not change, rename or remove!
    """
    return 0


def get_node_index_in_open_list(open_list, node):
    # check if this node is already in the open list and return its index
    for i in range(len(open_list)):
        if open_list[i][2].get_id() == node.get_id():
            return i
    return -1


def get_edge_path(goal_node_info):
    edge_path = []
    node_info = goal_node_info
    while node_info:
        if node_info[5]:
            edge_path.append(node_info[5])
        node_info = node_info[4]
    edge_path.reverse()
    return edge_path


def astar(start, heuristic, goal):
    """
    A* search algorithm. The function is passed a start graph.Node object, a heuristic function, and a goal predicate.
    
    The start node can produce neighbors as needed, see graph.py for details.
    
    The heuristic is a function that takes two parameters: a node, and an edge. The algorithm uses this heuristic to determine which node to expand next.
    Note that, unlike in classical A*, the heuristic can also use the edge used to get to a node to determine the node's heuristic value. This can be beneficial when the 
    edges represent complex actions (as in the planning case), and we want to take into account the differences produced by that action.
    
    The goal is also represented a function, that is passed a node, and returns True if that node is a goal node, otherwise False. This representation was also chosen to
    simplify implementing the planner later, which can use the functions developed in task 1 to determine if a state models the goal condition, 
    but is otherwise equivalent to classical A*. 
    
    The function should return a 4-tuple (path,distance,visited,expanded):
        - path is a sequence of graph.Edge objects that have to be traversed to reach a goal state from the start.
        - distance is the sum of costs of all edges in the path 
        - visited is the total number of nodes that were added to the frontier during the execution of the algorithm 
        - expanded is the total number of nodes that were expanded (i.e. whose neighbors were added to the frontier)
    """
    edge_path = None
    distance = None
    open_list = []
    closed_list = []
    i = 0

    '''
    tuple structure that represents a "node info" (in all this code we assume f(n) = g(n) + h(n))
        0 - f: accumulated cost plus heuristic value
        1 - i: just a counter value to break ties in heapq when two or more items have the same f value (i.e. priority)
        2 - node: current node
        3 - g: accumulated cost
        4 - parent node info: this same tuple structure for current node's parent 
        5 - edge: edge that led to current node
    '''
    # push start node to the priority queue
    heapq.heappush(open_list, (0, i, start, 0, None, None))

    # while there are nodes to expand
    while len(open_list) > 0:
        # get next node to expand from the priority queue, and push it to closed list
        current_node_info = heapq.heappop(open_list)
        current_node = current_node_info[2]
        closed_list.append(current_node)
        logger.debug("*** CURRENT NODE: %s" % current_node.get_id())
        logger.info("*** PRECEDING ACTION: %s" % (current_node_info[5].name if current_node_info[5] else "-"))
        logger.debug("accumulated cost: %s" % current_node_info[3])

        # check if current node is the goal AND that it was the lowest value in the queue
        if goal(current_node) and current_node in closed_list:
            logger.debug("---------------------- !!!!! REACHED GOAL !!!!! ----------------------")
            # rebuild path based on each node's parent node info
            distance = current_node_info[3]
            edge_path = get_edge_path(current_node_info)
            break

        # expand current node and get neighbors
        for edge in current_node.get_neighbors():
            # inc counter value to break ties in heapq when two or more items have the same f value
            i = i + 1

            # f = accumulated cost + edge cost + h
            accumulated_cost = current_node_info[3] + edge.cost
            h = heuristic(edge.target, edge)
            f = accumulated_cost + h
            logger.info("\t/neighbor: %s -> gn:%s g:%s h:%s f:%s i:%s" % (edge.name, edge.cost, current_node_info[3] + edge.cost, h, f, i))

            # check if neighbor is NOT in closed list
            if edge.target not in closed_list:
                # check if neighbor is already in open list
                node_index_in_open_list = get_node_index_in_open_list(open_list, edge.target)
                if node_index_in_open_list == -1:
                    # node is not in open list yet, push it through the priority queue
                    heapq.heappush(open_list, (f, i, edge.target, accumulated_cost, current_node_info, edge))
                else:
                    # check if new node path has a better cost than previous node entry in open list, if so, replace it
                    if open_list[node_index_in_open_list][0] > f:
                        logger.debug("\tBETTER cost for %s: %s > %s" % (open_list[node_index_in_open_list][2].get_id(),
                                                                         open_list[node_index_in_open_list][0], f))
                        del open_list[node_index_in_open_list]
                        heapq.heappush(open_list, (f, i, edge.target, accumulated_cost, current_node_info, edge))
                    else:
                        logger.debug("\tNO better cost for %s: %s < %s" % (
                        open_list[node_index_in_open_list][2].get_id(), open_list[node_index_in_open_list][0], f))
            else:
                logger.debug("\tALREADY in CLOSED list!!! %s" % edge.name)

        logger.debug("OPEN: %s" % " | ".join(
            "[%s %s %s]" % (element[0], element[2].get_id(), element[3]) for element in open_list))
        logger.debug("CLOSED: %s" % " | ".join("%s" % element.get_id() for element in closed_list))

    return edge_path, distance, len(open_list) + len(closed_list), len(closed_list)


def print_path(result):
    (path,cost,visited_cnt,expanded_cnt) = result
    print("visited nodes:", visited_cnt, "expanded nodes:",expanded_cnt)
    if path:
        print("Path found with cost", cost)
        for n in path:
            print(n.name)
    else:
        print("No path found")
    print("\n")

def main():
    """
    You are free (and encouraged) to change this function to add more test cases.
    
    You are provided with three test cases:
        - pathfinding in Austria, using the map shown in class. This is a relatively small graph, but it comes with an admissible heuristic. Below astar is called using that heuristic, 
          as well as with the default heuristic (which always returns 0). If you implement A* correctly, you should see a small difference in the number of visited/expanded nodes between the two heuristics.
        - pathfinding on an infinite graph, where each node corresponds to a natural number, which is connected to its predecessor, successor and twice its value, as well as half its value, if the number is even.
          e.g. 16 is connected to 15, 17, 32, and 8. The problem given is to find a path from 1 to 2050, for example by doubling the number until 2048 is reached and then adding 1 twice. There is also a heuristic 
          provided for this problem, but it is not admissible (think about why), but it should result in a path being found almost instantaneously. On the other hand, if the default heuristic is used, the search process 
          will take a noticeable amount (a couple of seconds).
        - pathfinding on the same infinite graph, but with infinitely many goal nodes. Each node corresponding to a number greater 1000 that is congruent to 63 mod 123 is a valid goal node. As before, a non-admissible
          heuristic is provided, which greatly accelerates the search process. 
    """
    target = "Bregenz"
    def atheuristic(n, edge):
        return graph.AustriaHeuristic[target][n.get_id()]
    def atgoal(n):
        return n.get_id() == target

    result = astar(graph.Austria["Eisenstadt"], atheuristic, atgoal)
    print_path(result)

    result = astar(graph.Austria["Eisenstadt"], default_heuristic, atgoal)
    print_path(result)

    target = 2050
    def infheuristic(n, edge):
        return abs(n.get_id() - target)
    def infgoal(n):
        return n.get_id() == target

    result = astar(graph.InfNode(1), infheuristic, infgoal)
    print_path(result)

    result = astar(graph.InfNode(1), default_heuristic, infgoal)
    print_path(result)

    def multiheuristic(n, edge):
        return abs(n.get_id()%123 - 63)
    def multigoal(n):
        return n.get_id() > 1000 and n.get_id()%123 == 63
    
    result = astar(graph.InfNode(1), infheuristic, multigoal)
    print_path(result)

    result = astar(graph.InfNode(1), default_heuristic, multigoal)
    print_path(result)

    result = astar(graph.InfNode(1), multiheuristic, multigoal)
    print_path(result)
    
    # more tests ...
    def power_of_2_heuristic(n, edge):
        log2n = 0
        if n.get_id() > 0:
            log2n = math.log2(n.get_id())
        return abs(math.floor(log2n) - math.floor(math.log2(1024)))

    def power_of_2_goal(n):
        sqr = math.sqrt(n.get_id())
        return (math.floor(sqr) == sqr) and n.get_id() > 1000

    result = astar(graph.InfNode(1), power_of_2_heuristic, power_of_2_goal)
    print_path(result)

    target = "Eisenstadt"
    result = astar(graph.Austria["Eisenstadt"], atheuristic, atgoal)
    print_path(result)


if __name__ == "__main__":
    main()