from pathfinding import astar, default_heuristic, print_path
import graph
import random
import traceback

class MyGraph(graph.Node):
    def __init__(self, id, nfun):
        self.id = id 
        self.nfun = nfun
    def get_id(self):
        return self.id
    def get_neighbors(self):
        return [graph.Edge(MyGraph(x, self.nfun), c, "%d - %d"%(self.id, x)) for (x,c) in self.nfun(self.id)]

passcnt = 0
totalcnt = 0

def runone(name, graph, h, goal, resn, reslen, resvis, resexp):
    global passcnt, totalcnt
    try:
        result = astar(graph, h, goal)
        (path,cost,visited_cnt,expanded_cnt) = result
        totalcnt += 1
        if (resn is None and path is None) or ((len(path) == resn) and abs(cost -reslen) < 0.01):
            print("PASS", name)
            passcnt += 1
        else:
            print("FAIL", name, "\n   has", len(path), "nodes, should be: ", resn, "has", cost, "cost, should be: ", reslen)
        print("   visited: %d (mine: %d), expanded: %d (mine: %d)"%(visited_cnt, resvis, expanded_cnt, resexp))
        #print_path(result)
    except Exception:
        print("FAIL", name, "\n   Threw an exception!")
        traceback.print_exc()
        

Blocksworld = graph.make_geom_graph(
    ["A B C", "AB C", "ABC", "AC B", "ACB", "BA C", "BAC", "BC A", "BCA", "CA B", "CAB", "CB A", "CBA"],
    [("A B C", "AB C", 1),
     ("A B C", "AC B", 1),
     ("A B C", "BC A", 1),
     ("A B C", "BA C", 1),
     ("A B C", "CA B", 1),
     ("A B C", "CB A", 1),
     ("ABC", "AB C", 1),
     ("ACB", "AC B", 1),
     ("BCA", "BC A", 1),
     ("BAC", "BA C", 1),
     ("CAB", "CA B", 1),
     ("CBA", "CB A", 1)])
     
BlocksworldG = graph.make_geom_graph(
    ["A B C", "AB C", "ABC", "AC B", "ACB", "BA C", "BAC", "BC A", "BCA", "CA B", "CAB", "CB A", "CBA",
     "A B (C)", "A C (B)", "B C (A)", "AB (C)", "AC (B)", "BC (A)", "BA (C)", "CA (B)", "CB (A)"],
    [("A B C", "A B (C)", 1),
     ("A B C", "A C (B)", 1),
     ("A B C", "B C (A)", 1),
     ("A B (C)", "AC B", 1),
     ("A B (C)", "BC A", 1),
     ("A C (B)", "AB C", 1),
     ("A C (B)", "CB A", 1),
     ("B C (A)", "BA C", 1),
     ("B C (A)", "CA B", 1),
     ("AC B", "AC (B)", 1),
     ("BC A", "BC (A)", 1),
     ("AB C", "AB (C)", 1),
     ("CB A", "CB (A)", 1),
     ("BA C", "BA (C)", 1),
     ("CA B", "CA (B)", 1),
     ("AC (B)", "ACB", 1),
     ("BC (A)", "BCA", 1),
     ("AB (C)", "ABC", 1),
     ("CB (A)", "CBA", 1),
     ("BA (C)", "BAC", 1),
     ("CA (B)", "CAB", 1)])
    

def main():

    target = "Bregenz"
    def atheuristic(n, edge):
        return graph.AustriaHeuristic[target][n.get_id()]
    def atgoal(n):
        return n.get_id() == target
    runone("Austria h", graph.Austria["Eisenstadt"], atheuristic, atgoal, 5, 692, 10, 6)

    runone("Austria d", graph.Austria["Eisenstadt"], default_heuristic, atgoal, 5, 692, 11, 10)
    target = 2050
    def infheuristic(n, edge):
        return abs(n.get_id() - target)
    def infgoal(n):
        return n.get_id() == target
        
    runone("InfGraph simple h", graph.InfNode(1), infheuristic, infgoal, 13, 13, 35,13)
    
    runone("InfGraph simple d", graph.InfNode(1), default_heuristic, infgoal, 12, 12, 1968, 1161)
    
    def multiheuristic(n, edge):
        return abs(n.get_id()%123 - 63)
    def multigoal(n):
        return n.get_id() > 1000 and n.get_id()%123 == 63
    
    runone("InfGraph multi h", graph.InfNode(1), multiheuristic, multigoal, 39, 39, 334, 155)
    
    runone("InfGraph multi d", graph.InfNode(1), default_heuristic, multigoal, 13, 13, 2485, 1466)
    
    def powers(n):
        return [(n-1,1), (n+1,1), (n*n,2), (n*n*n,3), (n**4,4)]
        
    def targeter(t):
        def istarget(n):
            return n.get_id() == t
        return istarget
        
    def targetheuristic(t):
        def heuristic(n, edge):
            return abs(n.get_id() - t)
        return heuristic
        
    runone("PowerGraph one h", MyGraph(1, powers), targetheuristic(123), targeter(123), 109, 112, 433, 109)
    
    runone("PowerGraph one d", MyGraph(1, powers), default_heuristic, targeter(123), 6, 9, 499, 140)
    
    random.seed(0)
    d0 = random.randint(1,10)
    d1 = random.randint(2,10)
    d2 = random.randint(11,20)
    def rdist(n):
        return [(n-1,3), (n+d0,1), (n*d1,1), (n+d2,1)]
        
    runone("RandomGraph(%d, %d, %d) h"%(d0,d1,d2), MyGraph(1, rdist), targetheuristic(543), targeter(543), 43, 43, 787, 339)
    
    runone("RandomGraph(%d, %d, %d) d"%(d0,d1,d2), MyGraph(1, rdist), default_heuristic, targeter(543), 6, 8, 3737, 1176)
    
    runone("RandomGraph(%d, %d, %d) h"%(d0,d1,d2), MyGraph(1, rdist), targetheuristic(6543), targeter(6543), 41, 41, 170, 43)
    
    deltas = list(range(-100, 500))
    random.shuffle(deltas)
    
    def rneigh(n):
        return [(n+d,i+1) for (i,d) in enumerate(deltas[:250])] + [(n-1,5)]
    
    runone("WideGraph h", MyGraph(1, rneigh), targetheuristic(9999), targeter(9999), 23, 149, 5580, 24)
    
    runone("Blocksworld h", Blocksworld["A B C"], default_heuristic, targeter("CAB"), 2, 2, 12, 11)
    
    runone("Sussman h", Blocksworld["AC B"], default_heuristic, targeter("CBA"), 3, 3, 12, 12)
    
    runone("BlocksworldG h", BlocksworldG["A B C"], default_heuristic, targeter("CAB"), 4, 4, 18, 18)
    
    runone("SussmanG h", BlocksworldG["AC B"], default_heuristic, targeter("CBA"), 6, 6, 21, 19)
    
    runone("ImpossibleBlocks h", BlocksworldG["AC B"], default_heuristic, targeter("CBAD"), None, None, 21, 21)
    
    
    
if __name__ == "__main__":
    main()