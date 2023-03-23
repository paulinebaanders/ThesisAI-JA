from functools import reduce
from math import sqrt, factorial
from fractions import Fraction
import itertools
import copy
from nnf import Var, Or, And
from .parser import Parser

####  SWITCHING REPRESENTATION JUDGEMENT ####
# jdict to..
def jdict_to_js(jdict):
    """The jdict is a dictionary with keys the issues. The returned
    judgement set (js) contains all issues that are 'True' in jdict."""
    js = []
    for issue in jdict.keys():
        if jdict[issue]:
            js.append(issue)
    return js
def jdict_to_bin(ordered_jdict):
    bin_string = ''
    for value in ordered_jdict.values():
        if value:
            bin_string += '1'
        else:
            bin_string += '0'
    return bin_string
# js to..
def js_to_jdict(scenario, js):
    """The js (judgment set) is a list containing accepted issues. With the agenda
    from self this js is put into a judgment; a dictionary containing for all issues
    True or False."""
    jdict = {}
    for issue in scenario.agenda.values():
        if issue in js:
            jdict[issue] = True
        else:
            jdict[issue] = False
    return jdict 
def js_to_bin(scenario, js):
    ordered_jdict = js_to_jdict(scenario, js)
    return jdict_to_bin(ordered_jdict)

####  SWITCHING REPRESENTATION PROFILE ####
def prof_mset_bin(scenario):
    sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    profile = []
    for mult_js in scenario.profile:
        profile.append(js_to_bin(scenario, mult_js[1])+str(mult_js[0]).translate(sup))
    return profile
def prof_mset(prof):
    sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    profile = []
    for mult_js in prof:
        profile.append(js_to_bin(scenario, mult_js[1])+str(mult_js[0]).translate(sup))
    return profile

####  OPERATIONS ON (COLLECTIONS OF) JUDGEMENTS ####
def order_dict(scenario, dict_in):
    result = {}
    for issue in scenario.agenda.values():
        result[issue] = dict_in[issue]
    return result
def revert_jdict(jdict, jdict2=False):
    """ Every value in jdict dict is reversed: True <-> False"""
    if jdict2 == False:        
        jdict_opposite = {}
        for key,val in jdict.items():
            if val == True:
                jdict_opposite[key] = False
            else:
                jdict_opposite[key] = True
        return jdict_opposite
    else:
        assert len(jdict)==len(jdict2)
        revert = True
        for issue,val in jdict.items():
            if val == jdict2[issue]:
                revert = False
                break
        return revert
def all_jdicts_bin(all_jdicts):
    binlist = []
    for jdict in all_jdicts.values():
        binlist.append(jdict_to_bin(jdict))
    return binlist
def count_consistentOpp(all_jdicts):
    """
    all_jdicts contains all consistent judgment sets we count
    the number of *pairs* that are antipodal"""
    countOpp = 0
    for idx1,idx2 in itertools.combinations(range(len(all_jdicts)), 2):
        if revert_jdict(all_jdicts[idx1], all_jdicts[idx2]):
            countOpp += 1
    return countOpp

####  OPERATIONS ON (COLLECTIONS OF) OUTCOMES ####
def clean_outcome(agenda, outcomes):
    """From original Jaggpy (modified)."""
    for i, outcome in enumerate(outcomes):
        translated_outcomes = {}
        for formula in outcome.keys():
            if formula[0] == 'l':
                #BUG5
                label = int(formula[1:])
                translation = scenario.agenda[label]
                translated_outcomes[translation] = outcome[formula]
        outcomes[i] = translated_outcomes
    # Remove duplicates from outcomes.
    final = [dict(t) for t in {tuple(outcome.items()) for outcome in outcomes}]
    return final
def agr(scenario, outcome:dict, lamb=0):
    """ADDED. The function gets an agenda and profile (j1, ..., jn), and jdict J 
    (i.e., canditate [clean] outcome. It computes a list 
    agr_vec=[j_1\cap J + lamb,..., jn \cap J + lamb]) """
    agr_vec = []
    for js_pair in scenario.profile:
        score = 0
        times_occur = js_pair[0]
        js = js_pair[1]
        for formula in scenario.agenda.values():
            if formula in js and outcome[formula]==True:
                score += 1
            elif formula not in js and outcome[formula]==False:
                score += 1
        if score == 0:
            score = lamb
        agr_vec.extend([score] * times_occur)
    return agr_vec

