#####################################################################
## Module from JAGGPY, some rules added.
## Modifications include moving computing the consistent outcomes
## to .src.classes
#####################################################################

import copy, math, warnings, time
from itertools import combinations
from nnf import Var, Or, And # pylint: disable=unused-import
from .classes import Solver
from .parser import Parser
import src.utils as utils

class BFSolver(Solver):
    """A brute force solver for Judgment Aggregation."""
    def __init__(self, binrep=False, idx_rep=False):
        self.binrep = binrep
        self.idx_rep = idx_rep
        self.idxs = 0

    def all_outcomes(self, scenario, rule, lamb=0):
        """Given a scenario object and the name of a rule
        this function will yield a list with all the outcomes
        of the judgment aggregation. The rule should be given
        as a string and can be one of the following lowercase commands:
            - kemeny            (New Kemeny implementation)
            - kemnash           (Kemeny-Nash implementation - with lamb=0)
            - lamb-kemnash      (Kemeny-Nash implementation - with lamb>0)
            - kemeny-original (Kemeny from JAGGPY)
        The utility of a player with judgment J_i when outcome is J is calculated
        as U_i = agr(J_i,J)+lamb.
        """
        self.idxs = 0
        # We determine the outcome with a helper function for corresponding rule.
        # Kemeny rule.
        if rule == "kemeny":
            outcomes = self.solve_kemeny(scenario)
        # Kemeny-Nash rule.
        elif rule == "kemnash":
            if lamb > 0:
                warnings.warn("For nonzero values of \u03BB for use parameterised Kemeny-Nash rule, now \u03BB is set to 0.")
            outcomes = self.solve_kemnash(scenario, 0)
        # Parameterised Kemeny-Nash rule.
        elif rule == "lamb-kemnash":
            outcomes = self.solve_kemnash(scenario, lamb)
        # Original Kemeny rule implementation from JAGGPY package.
        elif rule == "kemeny-original":
            outcomes = self.solve_kemeny_original(scenario)
        elif rule == "maxham":
            outcomes = self.solve_maxham(scenario)
        elif rule == "maxeq":
            outcomes = self.solve_maxeq(scenario)
        elif rule == "all_rules":
            outcomes = self.solve_all(scenario, lamb)
        else:
            raise Exception (f"{rule} is not a recognized aggregation rule.")
        if self.binrep:
            if rule == "all_rules":
                return [[utils.jdict_to_bin(out) for out in out_sing] for out_sing in outcomes]
            else:
                return [utils.jdict_to_bin(d) for d in outcomes]
        if self.idx_rep:
            return self.idxs, outcomes
        return outcomes

    def support_number(self, agenda, profile):
        """The function support_number gets an agenda and profile and returns a dictionary, 
        containing label,occurence pairs.
        Not used in new implementation; however, self.agr is based on it."""
        support_count = dict()
        for formula in agenda.values():
            support_count[formula] = 0
        for judgement_set in profile:
            times_accepted = judgement_set[0]
            accepted_formula = judgement_set[1]
            for formula in accepted_formula:
                support_count[formula] += times_accepted
        return support_count

    def agr(self, scenario, outcome:dict, lamb=0):
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

    def solve_kemeny(self, scenario):
        """New implementation based on list comprehension. Effect on performance is 
        neglectable."""
        agr_vecs = [self.agr(scenario, outcome) for outcome in scenario.out_consistent]
        # agr_sums = [reduce((lambda x,y: x+y), agr_vec) for agr_vec in agr_vecs]
        agr_sums = [sum(agr_vec) for agr_vec in agr_vecs]
        self.idxs = [idx for idx,agr in enumerate(agr_sums) if agr == max(agr_sums)]
        return [scenario.out_consistent[idx] for idx in self.idxs]

    def solve_kemnash(self, scenario, lamb=0):
        """New implementation based on list comprehension. Effect on performance is 
        neglectable."""
        agr_vecs = [self.agr(scenario, outcome, lamb) for outcome in scenario.out_consistent]
        agr_prods = [math.prod(agr_vec) for agr_vec in agr_vecs]
        self.idxs = [idx for idx,agr in enumerate(agr_prods) if agr == max(agr_prods)]
        return [scenario.out_consistent[idx] for idx in self.idxs]

    def solve_maxham(self, scenario):
        """Maximises the minimum agreement."""
        agr_vecs = [self.agr(scenario, outcome) for outcome in scenario.out_consistent]
        agr_mins = [min(agr_vec) for agr_vec in agr_vecs]
        self.idxs = [idx for idx,agr in enumerate(agr_mins) if agr == max(agr_mins)]
        return [scenario.out_consistent[idx] for idx in self.idxs]

    def solve_maxeq(self, scenario):
        """Minimises the maximum distance."""
        agr_vecs = [self.agr(scenario, outcome) for outcome in scenario.out_consistent]
        agr_maxDists = [ (max(agr_vec) - min(agr_vec)) for agr_vec in agr_vecs]
        self.idxs = [idx for idx,agr in enumerate(agr_maxDists) if agr == min(agr_maxDists)]
        return [scenario.out_consistent[idx] for idx in self.idxs]

    def solve_all(self, scenario, lamb):
        agr_vecs = [self.agr(scenario, outcome) for outcome in scenario.out_consistent]
        agr_vecs_lamb = [self.agr(scenario, outcome, lamb) for outcome in scenario.out_consistent]
        # Manipulation on agreement vectors.
        agr_sums = [sum(agr_vec) for agr_vec in agr_vecs]
        agr_prods = [math.prod(agr_vec) for agr_vec in agr_vecs_lamb]
        agr_mins = [min(agr_vec) for agr_vec in agr_vecs]
        agr_maxDists = [ (max(agr_vecs[out_idx]) - agr_mins[out_idx]) for out_idx in range(len(agr_vecs))]
        # Computing different optima.
        idxs_kem = [idx for idx,agr in enumerate(agr_sums) if agr == max(agr_sums)]
        idxs_kn = [idx for idx,agr in enumerate(agr_prods) if agr == max(agr_prods)]
        idxs_maxham = [idx for idx,agr in enumerate(agr_mins) if agr == max(agr_mins)]
        idxs_maxeq = [idx for idx,agr in enumerate(agr_maxDists) if agr == min(agr_maxDists)]
        self.idxs = [idxs_kem, idxs_kn, idxs_maxham, idxs_maxeq]
        return [[scenario.out_consistent[idx] for idx in idxs_opt] for idxs_opt in self.idxs]

    def solve_kemeny_original(self, scenario):
        """Slightly modified to be compatible with implementation."""
        # Keep track of the maximum agreement score and initiate list of outcomes.
        max_agreement = 0
        outcomes = []
        # Check agreement score for each outcome and update list of outcomes accordingly.
        for outcome in scenario.out_consistent:
            agreement_score = 0
            # For each formula in the pre-agenda, check how many agents agree
            # with the outcome and update agreement score.
            for issue in outcome.keys():
                support = self.support_number(scenario.agenda, scenario.profile)
                if outcome[issue]:
                    agreement_score += support[issue]
                else:
                    agreement_score += scenario.number_voters - support[issue]
            if agreement_score == max_agreement:
                outcomes.append(outcome)
            elif agreement_score > max_agreement:
                max_agreement = agreement_score
                outcomes = [outcome]
        return outcomes
    
