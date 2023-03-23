from src import Scenario
from src import Compare_Kemnash
import src.utils as utils
import matplotlib.pyplot as plt
import itertools, argparse, os, time, sys

l = [0, .01, .05, .1, .15, .25, .35, .45, .55]
l0 = [0]
l1 = [.01]
l2 = [.05]
l3 = [.1]
l4 = [.15]
l5 = [.25]
l6 = [.35]
l7 = [.45]
l8 = [.55]
lOdd = l[::2]
lEven = l[1::2]
lTrip = l[::3]
lEnds = l[::8]
lamb_dict = {
    'l':l,'l0':l0,'l1':l1,'l2':l2,'l3':l3,'l4':l4 ,'l5':l5 ,'l6':l6 ,'l7':l7,'l8': l8,'lOdd':lOdd,'lEven':lEven,
    'lTrip':lTrip, 'lEnds':lEnds}

# PARSER.
parser = argparse.ArgumentParser()
# Arguments for scenario.
parser.add_argument('--sc', type=int, default=None)
parser.add_argument('--path_scen', type=str, default="./jaggs/sc01_JVC.jagg", help='Path to .jagg file for reduced scenario.')
parser.add_argument('--num_judges', type=int, default=15, help='Number of judgements/judges that are contained in every profile.')
# Arguments for initialising comparison object.
parser.add_argument('--lambs', type=str, default='l', help='Key of lambda list in lamb_dicts.')
parser.add_argument('--sample', type=int, default=250000, help='Number of profiles in every iteration.')
# Plots
parser.add_argument('--show_plots', type=int, default=0, help='If True plot is shown (1/0 for True/False).')
parser.add_argument('--save_plots', type=int, default=0, help='If True plots saved (1/0 for True/False).')
parser.add_argument('--plot_folderDir', type=str, default="construct", help='Absolute dir of folder in which plot is saved.')
# Auxiliary 
parser.add_argument('--verbose', type=int, default=1, help='If True all result values are printed (1/0 for True/False).')
args = parser.parse_args()

# SCENARIO.
if args.sc == None:
    path = args.path_scen
    name = "{}".format(args.path_scen[8:-5])
# Convenient way for pre-defined scenarios.
elif args.sc == 1:
    path = "./jaggs/sc01_JVC.jagg"
    name = "sc01"
elif args.sc == 2:
    path = "./jaggs/sc02_PA3.jagg"
    name = "sc02"
elif args.sc == 3:
    path = "./jaggs/sc03_CM.jagg"
    name = "sc03"
elif args.sc == 4:
    path = "./jaggs/sc04_SDC.jagg"
    name = "sc04"
elif args.sc == 5:
    path = "./jaggs/sc05_PA4.jagg"
    name = "sc05"
elif args.sc == 6:
    path = "./jaggs/sc06_GR.jagg"
    name = "sc06"
elif args.sc == 7:
    path = "./jaggs/sc07_PL3.jagg"
    name = "sc07"
elif args.sc == 8:
    path = "./jaggs/sc08_PL4.jagg"
    name = "sc08"
elif args.sc == 9:
    path = "./jaggs/sc09_PL6.jagg"
    name = "sc09"
else:
    path = "./jaggs/sc10_PL7.jagg"
    name = "sc10"


scen = Scenario()
# scen.load_from_file(args.path_scen, args.num_judges)
scen.load_from_file(path, args.num_judges)
# Get result dictionary
lambs = lamb_dict[args.lambs]
result = Compare_Kemnash(scen, lambs, args.sample).result()
symdif_, solprof_, qual_, lamb_, ze_ = [], [], [], [], []
for label in result:
    if label[:6] == 'symdif':
        symdif_.append(["{:.5f}".format(ele) for ele in result[label]])
    elif label[:8] == 'sol/prof':
        solprof_.append(["{:.5f}".format(ele) for ele in result[label]])
    elif label[0] == 'R':
        qual_.append(["{:.5f}".format(ele) for ele in result[label]])
    elif label[-2:] == 'KN':
        lamb_.append(["{:.5f}".format(ele) for ele in result[label]])
    elif label == 'ZE':
        ze_.append(["{:.5f}".format(ele) for ele in result[label]])
    

if args.verbose:
    print('**SYMDIFS: KKN KMH KME KNMH KNME**')
    for ele in symdif_:
        print(str(ele)[1:-1])
    print('**SOLPROFS: K KN MH ME**')
    for ele in solprof_:
        print(str(ele)[1:-1])
    print('**QUAL: meanKN meanMH meanME lowK lowKN mdK mdKN**')
    for ele in qual_:
        print(str(ele)[1:-1])
    print('**ZE**')
    for ele in ze_:
        print(str(ele)[1:-1])

if args.save_plots == args.show_plots == 0:
    sys.exit()