# Number of multisets of cardinality k, from set with n elements
def multiset_coefficient(n, k):
    """Formula for number of multisets with cardinality k from
    underlying set with n elements: C^R(n,k)=(n+k-1)!/(k!(n-1)!)"""
    return int(factorial(n+k-1) / (factorial(k) * factorial(n-1)))
# list (~set) to multiset
def mset(list_):
    """let list = [0,0,0,2,2], then mset(lex) =[0^3, 2^2] """
    sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    # remove duplicates from original list
    elements = []
    [elements.append(ele) for ele in list_ if ele not in elements]
    mset = []
    for ele in elements:
        mset.append(str(ele)+str(sum(ele_it == ele for ele_it in list_)).translate(sup))
    return mset
# Print lists
def print_list(list_):
    if type(list_[0]) == float:
        list_ = [round(ele, 2) for ele in list_]
        if len(list_) == 1:
            return str(list_[0])
    if type(list_[0]) == int and len(list_)==1:
        return str(list_[0])
    if len(list_) == 1:
        return '('+str(list_[0])+')'
    else:
        string = '('+str(list_[0])
        for ele in list_[1:]:
            string += ', '+str(ele)
        return string+')'
def print_inits(module):
    str_print = {}
    # Solver 1
    if module.solver1 == "bf":
        str_print['s1'] = "BFS"
    else:
        str_print['s1'] = "ASP"
    # Rule 1
    str_print['r1'] = str_rule(module.rule1, module.solver1, module.lamb1)
    # Total method 1.
    if module.rule1 in ["lamb-kemnash", "lamb-kemnash-opt"]:
        str_print['t1'] = str_print['r1'][:-1]+', '+str_print['s1']+']'
    else:
        str_print['t1'] = str_print['r1']+' ['+str_print['s1']+']'
    if module.singleMethod:
        return str_print
    # Solver 2
    if module.solver2 == "bf":
        str_print['s2'] = "BFS"
    else:
        str_print['s2'] = "ASP"
    # Rule 2
    str_print['r2'] = str_rule(module.rule2, module.solver2, module.lamb2)
    # Total method 1.
    if module.rule2 in ["lamb-kemnash", "lamb-kemnash-opt"]:
        str_print['t2'] = str_print['r2'][:-1]+', '+str_print['s2']+']'
    else:
        str_print['t2'] = str_print['r2']+' ['+str_print['s2']+']'
    return str_print

def str_rule(rule, solver, lamb):
    if rule == "kemeny" and solver == "bf":
        str_rule = "Kemeny"
    elif rule == "kemeny":
        str_rule = "Kemeny [Opt]"
    elif rule == "kemnash" and solver == "bf":
        str_rule = "Kemeny-Nash"
    elif rule == "kemnash":
        str_rule = "Kemeny-Nash [Opt]"
    elif rule == "lamb-kemnash" and solver == "bf":
        str_rule = "\u03BB-Kemeny-Nash [\u03BB="+str(lamb)+"]"
    elif rule == "lamb-kemnash":
        str_rule = "\u03BB-Kemeny-Nash [Opt, \u03BB="+str(lamb)+"]"
    elif rule == "kemeny-original" and solver == "bf":
        str_rule = "Kemeny [JA-ASP]"
    elif rule == "kemeny-original":
        str_rule = "Kemeny [Opt, JA-ASP]"
    elif rule == "kemeny-sat":
        str_rule = "Kemeny [Sat]"
    elif rule== "kemnash-sat":
        str_rule = "Kemeny-Nash [Sat]"
    elif rule == "lamb-kemnash-sat":
        str_rule = "\u03BB-Kemeny-Nash [Sat, \u03BB="+str(lamb)+"]"
    elif rule == "kemeny-original-sat":
        str_rule = "Kemeny [Sat, JA-ASP]"
    else:
        str_rule = rule
    return str_rule