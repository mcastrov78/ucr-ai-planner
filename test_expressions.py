from expressions import make_world, make_expression, models, apply, substitute
import traceback

run = 0
passed = 0

def run_test_simple(world_spec, expression_spec, result, sets={}):
    global run, passed 
    run += 1
    try:
        world = make_world(world_spec, sets)
        exp = make_expression(expression_spec)
        res = models(world, exp)
        if res == result:
            passed += 1
            return True
    except Exception:
        traceback.print_exc()
    return False
        
def run_test_apply(world_spec, action_spec, expression_spec, result, sets={}):
    global run, passed 
    run += 1
    try:
        world = make_world(world_spec, sets)
        action = make_expression(action_spec)
        world1 = apply(world, action)
        exp = make_expression(expression_spec)
        res = models(world1, exp)
        if res == result:
            passed += 1
            return True
    except Exception:
        traceback.print_exc()
       
    return False
        
def run_test_substitute(world_spec, expression_spec, subst, result, sets={}):
    global run, passed 
    run += 1
    try:
        
        world = make_world(world_spec, sets)
        action = make_expression(action_spec)
        world1 = apply(world, action)
        exp = make_expression(expression_spec)
        res = models(world1, exp)
        if res == result:
            passed += 1
            return True
    except Exception:
        traceback.print_exc()
    return False
        
def run_test_plan(world_spec, plan, expression_spec, result, sets={}):
    global run, passed 
    run += 1
    try:
        world = make_world(world_spec, sets)
        i = 1
        for p in plan:
            run += 1
            (pre,eff,subst) = p
            
            
            preexp = make_expression(pre)
            effexp = make_expression(eff)
            
            for s in subst:
                (var,val) = s 
                preexp = substitute(preexp, var, val)
                effexp = substitute(effexp, var, val)
            if not models(world, preexp):
                print("precondition failed at step", i)
                return False
            world = apply(world, effexp)
            passed += 1
            i += 1
        exp = make_expression(expression_spec)
        res = models(world, exp)
        if res == result:
            passed += 1
            return True
    except Exception:
        traceback.print_exc()
    return False
        

def sub(ast, subst):
    item = ast[0]
    if item in ["and", "or", "imply", "when", "not"]:
        result = [item]
        for i in ast[1:]:
            result.append(sub(i, subst))
        return tuple(result)
    elif item in ["exists", "forall"]:
        result = [item, ast[1]]
        for i in ast[2:]:
            result.append(sub(i, subst))
        return tuple(result)
    result = [item]
    for i in ast[1:]:
        newval = i
        for s in subst:
            (var,val) = s
            if i == var:
                newval = val
        result.append(newval)

    return tuple(result)
        
        
def run_test_planp(world_spec, plan, expression_spec, result, sets={}):
    global run, passed 
    run += 1
    try:
        world = make_world(world_spec, sets)
        i = 1
        for p in plan:
            run += 1
            (pre,eff,subst) = p
            
            preexp = make_expression(sub(pre, subst))
            effexp = make_expression(sub(eff, subst))
            
            if not models(world, preexp):
                print("precondition failed at step", i, preexp)
                return False
            world = apply(world, effexp)
            passed += 1
            i += 1
        exp = make_expression(expression_spec)
        res = models(world, exp)
        if res == result:
            passed += 1
            return True
    except Exception:
        traceback.print_exc()
    return False

results = {}

facts = [("on", "a", "b"), ("on", "b", "c"), ("on", "c", "d")]
exp = ("or", ("on", "a", "b"), ("on", "a", "d"))
results["simple_or"] = run_test_simple(facts, exp, True)

exp = ["and", ("not", ("on", "a", "b")), ("on", "a", "c")]

results["simple_and"] = run_test_simple(facts, exp, False)

results["simple_not"] = run_test_simple(facts, ("not", ("on", "a", "b")), False)

results["simple_imply"] = run_test_simple(facts, ("imply", ("on", "a", "b"), ("on", "b", "a")), False)

