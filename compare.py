from src import Scenario
from src import CompareRules
from src import BFSolver
from src import ASPSolver
import src.utils as utils
import itertools, argparse


# Add parser.
parser = argparse.ArgumentParser()
# Arguments for scenario.
parser.add_argument('--path_scen', type=str, default="./jaggs/sc01_JVC.jagg", help='Rel dir to .jagg file for reduced scenario.')
parser.add_argument('--num_judges', type=int, default=15, help='Number of judgements/judges that are contained in every profile.')
parser.add_argument('--show_nums_consistent', type=bool, default=1, help='Show number of consistent and antipodal judgements (0/1 for False/True).')
parser.add_argument('--show_judgements_consistent', type=bool, default=0, help='Show rational and feasible judgements (0/1 for False/True).')
# Arguments for initialising comparison object.
parser.add_argument('--solver1', type=str, default="bf", help='Solver method. options: "bf" (BFS), "asp" (ASP solver).')
parser.add_argument('--rule1', type=str, default="kemeny",
        help='Options: "kemeny", "kemeny-original", "kemnash", "lamb-kemnash". For ASP also saturation versions as "X-sat" (e.g, "kemeny-sat")')
parser.add_argument('--lamb1', type=float, default=0, help='value of \u03BB parameter, rule is lamb-kemnash or lamb-kemnash-sat ')
parser.add_argument('--solver2', type=str, default="bf", help='Solver method. options: "bf" (BFS), "asp" (ASP solver).')
parser.add_argument('--rule2', type=str, default="kemnash", help='Rule used by solver2, options same as for rule1.')
parser.add_argument('--lamb2', type=float, default=0, help='value of \u03BB parameter, rule is lamb-kemnash or lamb-kemnash-sat ')
# Arguments for results that are produced / printed.
parser.add_argument('--sample', type=int, default=0, help='Number of profiles in every iteration.')
parser.add_argument('--simulate', type=int, default=40000000, help='If total number of profiles exceeds this number, profile is simulated.')
parser.add_argument('--all_examples', type=int, default=0, help='If False only when outcomes differ (0/1 for False/True).')
parser.add_argument('--num_examples', type=int, default=0, help='Maximal number of examples that is printed.')
parser.add_argument('--time_analysis', type=int, default=1, help='If True execution time is part of the (comparison) analysis (0/1 for False/True).')
parser.add_argument('--show_result', type=int, default=1, help='If True, the result are printed (0/1 for False/True).')
args = parser.parse_args()

# Initialise the scenario object
reducedScen = Scenario()
# Load the reduced scenario.
reducedScen.load_from_file(args.path_scen, args.num_judges)
# Show consistent judgments
in_consistent = reducedScen.in_consistent
out_consistent = reducedScen.out_consistent
if args.show_nums_consistent:
    num_in = len(in_consistent)
    num_out = len(out_consistent)
    num_antipodal_in = utils.count_consistentOpp(in_consistent)
    num_antipodal_out = utils.count_consistentOpp(out_consistent)
    print("There are "+str(num_in)+" rational (allowed individual) judgements"
            +" cotaining "+str(num_antipodal_in)+" PAIRS of antipodal judgements.")
    print("There are "+str(num_out)+" feasible (allowed collective) judgements"\
            +" cotaining "+str(num_antipodal_out)+" PAIRS of antipodal judgements.")
if args.show_judgements_consistent:
    print('The rational judgements are:')
    print(utils.print_list([utils.jdict_to_bin(jdict) for jdict in in_consistent]))
    print('The feasible judgements are:')
    print(utils.print_list([utils.jdict_to_bin(jdict) for jdict in out_consistent]))
# Initialising comparison object
comparison = CompareRules(reducedScen, args.solver1, args.rule1, args.lamb1, args.solver2,
            args.rule2, args.lamb2)
result = comparison.result(args.all_examples, args.num_examples, args.sample, 
                args.time_analysis, args.show_result, args.simulate)