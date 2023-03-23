#####################################################################
## The ASP solver that uses the given rule to give back the
## outcome of the judgment aggregation. We use clingo to find the
## correct answer sets.
#####################################################################

import textwrap, clingo, time
from fractions import Fraction
from .classes import Solver
from .parser import Parser
import src.utils as utils
import src.asp_rules as asp_rules

class ASPSolver(Solver):
    """A solver that uses Answer Set Programming to compute outcomes."""
    def __init__(self, binrep=False, print_asp=False):
        self.opt = False
        self.binrep = binrep

    def all_outcomes(self, scenario, rule, lamb=0):
        """Given a scenario object and the name of a rule
        this function will yield the outcomes
        of the judgment aggregation. Each outcome is yielded seperately.
        The rule should be given as a string and can be one of the
        following lowercase commands:
            - kemeny                (using optimisation - based on Kemeny JAGGPY)
            - kemnash               (using optimisation - borrows from Kemeny JAGGPY)
            - lamb-kemnash          (using optimisation - borrows from Kemeny JAGGPY)
            - kemeny-sat            (saturation technique - based on Kemeny JA-ASP)
            - kemnash-sat           (saturation technique - based on Kemeny JA-ASP)
            - lamb-kemnash-sat      (saturation technique - based on Kemeny JA-ASP)
            - kemeny-original       (Kemeny with optimisation from JAGGPY)
            - kemeny-original-sat   (Kemeny with saturation from JA-ASP package)
        """
        # Make sure that Solver is not in optimisation mode
        self.opt = False
        t0 = time.time()
        # Give a warning if scenario does not include profile
        if scenario.profile == []:
            raise Exception ("The scenario does not include a profile")
            
        parser = Parser()

        # Create a list of all variables in the scenario. REMOVED IN SEP
        all_variables = set()
        for var in scenario.variables:
            all_variables.add(var)

        # Add the scenario to the asp_program using the scenario argument.
        asp_program = textwrap.dedent("""% We first add the scenario to our ASP program.
        """)

        # Adding issues.
        asp_program += textwrap.dedent("""
        % Adding the labels that represent the issues.
        """)
        for key in scenario.agenda:
            asp_program += f"issue(l{key}).\n"
            all_variables.add(f"l{key}")

        # Adding voters and judgment sets.
        asp_program += textwrap.dedent("""
        % Adding voters and specifying how they voted.
        """)
        voter_count = 0
        for coalition in scenario.profile:
            for voter_index in range(1,coalition[0]+1):
                # Register new voter.
                voter = str(voter_count + voter_index)
                asp_program += f"voter({voter}).\n"
                # Register how they voted for each issue.
                for label in scenario.agenda:
                    if scenario.agenda[label] in coalition[1]:
                        asp_program += f"js({voter},l{label}).\n"
                    else:
                        asp_program += f"js({voter},-l{label}).\n"
            voter_count += coalition[0]

        # Adding input constraints.
        asp_program += "\n% Declare input constraints (in CNF)\n"
        total_input_constraints = ""

        # Compound separate constraints into one.
        for conjunct in scenario.input_constraints:
            total_input_constraints += f"{conjunct} & "

        # Add auxiliary input constraints that guarantee that labels
        # correspond to the right formulas.
        for constraint in parser.translate_agenda(scenario.agenda):
            total_input_constraints += f"({constraint}) & "
        total_ic = total_input_constraints[:-3]

        # Translate the constraint to CNF.
        cnf_object = parser.to_cnf(total_ic, all_variables)
        ic_cnf = cnf_object[0]
        all_variables = all_variables.union(cnf_object[1])

        # Adding the input constraint clauses to the program.
        conjuncts = ("".join(ic_cnf.split())).split("&")
        clause_number = 1
        for clause in conjuncts:
            prep_clause = "".join(clause.split("("))
            prep_clause = "".join(prep_clause.split(")"))
            conjunct = prep_clause.split("|")
            for string in conjunct:
                if string[0] == "(":
                    formula = string[1:]
                elif string[-1] == ")":
                    formula = string[:-1]
                else:
                    formula = string
                if formula[0] == "~":
                    asp_program += f'inputClause({clause_number}, -{formula[1:]}).\n'
                else:
                    asp_program += f'inputClause({clause_number}, {formula}).\n'
            clause_number += 1

        # Adding output constraints.
        asp_program += "\n% Declare output constraints (in CNF)\n"
        total_output_contstraints = ""

        # Compound separate constraints into one.
        for conjunct in scenario.output_constraints:
            total_output_contstraints += f"{conjunct} & "

        # Add auxiliary input constraints that guarantee
        # that labels correspond to the right formulas.
        for constraint in parser.translate_agenda(scenario.agenda):
            total_output_contstraints += f"({constraint}) & "
        total_oc = total_output_contstraints[:-3]

        # Translate the constraint to CNF.
        cnf_object = parser.to_cnf(total_oc, all_variables)
        oc_cnf = cnf_object[0]
        all_variables = all_variables.union(cnf_object[1])

        # Adding the output constraint clauses to the program.
        conjuncts = ("".join(oc_cnf.split())).split("&")
        clause_number = 1
        for clause in conjuncts:
            prep_clause = "".join(clause.split("("))
            prep_clause = "".join(prep_clause.split(")"))
            conjunct = prep_clause.split("|")
            for string in conjunct:
                if string[0] == "(":
                    formula = string[1:]
                elif string[-1] == ")":
                    formula = string[:-1]
                else:
                    formula = string
                if formula[0] == "~":
                    asp_program += f'outputClause({clause_number}, -{formula[1:]}).\n'
                else:
                    asp_program += f'outputClause({clause_number}, {formula}).\n'
            clause_number += 1

        # Declare variables.
        asp_program += '\n'
        for variable in all_variables:
            asp_program += f'variable({variable}).\n'

        # Add the consistency checks for the input and output constraints.
        # ja.py from JA-ASP (modified)
        asp_program += textwrap.dedent("""
        % generate literals over all issues
        ilit(X;-X) :- issue(X).
        lit(X) :- ilit(X).
        % generate literals over all auxiliary variables
        lit(X;-X) :- variable(X).
        % auxiliary predicate for variables
        var(X) :- issue(X).
        % auxiliary predicates for counting/identifying issues, literals, voters
        numissues(N) :- N = #count { Z : issue(Z) }.
        issuenum(1..N) :- numissues(N).
        numilits(N) :- N = #count { Z : ilit(Z) }.
        ilitnum(1..N) :- numilits(N).
        numlits(N) :- N = #count { Z : lit(Z) }.
        litnum(1..N) :- numlits(N).
        numvars(N) :- N = #count { Z : var(Z) }.
        varnum(1..N) :- numvars(N).
        numvoters(N) :- N = #count { A : voter(A) }.
        voternum(1..N) :- numvoters(N).
        % auxiliary predicate for finding clauses
        inputClause(C) :- inputClause(C,_).
        outputClause(C) :- outputClause(C,_).
        % every voter is an agent
        agent(A) :- voter(A).
        % require that every agent has a judgment set
        % + completeness (& negation-freeness)
        1 { js(A,X); js(A,-X) } 1 :- agent(A), ilit(X).
        % The collective judgement must also specify acceptance of clauses
        1 { js(col,X); js(col,-X) } 1 :- lit(X).
        % constraint consistency (CNF)
        % individual judgements must be compatible with input clauses.
        :- agent(A), voter(A), inputClause(C), js(A,-L) : inputClause(C,L).
        % generate a collective outcome
        agent(col).
        % collective judgement must be compatible with output constriant.
        :- agent(col), outputClause(C,_), js(col,-L) : outputClause(C,L).
        % The outcome should only contain the literals that correspond to issues.
        outcome(X) :- agent(col), js(col,X), ilit(X).
        #show outcome/1.
        """)
        t1=time.time()

        # Add the ASP code corresponding to the rule that is to be executed.
        # Add the ASP code corresponding to the rule that is to be executed.
        if rule == "kemeny":
            self.opt = True
            asp_program += textwrap.dedent(asp_rules.kemeny())

        elif rule == "kemnash":
            if lamb > 0:
                warnings.warn("For nonzero values of \u03BB for use parameterised Kemeny-Nash rule, now \u03BB is set to 0.")
            self.opt = True
            self.opt = True
            asp_program += textwrap.dedent(asp_rules.kemnash(0))

        elif rule == "lamb-kemnash":
            self.opt = True
            asp_program += textwrap.dedent(asp_rules.kemnash(lamb))

        elif rule == "kemeny-sat":
            self.opt = False
            asp_program += textwrap.dedent(asp_rules.kemeny_sat())

        elif rule == "kemnash-sat":
            self.opt = False
            if lamb > 0:
                warnings.warn("For nonzero values of \u03BB, use "\
                    "parameterised Kemeny-Nash rule. Now \u03BB is set to 0.")
            asp_program += textwrap.dedent(asp_rules.kemnash_sat(0))

        elif rule == "lamb-kemnash-sat":
            self.opt = False
            asp_program += textwrap.dedent(asp_rules.kemnash_sat(lamb))

        elif rule == "kemeny-original":
            self.opt = True
            asp_program += textwrap.dedent(asp_rules.kemeny_original())

        elif rule == "kemeny-original-sat":
            self.opt = False
            asp_program += textwrap.dedent(asp_rules.kemeny_original_sat())

        else:
            raise Exception (f"{rule} is not a recognized aggregation rule.")

        t2 = time.time()
        print(asp_program)

        # Ground and solve the program.
        control = clingo.Control(arguments=["--project"])
        control.add("base", [], asp_program)
        t3 = time.time()
        print('t3-t2', t3-t2)
        print('t3-t0', t3-t0)
        control.ground([("base", [])])
        control.configuration.solve.models = 0
        if self.opt:
            control.configuration.solve.opt_mode = "optN"

        # Yield the results of the program.
        outcomes = []
        with control.solve(yield_=True) as handle:
            for m in handle:
                if self.opt:
                    if m.optimality_proven:
                        outcome =[str(atom)[8:-1] for atom in m.symbols(atoms=True) 
                            if str(atom)[:7] == 'outcome']
                        outcome_dict = {}
                        for label in scenario.agenda:
                            outcome_dict[scenario.agenda[label]] = False
                            if "l"+str(label) in outcome:
                                outcome_dict[scenario.agenda[label]] = True
                        outcomes.append(outcome_dict)
                else:
                    outcome =[str(atom)[8:-1] for atom in m.symbols(atoms=True) 
                        if str(atom)[:7] == 'outcome']
                    outcome_dict = {}
                    for label in scenario.agenda:
                        outcome_dict[scenario.agenda[label]] = False
                        if "l"+str(label) in outcome:
                            outcome_dict[scenario.agenda[label]] = True
                    outcomes.append(outcome_dict)
        outcomes = [dict(t) for t in {tuple(outcome.items()) for outcome in outcomes}]
        if self.binrep:
            outcomes = [utils.jdict_to_bin(d) for d in outcomes]
        t4= time.time()
        print('t4-t0',t4-t0)
        return outcomes