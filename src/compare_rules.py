import itertools, random, math, time, sys
from more_itertools import random_combination 
from .bf_solver import BFSolver
from .asp_solver import ASPSolver 
import src.utils as utils

class CompareRules():
    """ Class to compare two judgement aggregation methods (solver+rule+lambda)
    with each other. If methods are the same than analysis one a single method."""

    def __init__(self, scenario, solver1:str, rule1:str, lamb1:float, 
                    solver2:str, rule2:str, lamb2:float):
        """The class is initialized with:
        scenario;
        solver1: choices "bf" (brute force) or "asp" (Answer Set Programming).
        rule1: rule uses in first method, options:
                "kemeny", "kemnash", "lamb-kemnash", "kemeny-original" for bf; 
                "kemeny", "kemnash", "lamb-kemnash", "kemeny-sat", "kemnash-sat"
                "lamb-kemnash-sat", "kemeny-original", "kemeny-sat-original" for asp.
        lamb1: Value for \u03BB that is used in parameterised (lamb-kemnashX) implementation.
        solver2: idem solver1.
        rule2: idem rule1.
        lamb2: idem lamb1."""
        self.scenario = scenario
        self.solver1 = solver1
        self.rule1 = rule1
        self.lamb1 = lamb1
        self.solver2 = solver2
        self.rule2 = rule2
        self.lamb2 = lamb2
        self.singleMethod = False
        # If single method:
        if solver1==solver2 and rule1==rule2 and lamb1==lamb2:
            self.singleMethod = True
        self.prof_tot = 0
        self.prof_test = 0
        self.indices = 0


    def result(self, all_ex:bool=False, num_ex:int=1, sample:int=250000, 
                time_an:bool=False, show_res:bool=True, simulate:int=40000000):
        """ 
        all_ex: If True all examples are printed; otherwise, only the ones with different outcomes.
        num_ex: Maximal number of examples to be printed.
        sample: Number of profiles computed. If 0 all profiles computed.
        time_an: If True time (comparison) analysis is executed.
        show_res: Dictionary with results is printed (in a nice format).
        simulate: If self.prof_tot > simulate, a profile (multiset) is simulated as random 
                permutation. (To prevent RAM overflow.)"""
        ##################################################
        ################    GROUNDWORK    ################
        ##################################################
        # Random seed
        random.seed(time.time())
        # To calculate total time
        time_tot0 = time.time() 
        # Variable to show time estimation (after 60s).
        first_pass = True
        prof_done = 0
        # Convenient shorthands
        bfs = BFSolver(binrep=False)
        asp = ASPSolver(binrep=False)

        # Computing total number of profiles (= multisets).
        self.prof_tot = self.scenario.num_profs
        # If sample > self.prof_tot all profiles are iterated and sample set 0
        if sample > self.prof_tot:
            sample = 0
        # In case self.prof_tot > simulate 
        if self.prof_tot > simulate and sample > 0:
            print('PROFILE SIMULATION')
            self.indices = [0] * sample
            self.prof_test = sample
        elif self.prof_tot > simulate:
            print('PROFILE SIMULATION')
            self.indices = [0] * self.prof_tot
            self.prof_test = self.prof_tot
        else:
            self.indices = self.compute_indices(sample)

        # Counts to measure quantitative difference.
        cum = {'sol1':0, 'sol2':0, 'overlap':0, 'overlap_same':0, 'overlap_dif':0}
        cum.update({'prof_same':0, 'prof_1same':0, 'ZEx10':0})
        # Counts to measure qualitative difference.
        cum.update({'sum_agr1':0, 'sum_agr2':0, 'mean_agr1':0, 'mean_agr2':0})
        cum.update({'mean_dist1':0, 'mean_dist2':0, 'num_below1':0, 'num_below2':0})
        cum.update({'low_agr1':0, 'low_agr2':0, 'max_agrDif1':0, 'max_agrDif2':0})
        # For printing examples
        examples_print = []
        # For basic time comparison
        time_r1 = 0
        time_r2 = 0

        ##################################################
        ########    ITERATING THROUGH PROFILES    ########
        ##################################################
        for index in self.indices:
            # Constructing profile corresponding to index
            self.scenario.profile = self.construct_profile(index)

            time_single0 = time.time()      # For time analysis
            # Using the modified Jaggpy solvers to compute outcomes of profile.
            if self.solver1 == "bf":
                outcomes1 = list(bfs.all_outcomes(
                    self.scenario, self.rule1, self.lamb1))
            else:
                outcomes1 = list(asp.all_outcomes(
                    self.scenario, self.rule1, self.lamb1))
            time_single1 = time.time()      # For time analysis
            if self.singleMethod:
                outcomes2 = outcomes1
            elif self.solver2 == "bf":
                outcomes2 = list(bfs.all_outcomes(
                    self.scenario, self.rule2, self.lamb2))
            else:
                outcomes2 = list(asp.all_outcomes(
                    self.scenario, self.rule2, self.lamb2))
            time_single2 = time.time()      # For time analysis
            # Appending times for time analysis
            time1 = time_single1 - time_single0
            time2 = time_single2 - time_single0
            time_r1 += time1
            time_r2 += time2
            if time_an:
                if prof_done == 0 or time1 > timeMax_r1:
                    timeMax_r1 = time1
                    profMax_r1 = self.scenario.profile
                if prof_done == 0 or time1 < timeMin_r1:
                    timeMin_r1 = time1
                    profMin_r1 = self.scenario.profile
                if prof_done == 0 or time2 > timeMax_r2:
                    timeMax_r2 = time2
                    profMax_r2 = self.scenario.profile
                if prof_done == 0 or time2 < timeMin_r2:
                    timeMin_r2 = time2
                    profMin_r2 = self.scenario.profile

            ###  QANTATIVE ANALYSIS  ###
            result_quantitative = self.quantitative_analysis(outcomes1, outcomes2)
            # Processing quantitative analysis
            for key,value in result_quantitative.items():
                cum[key] += value

            ###  QUALITATIVE ANALYSIS  ###
            result_qualitative = self.qualitative_analysis(outcomes1, outcomes2)
            # Processing qualitative analysis
            for key,value in result_qualitative.items():
                if type(value) == float:
                    cum[key] += value

            ###  EXAMPLES TO PRINT  ###
            # Adding extensive comparison to examples to print
            if len(examples_print) < num_ex:          
                if not all_ex and result_quantitative['prof_same'] == 1:
                    continue
                else:
                    example = {'prof':self.scenario.profile, 'out1':outcomes1, 'out2':outcomes2}
                    example['same'] = bool(result_quantitative['prof_same'])
                    for measure,value in result_qualitative.items():
                        example[measure] = result_qualitative[measure]
                    examples_print.append(example)

            ###  TIMER  ###
            # After 60s it will give an estimate of duration
            prof_done += 1
            t = time.time()
            if t - time_tot0 > 60 and first_pass:
                time_est = int((self.prof_test * (t - time_tot0)) / (prof_done * 60))
                print('TIME INDICATION: '+str(prof_done)+'/'+str(self.prof_test) + ' took ' +\
                str(int(t-time_tot0))+'s. Estimate total time: ' + str(time_est) + 'min.')
                first_pass = False

        ##################################################
        ############    PROCESSING RESULTS    ############
        ##################################################
        ###  PRINT EXAMPLES  ###
        if num_ex > 0:
            self.print_examples(examples_print)

        ###  PUTTING TOGETHER RELEVANT RESULTS  ###
        result = {}
        for key,value in cum.items():
            if type(value) == float:
                result[key] = value / self.prof_test
            else:
                result[key] = value
        result['sym_dif'] = ( cum['sol1']+cum['sol2']-2*cum['overlap'] ) / (
            cum['sol1']+cum['sol2']-cum['overlap'])
        result['rules_equiv'] = bool(cum['prof_same'] == self.prof_test)

        # Processing times and time analysis
        time_tot1 = time.time()
        result['time_tot'] = time_tot1 - time_tot0
        result['time_r1'] = time_r1
        result['time_r2'] = time_r2
        result['iters1sec_r1'] = '{:.2e}'.format(self.prof_test / time_r1)
        result['iters1sec_r2'] = '{:.2e}'.format(self.prof_test / time_r2)
        if time_an:
            result['tmax//tmin_r1'] = '{:.0f}'.format(timeMax_r1 // timeMin_r1)
            result['tmax//tmin_r2'] = '{:.0f}'.format(timeMax_r2 // timeMin_r2)
            self.scenario.profile = profMax_r1
            result['prof_max_r1'] = utils.prof_mset_bin(self.scenario)
            self.scenario.profile = profMin_r1
            result['prof_min_r1'] = utils.prof_mset_bin(self.scenario)
            self.scenario.profile = profMax_r2
            result['prof_max_r2'] = utils.prof_mset_bin(self.scenario)
            self.scenario.profile = profMin_r2
            result['prof_min_r2'] = utils.prof_mset_bin(self.scenario)

        ###  PRINT RESULTS  ###
        if show_res:
            result_string = {}
            for label in result:
                if type(result[label]) == float:
                    result_string[label] = '{:.2f}'.format(result[label])
                elif type(result[label]) == int:
                    result_string[label] = '{:.2e}'.format(result[label])
                else:
                    result_string[label] = result[label]
            self.print_result(result_string)
        return result

    def quantitative_analysis(self, outcomes1:list, outcomes2:list):
        """Given lists outcomes1 and outcomes2:
        the overlap (int) between solutions and whether solutions are the 
        same (bool) is calculated."""
        quan = {}
        quan['sol1'] = len(outcomes1)
        if self.singleMethod:
            return quan
        quan['sol2'] = len(outcomes2)
        quan['overlap'] = 0
        quan['overlap_same'] = 0
        quan['overlap_dif'] = 0
        quan['prof_1same'] = 0
        quan['prof_same'] = 0

        for out1 in outcomes1:
            for out2 in outcomes2:
                if out1 == out2:
                    quan['overlap'] += 1
                    quan['prof_1same'] = 1

        if len(outcomes1) == len(outcomes2) == quan['overlap']:
            quan['overlap_same'] = quan['overlap']
            quan['prof_same'] = 1
        else:
            quan['overlap_dif'] = quan['overlap']
        return quan

    def qualitative_analysis(self, outcomes1:list, outcomes2:list):
        """The criterions aim to measure the spread in utility among judges (via 
        distances from average utility, and the number of judges with agreement less
        than average). Further, we compare the worst of judge with the best
        of judge (via lowest agreement and greatest difference in agreement)."""
        qual = {}
        # The sets in the comments are multisets (may contain copies).
        # For o in outcomes and i in Voters, let: agr(o,i) = Agr(js_o, js_i) #R
        # (agr_msets)[o] = list({ agr(o,i) | i in Voters })
        qual['agr_msets1'] = [utils.agr(self.scenario, out) for out in outcomes1] 
        
        # # sums[o] = sum({ agr(o,i) | i in Voters })
        # qual['sums1'] = [utils.sum(agr_mset) for agr_mset in qual['agr_msets1']] 
        # means[o] = mean({ agr(o,i) | i in Voters })
        qual['means1'] = [ (sum(agr_mset)/float(len(agr_mset))) for agr_mset in qual['agr_msets1']] 
        # signed_dists1[o] = list({ (agr(o,i) - means[o]) | i in Voters })
        signed_dists1 = [[qual['agr_msets1'][o][i] - qual['means1'][o]
            for i in range(self.scenario.number_voters)] for o in range(len(outcomes1))]
        # dists1[o] = list({ abs(agr(o,i) - means[o]) | i in Voters })
        dists1 = [[abs(signed_dists1[o][i]) for i in range(self.scenario.number_voters)]
            for o in range(len(outcomes1))]
        # mdists[o] = mean({ dist(o,i) | i in Voters})
        qual['mean_dists1'] = [ (sum(dists1[o])/float(len(dists1[o]))) for o in range(len(outcomes1))]
        # Number of judges with agr less than average:
        qual['nums_below1'] = [sum(signed_dists1[o][i] < 0 
            for i in range(self.scenario.number_voters)) for o in range(len(outcomes1))]

        # List with greatest differences in utility.
        qual['greatest_difs1'] = [max(qual['agr_msets1'][o]) - min(qual['agr_msets1'][o]) 
            for o in range(len(outcomes1))]
        # List with lowest utilities.
        qual['lows1'] = [min(qual['agr_msets1'][o]) for o in range(len(outcomes1))]

        # The aggregated values.
        # qual['sum_agr1'] = sum(qual['sums1'])/float(len(qual['sums1'])) #R
        qual['mean_agr1'] = sum(qual['means1'])/float(len(qual['means1']))
        qual['mean_dist1'] = sum(qual['mean_dists1'])/float(len(qual['mean_dists1']))
        qual['num_below1'] = sum(qual['nums_below1'])/float(len(qual['nums_below1']))
        qual['max_agrDif1'] = sum(qual['greatest_difs1'])/float(len(qual['greatest_difs1']))
        qual['low_agr1'] = sum(qual['lows1'])/float(len(qual['lows1']))

        if self.singleMethod:
            return qual
        
        # Same for result from second rule
        qual['agr_msets2'] = [utils.agr(self.scenario, out) for out in outcomes2]
        
        # qual['sums2'] = [sum(agr_mset) for agr_mset in qual['agr_msets2']] #R
        qual['means2'] = [sum(agr_mset)/ float(len(agr_mset)) for agr_mset in qual['agr_msets2']] 
        signed_dists2 = [[qual['agr_msets2'][o][i] - qual['means2'][o]
            for i in range(self.scenario.number_voters)] for o in range(len(outcomes2))]
        dists2 = [[abs(signed_dists2[o][i]) for i in range(self.scenario.number_voters)]
            for o in range(len(outcomes2))]
        qual['mean_dists2'] = [sum(dists2[o])/float(len(dists2[o])) for o in range(len(outcomes2))]
        qual['nums_below2'] = [sum(signed_dists2[o][i] < 0 
            for i in range(self.scenario.number_voters)) for o in range(len(outcomes2))]
        
        qual['greatest_difs2'] = [max(qual['agr_msets2'][o]) - min(qual['agr_msets2'][o]) 
            for o in range(len(outcomes2))]
        qual['lows2'] = [min(qual['agr_msets2'][0]) for o in range(len(outcomes2))]

        # qual['sum_agr2'] = sum(qual['sums2'])/float(len(qual['sums2'])) #R
        qual['mean_agr2'] = sum(qual['means2'])/float(len(qual['means2']))
        qual['mean_dist2'] = sum(qual['mean_dists2'])/float(len(qual['mean_dists2']))
        qual['num_below2'] = sum(qual['nums_below2'])/float(len(qual['nums_below2']))
        qual['max_agrDif2'] = sum(qual['greatest_difs2'])/float(len(qual['greatest_difs2']))
        qual['low_agr2'] = sum(qual['lows2'])/float(len(qual['lows2']))

        # Keep track of negative distances.
        if self.rule1 == "kemeny":
            if self.rule2 == "kemnash" or self.rule2 == "lamb-kemnash":
                # For every outcome2 checks if distance is greater than ALL distances for outcome1
                # then divides number of instances by total number of outcomes 2.
                qual['ZEx10'] = 10 * float([min([bool(qual['mean_dists2'][i] > qual['mean_dists1'][j]) 
                    for j in range(len(outcomes1))]) for i in range(len(outcomes2))].count(True) / len(outcomes2))
        return qual

    def compute_indices(self, sample:int):
        """We build an iterator all_indices that contains tuples that represent
        the indices of consistent judgements in the corresponding profile """
        all_indices = itertools.combinations_with_replacement(
            range(len(self.scenario.in_consistent)), self.scenario.number_voters)
        if sample > 0:
            self.prof_test = sample
            # randomly draw indices from the set of all indices
            all_indices = random_combination(all_indices, self.prof_test)
        else:
            self.prof_test = self.prof_tot
            all_indices = random_combination(all_indices, self.prof_test)
        return all_indices

    def construct_profile(self, index):
        profile = []
        if index == 0:
            profile_permutation = []
            for judge in range(self.scenario.number_voters):
                profile_permutation.append(random.randrange(len(self.scenario.in_consistent)))
            for i in range(len(self.scenario.in_consistent)):
                num_occur = profile_permutation.count(i)
                if num_occur > 0:
                    profile.append([num_occur, utils.jdict_to_js(self.scenario.in_consistent[i])])
        else:
            for i in range(len(self.scenario.in_consistent)):
                num_occur = list(index).count(i)
                if num_occur > 0:
                    profile.append([num_occur, utils.jdict_to_js(self.scenario.in_consistent[i])])
        return profile

    def print_result(self, result:dict):
        from src.utils import print_list as pl
        dum = utils.print_inits(self)
        sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        print('********************************************************')
        print('***************      MAIN  ANALYSIS      ***************')
        print('********************************************************')
        if self.singleMethod:
            print(dum['t1'])
            print('Voters: '+ str(self.scenario.number_voters) + '; '\
                    +'Samples: '+str(self.prof_test)+'/'+str(self.prof_tot)+'; Time: '\
                    +result['time_tot']+'s')
        else:
            print(dum['t1']+'   versus    '+dum['t2']\
                    +'     --  Total time:  '+result['time_tot'])
            print('Voters: '+ str(self.scenario.number_voters) + '; '\
                    +'Samples: '+str(self.prof_test)+'/'+str(self.prof_tot)+'; Time: '\
                    +result['time_tot']+'s; Identical: '+str(result['rules_equiv'])+'.')
        print('**  Quantitative Analysis  **')
        if self.singleMethod:
            print('Solutions: '+result['sol1'])
        else:
            print('Solutions:         '+result['sol1']+' versus '+result['sol2'])
            print('Shared solutions:  '+result['overlap'])
            print('Profiles same:     '+result['prof_same'])
            print('Sym difference:    '+result['sym_dif'])
                        # 'Weighted' number of profiles with distance bigger than Kemeny
            if self.rule1 == "kemeny":
                if self.rule2 == "kemnash" or "lamb-kemnash":
                    print('Zero-effect:       {}e-01'.format(result['ZEx10']))
        print('**  Qualitative Analysis  **')
        if not self.singleMethod:
            # Average agreement = sum({agr(i) | i in voters}) / n
            print('Avg Agr:                '\
                    +result['mean_agr1']+' versus '+result['mean_agr2'])
            # Average dist = sum({Agr(i) - mean(Agr) | i in voters}) / n
            print('Avg dist (Agr to avg):  '\
                    +result['mean_dist1']+' versus '+result['mean_dist2'])
            # #(Agr < avg Agr) = |{agr(i) | agr(i) < avg Agr}|
            print('#(Agr < avg Agr):       '\
                    +result['num_below1']+' versus '+result['num_below2'])
            # Lowest agreement encountered (in any of the outcomes)
            print('Agr low:                '\
                    +result['low_agr1']+' versus '+result['low_agr2'])
            # Agr dist high = max( max(Agr(i)) - min(Agr(i)) )
            print('Agr dist high:          '\
                    +result['max_agrDif1']+' versus '+result['max_agrDif2'])
            print('**  Comparison Times  **')
            print('Total time:            '+result['time_r1']+' versus '+result['time_r2'])
            print('Solver iterations p/s: {} versus {}'.format(
                result['iters1sec_r1'], result['iters1sec_r2']))
            # Time analysis
            if 'tmax//tmin_r1' in result:
                print('**  Time Analysis  **')
                print('tmax//tmin:   '\
                +'{} versus {}'.format(result['tmax//tmin_r1'], result['tmax//tmin_r2']))
                print('Profile max:  '\
                +pl(result['prof_max_r1'])+' versus '+pl(result['prof_max_r2']))
                print('Profile min:  '\
                +pl(result['prof_min_r1'])+' versus '+pl(result['prof_min_r2']))
        else:
            print('Avg Agr:                '+result['mean_agr1'])
            print('Avg dist (Agr to avg):  '+result['mean_dist1'])
            print('#(Agr < avg Agr):       '+result['num_below1'])
            print('Agr low:                '+result['low_agr1'])
            print('Agr dist high:          '+result['max_agrDif1'])
            print('**  Time  **')
            print('Solver iterations p/s: {}'.format(result['iters1sec_r1']))
        return None

    def print_examples(self, examples_print:list):
        print('********************************************************')
        print('***************         EXAMPLES         ***************')
        print('********************************************************')
        from src.utils import print_list as pl
        if len(examples_print) == 0:
            print("No examples to print")
        else:
            for idx,example in enumerate(examples_print):
                # Changing some representations
                example['out1'] = [utils.jdict_to_bin(outcome) for outcome in example['out1']]
                example['out2'] = [utils.jdict_to_bin(outcome) for outcome in example['out2']]
                self.scenario.profile = example['prof']
                profile = utils.prof_mset_bin(self.scenario)
                agr_msets1 = [utils.mset(agr_set) for agr_set in example['agr_msets1']][0]
                agr_msets2 = [utils.mset(agr_set) for agr_set in example['agr_msets2']][0]
                lows1 = example['lows1']
                lows2 = example['lows2']
                dum = utils.print_inits(self)
                # Printing results
                print('-----  EXAMPLE '+str(idx+1)+'    -----')
                print(dum['t1']+'  versus  '+dum['t2'])
                print('Profile:                '+pl(profile))
                print('Outcomes:               ' +pl(example['out1'])+' versus '+pl(example['out2']))
                # Agreement msets = { {agr(i,j) | i in voters} | for j in outs}
                print('Agr msets:              ' +pl(agr_msets1)+' versus '+pl(agr_msets2))
                # Average agreement = {sum({agr(i,j) | i in voters}) / n |for j in outs}
                print('Avg Agr:                '+pl(example['means1'])+' versus '\
                +pl(example['means2']))
                # Avg dist = {sum({Agr(i,j) - mean(Agr) | i in voters}) / n |for j in outs}
                print('Avg dist (Agr to avg):  '+pl(example['mean_dists1'])+' versus '\
                +pl(example['mean_dists2']))
                 # #(Agr < avg Agr) = { size({agr(i,j) | agr(i,j) < avg Agr}) |for j in outs}
                print('#(Agr < avg Agr):       '\
                +pl(example['nums_below1'])+' versus '+pl(example['nums_below2']))
                # Lowest agreements for outcome
                print('Agr low:                '+pl(lows1)+' versus '+pl(lows2))
                # Maxima of agr(i1,j) - agr(i2,j) for j in outs
                print('Agr dist high:          '+pl(example['greatest_difs1'])+' versus '\
                +pl(example['greatest_difs2']))
                print()
        return None