results["simple_exists"] = run_test_simple(facts, ("exists", ("?v", "-", ""), ("on", "a", "?v")), True, sets={"": ["a", "b", "c"]})

results["simple_forall"] = run_test_simple(facts, ("forall", ("?v", "-", "restricted"), ("on", "?v", "b")), True, sets={"": ["a", "b", "c"], "restricted": ["a"]})


facts = [("at", "store", "mickey"), ("at", "airport", "minny")]
sets = {"Locations": ["home", "park", "store", "airport", "theater"], "": ["home", "park", "store", "airport", "theater", "mickey", "minny"]}
exp = ("and", 
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
                                ("at", "?l", "minny")))))
                                
results["mickey_basic"] = run_test_simple(facts, exp, True, sets)

action = ("friends", "mickey", "minny")
results["mickey_not_friends"] = run_test_apply(facts, action, exp, False, sets)

facts = [("at", "store", "mickey"), ("at", "airport", "minny"), ("friends", "mickey", "minny")]
action = ("and", ("at", "store", "minny"), ("not", ("at", "airport", "minny")))
results["mickey_move_friends"] = run_test_apply(facts, action, exp, True, sets)

facts = [("at", "store", "mickey"), ("at", "store", "minny"), ("friends", "mickey", "minny")]
action = ("and", 
                                       ("at", "home", "mickey"), 
                                       ("not", ("at", "store", "mickey")), 
                                       ("when", 
                                             ("at", "store", "minny"), 
                                             ("and", 
                                                  ("at", "home", "minny"), 
                                                  ("not", ("at", "store", "minny")))))
results["mickey_collocated"] = run_test_apply(facts, action, exp, True, sets)

facts = [("at", "store", "mickey"), ("at", "airport", "minny"), ("friends", "mickey", "minny")]
results["mickey_not_collocated"] = run_test_apply(facts, action, exp, False, sets)

facts = [("above", "f0", "f1"), ("above",  "f0", "f2"), ("above",  "f0", "f3"), ("above",  "f1", "f2"), ("above",  "f1", "f3"), 
         ("above", "f2", "f3"), ("origin", "p0", "f3"), ("destin", "p0", "f2"), ("origin", "p1", "f1"), ("destin", "p1", "f3"), ("lift-at", "f0")]
         
pboard = ("and", ("lift-at", "?f"), ("origin", "?p", "?f"))
eboard = ("boarded", "?p")

pserve = ("and", ("lift-at", "?f"), ("destin", "?p", "?f"), ("boarded", "?p"))
eserve = ("and", ("not", ("boarded", "?p")), ("served", "?p"))


pup = ("and", ("lift-at", "?f1"), ("above", "?f1", "?f2"))
eup = ("and", ("lift-at", "?f2"), ("not", ("lift-at", "?f1")))


pdown = ("and", ("lift-at", "?f1"), ("above", "?f2", "?f1"))
edown = ("and", ("lift-at", "?f2"), ("not", ("lift-at", "?f1")))

# Preprocessed
goal = ("served", "p0")

results["elevator_strips_1"] = run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True)


goal = ("and", ("served", "p0"), ("served", "p1"))

results["elevator_strips_2"] = run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True)
                      
goal = ("forall", ("?p", "-", "passenger"), ("served", "?p"))

results["elevator_strips_forall"] = run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})
                      
goal = ("not", ("exists", ("?p", "-", "passenger"), ("not", ("served", "?p"))))

results["elevator_strips_exists"] = run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})
                      
pstop = ("lift-at", "?f")
estop = ("and",
               ("forall", ("?p", "-", "passenger"), 
                  ("when", ("and", ("boarded", "?p"),
                             ("destin", "?p", "?f")),
                        ("and", ("not", ("boarded", "?p")),
                             ("served", "?p")))),
               ("forall", ("?p", "-", "passenger"), 
                   ("when", ("and", ("origin", "?p", "?f"), ("not", ("served", "?p"))),
                              ("boarded", "?p"))))

