import sys
import os 
import planner
import pddl
import time
import multiprocessing

MAXTIME = 600

def runplanner(domain, problem,useheuristic, cost, visited, expanded):
    (_,cost.value,visited.value,expanded.value) = planner.plan(pddl.parse_domain(domain), pddl.parse_problem(problem), useheuristic)
    
class TestResult:
    def __init__(self, solved, cost=-1, visited=-1, expanded=-1, duration=MAXTIME):
        self.solved = solved
        self.cost = cost 
        self.visited = visited 
        self.expanded = expanded 
        self.duration = duration
        
def runone(domain, problem, useheuristic):
    t0 = time.time()
    
    cost = multiprocessing.Value('d', 0)
    visited = multiprocessing.Value('d', 0)
    expanded = multiprocessing.Value('d', 0)
    p = multiprocessing.Process(target=runplanner, args=(domain, problem, useheuristic, cost, visited, expanded))
    p.start()
    p.join(MAXTIME)
    if not p.is_alive():
        duration = time.time() - t0
        return TestResult(True, cost.value, visited.value, expanded.value, duration)
    p.terminate()
    return TestResult(False)
    
    
    
def runtest(domain, problem):
    result = {}
    result[(problem,True)] = runone(domain, problem, True)
    result[(problem,False)] = runone(domain, problem, False)
    return result   

def process(dirname):
    contents = os.listdir(dirname)
    domain = None
    if "domain.pddl" in contents:
        domain = os.path.join(dirname, "domain.pddl")
    for c in contents:
        fullname = os.path.join(dirname, c)
        if os.path.isdir(fullname):
            process(fullname)
        else:
            if "domain" not in c and fullname.endswith(".pddl"):
                result = {}
                if domain:
                    result = runtest(domain, fullname)
                else:
                    if c.startswith("p") and len(c) > 2:
                        problem = c[:3]
                        for other in contents:
                            if other.startswith(problem) and "domain" in other:
                                result = runtest(os.path.join(dirname, other), fullname)
                                break
                if result:
                    for r in result:
                        (name, heuristic) = r 
                        h = "d"
                        if heuristic:
                            h = "h"
                        if result[r].solved:
                            print("%50s %s: expanded %8d, visited %8d, needed %6.2f seconds"%(name, h, result[r].expanded, result[r].visited, result[r].duration))
                        else:
                            print("%50s %s: timeout"%(name, h))


if __name__ == "__main__":
    process(sys.argv[1])