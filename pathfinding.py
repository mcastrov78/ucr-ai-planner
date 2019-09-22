import graph
import heapq

def default_heuristic(n, edge):
    """
    Default heuristic for A*. Do not change, rename or remove!
    """
    return 0


def print_open_nodes(list):
    print("ONODES: %s" % list)
    print("\t", end="")
    for element in list:
        print("%s" % element[1].name, end=" * ")
    print("")


def print_closed_nodes(list):
    print("CNODES: %s" % list)
    print("\t", end="")
    for element in list:
        print("%s" % element.name, end=" * ")
    print("")


def print_heapq(list):
    print("PQ: %s" % list)
    for i in range(len(list)):
        print(heapq.heappop(list), end=" * ")
    #print("\n")


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
    open_nodes = []
    closed_nodes = []

    heapq.heappush(open_nodes, (heuristic(start, None), start, 0, None))
    print_open_nodes(open_nodes)
    i = 0

    while len(open_nodes) > 0:
        current_node_info = heapq.heappop(open_nodes)
        current_node = current_node_info[1]
        closed_nodes.append(current_node)
        print("\nCURRENT NODE: %s" % current_node.name)
        print("accumulated cost: %s" % current_node_info[2])

        if goal(current_node):
            print("\n!!!!! REACHED GOAL !!!!!\n")
            node_parent = current_node_info[3]
            path = [current_node_info]
            while node_parent:
                path.append(node_parent)
                node_parent = node_parent[3]
            print("PATH: ", end="")
            for i in range(len(path)):
                print("%s" % path.pop()[1].get_id(), end=" - ")
            break

        for edge in current_node.get_neighbors():
            # f = accumulated cost + edge cost + h
            f = current_node_info[2] + edge.cost + heuristic(edge.target, edge)
            print("neighbor: %s -> gn:%s g:%s h:%s f:%s" % (edge.name, edge.cost, current_node_info[2] + edge.cost, heuristic(edge.target, edge), f))

            if edge.target not in closed_nodes:
                #if edge.target not in open_nodes:
                heapq.heappush(open_nodes, (f, edge.target, current_node_info[2] + edge.cost, current_node_info))
                #else:
                #    print("ELEMENT ALREADY IN OPEN LIST!!! %s" % edge.name)
            else:
                print("ELEMENT ALREADY IN CLOSED LIST!!! %s" % edge.name)


        print_open_nodes(open_nodes)
        print_closed_nodes(closed_nodes)
        #print_heapq(open_nodes)

        i = i + 1
        if i > 10:
            break

    return [],0,0,0

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
    g = graph.Austria
    print()
    print_path(result)
    '''
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
    '''

if __name__ == "__main__":
    main()