goal = ("forall", ("?p", "-", "passenger"), ("served", "?p"))
results["elevator_adl_1"] = run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pstop,estop,[("?f", "f1")])], ("boarded", "p1"), True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})

results["elevator_adl_2"] =  run_test_planp(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pstop,estop,[("?f", "f1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pstop,estop,[("?f", "f3")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pstop,estop,[("?f", "f2")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})

# Using substitute

goal = ("served", "p0")

results["elevator_strips_1_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True)


goal = ("and", ("served", "p0"), ("served", "p1"))

results["elevator_strips_2_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True)
                      
goal = ("forall", ("?p", "-", "passenger"), ("served", "?p"))

results["elevator_strips_forall_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})
                      
goal = ("not", ("exists", ("?p", "-", "passenger"), ("not", ("served", "?p"))))

results["elevator_strips_exists_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pboard,eboard,[("?f", "f1"), ("?p", "p1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pboard,eboard,[("?f", "f3"), ("?p", "p0")]),
                      (pserve,eserve,[("?f", "f3"), ("?p", "p1")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pserve,eserve,[("?f", "f2"), ("?p", "p0")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})
                      
pstop = ("lift-at", "?f")
estop = ("and",
               ("forall", ("?p", "-", "passenger"), 
                  ("when", ("and", ("boarded", "?p"),
                             ("destin", "?p", "?f")),
                        ("and", ("not", ("boarded", "?p")),
                             ("served", "?p")))),
               ("forall", ("?p", "-", "passenger"), 
                   ("when", ("and", ("origin", "?p", "?f"), ("not", ("served", "?p"))),
                              ("boarded", "?p"))))

goal = ("forall", ("?p", "-", "passenger"), ("served", "?p"))
results["elevator_adl_1_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pstop,estop,[("?f", "f1")])], ("boarded", "p1"), True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})

results["elevator_adl_2_subst"] = run_test_plan(facts, [(pup,eup,[("?f1", "f0"), ("?f2", "f1")]),
                      (pstop,estop,[("?f", "f1")]),
                      (pup,eup,[("?f1", "f1"), ("?f2", "f3")]),
                      (pstop,estop,[("?f", "f3")]),
                      (pdown,edown,[("?f1", "f3"), ("?f2", "f2")]),
                      (pstop,estop,[("?f", "f2")])], goal, True, {"passenger": ["p0", "p1"], "": ["p0", "p1"]})
                      
pload = ("and", ("at", "?t", "?l"), ("at", "?p", "?l"), ("free", "?a1", "?t"),
  		    ("forall", ("?a2", "-", "truckarea"),
  			    ("imply", ("closer", "?a2", "?a1"), ("free", "?a2", "?t"))))
                
eload = ("and", ("not", ("at", "?p", "?l")), ("not", ("free", "?a1", "?t")), ("in", "?p", "?t", "?a1"))

punload = ("and", ("at", "?t", "?l"), ("in", "?p", "?t", "?a1"),
  		    ("forall", ("?a2", "-", "truckarea"),
  			    ("imply", ("closer", "?a2", "?a1"), ("free", "?a2", "?t"))))
eunload = ("and", ("not", ("in", "?p", "?t", "?a1")), ("free", "?a1", "?t"), ("at", "?p", "?l"))

pdrive = ("and", ("at", "?t", "?from"), ("connected", "?from", "?to"))
edrive = ("and", ("not", ("at", "?t", "?from")), ("at", "?t", "?to"))

facts = [("at", "truck1", "l2"), ("free", "a1", "truck1"), ("free", "a2", "truck1"),
         ("closer", "a1", "a2"), ("at", "package1", "l2"), ("at", "package2", "l2"), ("at", "package3", "l2"),
         ("connected", "l1", "l2"), ("connected", "l1", "l3"), ("connected", "l2", "l1"), ("connected", "l2", "l3"),
         ("connected", "l3", "l1"), ("connected", "l3", "l2")]

results["truck_pre"] = run_test_simple(facts, sub(pload, [("?t", "truck1"), ("?l", "l2"), ("?p", "package1"), ("?a1", "a2")]),  True, {"trucks": ["truck1", "truck2"], "truckarea": ["a1", "a2"], "": ["a1", "a2", "truck1", "truck2"]})

facts = [("at", "truck1", "l3"), ("free", "a1", "truck1"), ("free", "a2", "truck1"),
         ("closer", "a1", "a2"), ("at", "package1", "l2"), ("at", "package2", "l2"), ("at", "package3", "l2"),
         ("connected", "l1", "l2"), ("connected", "l1", "l3"), ("connected", "l2", "l1"), ("connected", "l2", "l3"),
         ("connected", "l3", "l1"), ("connected", "l3", "l2")]
          
goal = ("and", ("at", "package1", "l1"), ("at", "package2", "l3"))

results["truck_plan"] = run_test_planp(facts, [(pdrive,edrive,[("?t", "truck1"), ("?from", "l3"), ("?to", "l2")]),
                      (pload,eload,[("?t", "truck1"), ("?l", "l2"), ("?p", "package1"), ("?a1", "a2")]),
                      (pload,eload,[("?t", "truck1"), ("?l", "l2"), ("?p", "package2"), ("?a1", "a1")]),
                      (pdrive,edrive,[("?t", "truck1"), ("?from", "l2"), ("?to", "l3")]),
                      (punload,eunload,[("?t", "truck1"), ("?l", "l3"), ("?p", "package2"), ("?a1", "a1")]),
                      (pdrive,edrive,[("?t", "truck1"), ("?from", "l3"), ("?to", "l1")]),
                      (punload,eunload,[("?t", "truck1"), ("?l", "l1"), ("?p", "package1"), ("?a1", "a2")])], goal, True, {"trucks": ["truck1", "truck2"], "truckarea": ["a1", "a2"], "": ["a1", "a2", "truck1", "truck2"]})
                      
results["truck_plan_subst"] = run_test_plan(facts, [(pdrive,edrive,[("?t", "truck1"), ("?from", "l3"), ("?to", "l2")]),
                      (pload,eload,[("?t", "truck1"), ("?l", "l2"), ("?p", "package1"), ("?a1", "a2")]),
                      (pload,eload,[("?t", "truck1"), ("?l", "l2"), ("?p", "package2"), ("?a1", "a1")]),
                      (pdrive,edrive,[("?t", "truck1"), ("?from", "l2"), ("?to", "l3")]),
                      (punload,eunload,[("?t", "truck1"), ("?l", "l3"), ("?p", "package2"), ("?a1", "a1")]),
                      (pdrive,edrive,[("?t", "truck1"), ("?from", "l3"), ("?to", "l1")]),
                      (punload,eunload,[("?t", "truck1"), ("?l", "l1"), ("?p", "package1"), ("?a1", "a2")])], goal, True, {"trucks": ["truck1", "truck2"], "truckarea": ["a1", "a2"], "": ["a1", "a2", "truck1", "truck2"]})
                      
exp = ("forall", ("?v", "-", ""), ("forall", ("?v1", "-", ""), ("has", "?v", "?v1")))
facts = [("has", "a", "b"), ("has", "b", "a"), ("has", "a", "c"), ("has", "c","a")]

results["nested_forall_false"] = run_test_simple(facts, exp, False, sets={"": ["a", "b", "c"]})

facts = [("has", "a", "b"), ("has", "a", "a"), ("has", "b", "a"), ("has", "b", "b"), ("has", "a", "c"), ("has", "c","a"), ("has", "c", "c"), ("has", "b", "c"), ("has", "c", "b")]
results["nested_forall_true"] = run_test_simple(facts, exp, True, sets={"": ["a", "b", "c"]})

print("passed %d of %d tests"%(passed, run))
for t in results:
    print(t, results[t])