if args.save_plots:
    # Construct name for plot.
    if args.plot_folderDir == "construct":
        plot_folderDir = os.path.abspath(os.getcwd())+'/Plots/'+name
    else:
        plot_folderDir = args.plot_folderDir
    if args.sample > scen.num_profs:
        sname = "all"
    elif args.sample == 250000:
        sname = "S1"
    elif args.sample == 500000:
        sname = "S2"
    elif args.sample == 1000000:
        sname = "S3"
    elif args.sample == 1500000:
        sname = "S4"
    elif args.sample == 2000000:
        sname = "S5"
    else:
        sname = "s{}".format(args.sample)
    nameSymdif = "{}-symd-n{:.0f}-{}-{}.png".format(name, scen.number_voters, sname, args.lambs)
    nameSolprof = "{}-sol-n{:.0f}-{}-{}.png".format(name, scen.number_voters, sname, args.lambs)
    nameQual = "{}-qual-n{:.0f}-{}-{}.png".format(name, scen.number_voters, sname, args.lambs)
    nameLamb = "{}-lamb-n{:.0f}-{}-{}.png".format(name, scen.number_voters, sname, args.lambs)
    nameZE = "{}-ze-n{:.0f}-{}-{}.png".format(name, scen.number_voters, sname, args.lambs)
    
    # Create full directory for plot.
    dir_plotSymdif = plot_folderDir+'/'+nameSymdif
    dir_plotSolprof = plot_folderDir+'/'+nameSolprof
    dir_plotQual = plot_folderDir+'/'+nameQual
    dir_plotLamb = plot_folderDir+'/'+nameLamb
    dir_plotZE = plot_folderDir+'/'+nameZE
    # Create folder directory if it doesn't exist.
    if not os.path.exists(plot_folderDir):
        os.makedirs(plot_folderDir)

# PLOTS.
# Symmetric Difference.
fig, ax = plt.subplots(1)
ax.plot(lambs, result['symdifKemKN'], color="purple", linewidth=1, linestyle="-")
ax.plot(lambs, result['symdifKemMaxham'], color="gray",linewidth=1, linestyle="-")
ax.plot(lambs, result['symdifKemMaxeq'], color="gray",linewidth=1, linestyle="--")
ax.plot(lambs, result['symdifKN-Maxham'], color="brown",linewidth=1, linestyle="-")
ax.plot(lambs, result['symdifKN-Maxeq'], color="brown",linewidth=1, linestyle="--")
if args.save_plots:
    plt.savefig(dir_plotSymdif, format='png')
if args.show_plots:
    plt.show()
# Collective judgements per profile
fig, ax = plt.subplots(1)
ax.plot(lambs, result['sol/profKem'], color="blue", linewidth=1, linestyle="-")
ax.plot(lambs, result['sol/profKN'], color="orange",linewidth=1, linestyle="-")
ax.plot(lambs, result['sol/profMaxham'], color="black",linewidth=1, linestyle="-")
ax.plot(lambs, result['sol/profMaxeq'], color="red",linewidth=1, linestyle="-")
if args.save_plots:
    plt.savefig(dir_plotSolprof, format='png')
if args.show_plots:
    plt.show()
# Qualitative.
fig, ax = plt.subplots(1)
ax.plot(lambs, result['R-meanKN'], color="blue", linewidth=1, linestyle="-")
ax.plot(lambs, result['R-meanMaxham'], color="blue", linewidth=1, linestyle="--")
ax.plot(lambs, result['R-meanMaxeq'], color="blue", linewidth=1, linestyle="-.")
ax.plot(lambs, result['R-lowKem'], color="black", linewidth=1, linestyle=":")
ax.plot(lambs, result['R-lowKN'], color="black", linewidth=1, linestyle="-")
ax.plot(lambs, result['R-maxdistKem'], color="red", linewidth=1, linestyle=":")
ax.plot(lambs, result['R-maxdistKN'], color="red", linewidth=1, linestyle="-")
if args.save_plots:
    plt.savefig(dir_plotQual, format='png')
if args.show_plots:
    plt.show()
# Lambda
fig, ax = plt.subplots(1)
ax.plot(lambs, result['meanKN'], color="blue", linewidth=1, linestyle="-")
ax.plot(lambs, result['lowKN'], color="black", linewidth=1, linestyle="-")
ax.plot(lambs, result['maxdistKN'], color="red", linewidth=1, linestyle="-")
if args.save_plots:
    plt.savefig(dir_plotLamb, format='png')
if args.show_plots:
    plt.show()
# Zero-effect
fig, ax = plt.subplots(1)
ax.plot(lambs, result['ZE'], color="green", linewidth=1, linestyle="-")
if args.save_plots:
    plt.savefig(dir_plotZE, format='png')
if args.show_plots:
    plt.show()