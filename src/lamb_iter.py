import itertools, random, math, time, sys
from more_itertools import random_combination 
from .bf_solver import BFSolver
from .asp_solver import ASPSolver 
import src.utils as utils
import matplotlib.pyplot as plt

class Compare_Kemnash():
    """ Class to compare two judgement aggregation methods (solver+rule+lambda)
    with each other. If methods are the same than analysis one a single method."""

    def __init__(self, scenario, lambs:list, sample:int=250000):
        """The class is initialized with:
        scenario;
        lambs: value of lambda-parameter for parameterised Kemeny-Nash rule
        sample: sample x 10^4 is max number of iterations (ie if sample>num_profs -> arg ignored)"""
        self.scenario = scenario
        self.lambs = lambs
        if len(lambs) == 1:
            self.single = True
        if self.scenario.num_profs > sample:
            self.sample = True
            self.prof_test = sample
            self.indices = [0] * sample
        else:
            self.sample = False
            self.prof_test = self.scenario.num_profs
        # Useful for iteration later on
        self.rules = ['Kem', 'KN', 'Maxham', 'Maxeq']
        self.rulesComb = ['KemKN', 'KemMaxham', 'KemMaxeq', 'KN-Maxham', 'KN-Maxeq']
        self.outcomes = []
        self.idxs_outcomes = []

    def result(self, verbose=True):
        """ 
        all_ex: If True all examples are printed; otherwise, only the ones with different outcomes.
        num_ex: Maximal number of examples to be printed.
        sample: Number of profiles (*10^-4) computed. If 0 all profiles computed.
        time_an: If True time (comparison) analysis is executed.
        show_res: Dictionary with results is printed (in a nice format).
        simulate: If self.prof_tot > simulate, a profile (multiset) is simulated as random 
                permutation. (To prevent RAM overflow.)"""
        ########    GROUNDWORK    ########
        # Random seed
        random.seed(time.time())
        # Variable to show time estimation (after 60s).
        first_pass = True
        prof_done = 0
        # Convenient shorthands
        bfs = BFSolver(binrep=False, idx_rep=True)

        # Initialise dictionaries to keep counts during profile iterations for current lambda.
        cumQuan = {}
        cumQual = {}
        for rule in self.rules:
            cumQuan['sol'+rule] = 0
        for comb in self.rulesComb:
            cumQuan['symdif'+comb] = 0
        for count in ['mean', 'SD', 'low', 'maxdist']:
            for rule in self.rules:
                cumQual[count+rule] = 0 
        cumQual['ZE'] = 0

        # Initialise dictionary to append results for single lambda
        final = {}
        for comb in self.rulesComb:
            final['symdif'+comb] = []
        for rule in self.rules:
            final['sol/prof'+rule] = []
        final.update({'R-meanKN':[], 'R-meanMaxham':[], 'R-meanMaxeq': [], 'R-lowKem':[], 'R-lowKN':[]})
        final.update({'R-maxdistKem':[], 'R-maxdistKN':[], 'ZE':[], 'SD-KNKem':[]})
        final.update({'meanKN':[], 'SDKN':[], 'lowKN':[], 'maxdistKN':[]})

        ########    FOR EVERY LAMBDA ITERATE THROUGH PROFILES    ########
        t0 = time.time()
        for idxl,lamb in enumerate(self.lambs):
            # Empty cumulative dicts.
            for label in cumQuan:
                cumQuan[label] = 0
            for label in cumQual:
                cumQual[label] = 0
            if not self.sample:
                self.indices = itertools.combinations_with_replacement(
                    range(len(self.scenario.in_consistent)), self.scenario.number_voters)

            for index in self.indices:
                if self.sample:
                    # Get random multiset index
                    pool = tuple(self.scenario.out_consistent)
                    num_consistent = len(pool)
                    index = tuple(sorted(random.choices(range(num_consistent), k=self.scenario.number_voters)))
                # Constructing profile corresponding to index
                self.scenario.profile = []
                for i in range(len(self.scenario.in_consistent)):
                    num_occur = list(index).count(i)
                    if num_occur > 0:
                        self.scenario.profile.append([num_occur, utils.jdict_to_js(self.scenario.in_consistent[i])])

                # Using the modified Jaggpy solvers to compute outcomes of profile.
                self.idxs, self.outcomes = bfs.all_outcomes(self.scenario, "all_rules", lamb)
                self.idxs = [set(idxs) for idxs in self.idxs]

                #  Updating quantitative analysis dict 
                cumQuan = self.quantitative_analysis(cumQuan)
                #  Updating qualitative analysis dict
                cumQual = self.qualitative_analysis(cumQual)

                ###  TIMER  ###
                # After 60s it will give an estimate of duration
                prof_done += 1
                t = time.time()
                if t - t0 > 30 and first_pass and idxl == 0:
                    time_est = int((len(self.lambs) * self.prof_test * (t - t0)) / (prof_done * 60))
                    print('TIME INDICATION: '+str(prof_done)+'/'+str(self.prof_test) + ' took ' +\
                    str(int(t-t0))+'s. Estimate total time: ' + str(time_est) + 'min.')
                    first_pass = False

            ############    PROCESSING RESULTS    ############
            for comb in self.rulesComb:
                final['symdif'+comb].append(((cumQuan['symdif'+comb]) / float(self.prof_test)) / len(self.scenario.out_consistent))
            for rule in self.rules:
                final['sol/prof'+rule].append(cumQuan['sol'+rule] / float(self.prof_test))
            final['R-meanKN'].append(cumQual['meanKN']/cumQual['meanKem'])
            final['R-meanMaxham'].append(cumQual['meanMaxham']/cumQual['meanKem'])
            final['R-meanMaxeq'].append(cumQual['meanMaxeq']/cumQual['meanKem'])
            final['R-lowKem'].append(cumQual['lowKem']/cumQual['lowMaxham'])
            final['R-lowKN'].append(cumQual['lowKN']/cumQual['lowMaxham'])
            final['R-maxdistKem'].append(cumQual['maxdistKem']/cumQual['maxdistMaxeq'])
            final['R-maxdistKN'].append(cumQual['maxdistKN']/cumQual['maxdistMaxeq'])
            # final['SD-KNKem'].append(round( cumQual['SDKN']/cumQual[', 2))
            final['ZE'].append(cumQual['ZE'] / self.prof_test)
            final['meanKN'].append(cumQual['meanKN']/self.prof_test)
            final['SDKN'].append(cumQual['SDKN']/self.prof_test)
            final['lowKN'].append(cumQual['lowKN']/self.prof_test)
            final['maxdistKN'].append(cumQual['maxdistKN']/self.prof_test)
        return final

    def quantitative_analysis(self, cumQuan):
        """Updates counts necessary for symmetric difference computations"""
        # Adding number of solutions.
        for idx,rule in enumerate(self.rules):
            cumQuan['sol'+rule] += len(self.idxs[idx])
        idxKem, idxKN, idxMaxham, idxMaxeq = self.idxs
        idxs1 = [idxKem, idxKem, idxKem, idxKN, idxKN]
        idxs2 = [idxKN, idxMaxham, idxMaxeq, idxMaxham, idxMaxeq]
        for idx,comb in enumerate(self.rulesComb):
            cumQuan['symdif'+comb] += len(idxs1[idx].symmetric_difference(idxs2[idx]))
        return cumQuan

    def qualitative_analysis(self, cumQual):
        """Comparing utalitarian and egalitarian measures."""
        # Computations. 
        agr_msets = [[utils.agr(self.scenario, out) for out in outcomes] for outcomes in self.outcomes] 
        means = [[sum(agr_mset)/float(len(agr_mset)) for agr_mset in agr_mseti] for agr_mseti in agr_msets] 
        dists2 = [[[(agr_msets[ridx][oidx][nidx] - means[ridx][oidx])**2 for nidx in range(self.scenario.number_voters)]
            for oidx in range(len(self.outcomes[ridx]))] for ridx in range(len(self.rules))] 
        SDs = [[math.sqrt(sum(dists)/float(len(dists))) for dists in dists2i] for dists2i in dists2]
        lows = [[min(agr_mset) for agr_mset in agr_mseti] for agr_mseti in agr_msets]
        maxdists = [[max(agr_msets[ridx][oidx]) - min(agr_msets[ridx][oidx]) for oidx in range(
            len(self.outcomes[ridx]))] for ridx in range(len(self.rules))]
        # Zero effect
        ZE = float([min([bool(SDs[1][KNIdx] > SDs[0][KemIdx]) for KemIdx in range(len(self.outcomes[0]))])
            for KNIdx in range(len(self.outcomes[1]))].count(True) / len(self.outcomes[1]))
        for idx,rule in enumerate(self.rules):
            cumQual['mean'+rule] += sum(means[idx])/float(len(means[idx]))
            cumQual['SD'+rule] += sum(SDs[idx])/float(len(SDs[idx]))
            cumQual['low'+rule] += sum(lows[idx])/float(len(lows[idx]))
            cumQual['maxdist'+rule] += sum(maxdists[idx])/float(len(maxdists[idx]))
        cumQual['ZE'] += ZE
        return cumQual