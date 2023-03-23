######################################################################
## Useful python classes for the scenarios and the possible solvers.
## Originally from JAGGPY package, minor modifications.
#################################################################

# A scenario class that will allow us to create a scenario object by loading
# information from a .jagg file. A scenario has an agenda, input constraints,
# output constraints and a profile.

from abc import ABC, abstractmethod
from itertools import islice
from nnf import Var, Or, And  # pylint: disable=unused-import
from .parser import Parser 
import src.utils as utils
import time



class Scenario:
    """A Scenario object has the following properties:
            - variables: a list of occurring variables
            - agenda: a dictionary with numbers as keys and
                formulas as values
            - input_constraints: a list of input constraints
            - output_constraints: a list of output constraints
            - profile: a list of judgment sets
            - number_voters: an integer specifying the number of voters
            """
    def __init__(self):
        """A Scenario object has the following properties:
            - variables: a list of occurring variables
            - agenda: a dictionary with numbers as keys and
                formulas as values
            - input_constraints: a list of input constraints
            - output_constraints: a list of output constraints
            - profile: a list of judgment sets
            - number_voters: an integer specifying the number of voters
            - in_consistent: list with all rational judgement dictionaries
            - out_consistent: list with all feasible judgement dictionaries.
            """
        self.agenda = {}
        self.variables = []
        self.input_constraints = []
        self.output_constraints = []
        self.profile = []
        self.number_voters = 0
        # Added attributes (to prevent recomputation in profile iteration)
        self.in_consistent = {}
        self.out_consistent = {}
        self.num_profs = 0

    def load_from_file(self, path, num_voters=None):
        # Num_voters is added variable; with profile iteration you do not need
        # specify jagg file for every size anymore
        """Load the scenario from a .jagg file given its path.
        The path should be a raw string, i.e. of the form r"path/to/file".
        The file should have the following format, with each element being on
        a new line:
            - var_1,..., var_n: list of all the variables
            - Number of Formulas: The number of formulas in the pre-agenda
            - X, Formula: The formula labeled by the number X
            - In, Formula: The input constraint labeled by the text "In"
            - Out, Formula: The output constraint labeled by the text "Out"
            - Number of voters, Number of distinct judgment sets
            - J, l1;...;ln: A list of the labels of the formulas
                that are accepted. The rest is rejected.
                This profile occurs J times. The formulas should be
                given by the times they are selected and seperated
                by a semicolon. For example, "4, 2;4;5".
        A formula can contain the following operators:
            - The OR operator |
            - The AND operator &
            - The NOT operator ~
            - The IMPLIES operator ->
        Parentheses can be omitted where clear from context. """
        # Read the file and split all lines
        with open(path, encoding='utf-8') as conn:
            text = conn.read()
            lines = text.splitlines()

        # Remove blank lines and comments from the lines
        lines = [line for line in lines if line != "" and line[0] != "#"]

        # Create a parser object for future use
        parser = Parser()

        # Add the VARIABLES to the scenario
        # var_prefix is changed and it is explicitly checked that none of the 
        # Modified._
        var_prefix = "_"
        self.variables = lines[0].split(", ")
        # Modified: added.
        for var in self.variables:
            if var in var_prefix:
                raise Exception ("Variables and var_prefix incompatible")
        formula_def = f'({self.variables[0]} | ~{self.variables[0]})'

        # Add the formulas to the AGENDA dictionary using the given label
        number_of_formulass = int(lines[1])
        for i in range(2, number_of_formulass+2):
            current_line = lines[i].split(", ")
            label = int(current_line[0])
            formula = current_line[1]
            self.agenda[label] = parser.to_nnf(formula)

        # Update what variables appear in the scenario.
        all_variables = []
        for var in self.variables:
            all_variables.append(var)
        for label in self.agenda.keys():
            all_variables.append(f'l{label}')

        # Add the INPUT CONSTRAINT to the list of constraints
        line_number = number_of_formulass+2
        while lines[line_number].split(", ")[0] == "In":
            formula = lines[line_number].split(", ")[1]
            if formula == "":
                formula = formula_def
            self.input_constraints.append(parser.to_nnf(formula))
            line_number += 1

        # Add the OUTPUT CONSTRAINTS to the list of constraints
        while len(lines) != line_number and lines[line_number].split(", ")[0] == "Out":
            formula = lines[line_number].split(", ")[1]
            if formula == "":
                formula = formula_def
            self.output_constraints.append(parser.to_nnf(formula))
            line_number += 1

        # Consturct the CONSISTENT judgement
        # Translated agenda: issues are represented by their labels.
        translated_agenda = parser.translate_agenda(self.agenda)

        # Convert constraints to strings
        in_string = ""
        out_string = ""
        for conjunct in self.input_constraints:
            in_string += f'({conjunct}) & '
        for conjunct in self.output_constraints:
            out_string += f'({conjunct}) & '
        for conjunct in translated_agenda:
            in_string += f'({conjunct}) & '
            out_string += f'({conjunct}) & '
        # Add constraint of completeness
        for var in all_variables:
            in_string += f"({var} | ~{var}) & "
            out_string += f"({var} | ~{var}) & "
        in_string = in_string[:-3]
        out_string = out_string[:-3]

        # Preprocess the string representing the scenario.
        in_string_prepro = in_string
        out_string_prepro = out_string
        for var in all_variables:
            in_string_prepro = in_string_prepro.replace(var, var_prefix + var)
            out_string_prepro = out_string_prepro.replace(var, var_prefix + var)
        # If more than ten variables this goes wrong, following fix:
        in_string_prepro = in_string_prepro.replace(var_prefix + var_prefix, var_prefix)
        out_string_prepro = out_string_prepro.replace(var_prefix + var_prefix, var_prefix)
        for var in all_variables:
            exec(f"{var_prefix}{var} = Var('{var}')")
        in_constraint = eval(in_string_prepro)
        out_constraint = eval(out_string_prepro)
        if not in_constraint.consistent():
            raise Exception ("The input constraints are inconsistent")
        if not out_constraint.consistent():
            raise Exception ("The output constraints are inconsistent")

        # List all the models that are consistent with the output constraints.
        self.in_consistent = self.clean_outcome(list(in_constraint.models()))
        self.out_consistent = self.clean_outcome(list(out_constraint.models()))
        in_consistent_bin = [utils.jdict_to_bin(jdict) for jdict in self.in_consistent]
        out_consistent_bin = [utils.jdict_to_bin(jdict) for jdict in self.out_consistent]

        # Add the number of voters to the scenario
        # If profile iteration we only add num_voters and we are done.
        if num_voters != None:
            self.number_voters = num_voters
        else:
            self.number_voters += int(lines[line_number].split(", ")[0])

            # Add every (occurence, js)-pair to the profile dictionary
            number_of_js = int(lines[line_number].split(", ")[1])
            for i in range(line_number+1, line_number+number_of_js+1):
                current_line = lines[i].split(", ")
                # If the list of accepted formulas is not empty continue
                if current_line[1] != '':
                    label = int(current_line[0])
                    formula_labels = list(map(int, current_line[1].split(";")))
                    js = []
                    for formula_label in formula_labels:
                        js.append(self.agenda[formula_label])
                    # Check if js is consistent with constraints
                    if utils.js_to_bin(self, js) not in in_consistent_bin:
                        raise Exception (f"The judgment set on line {i} is inconsistent"\
                            " with the input constraints.")
                    # Add the judgment set to the scenario
                    self.profile.append([label, js]) 
                else:
                    # If the all issues are rejected, add the empty list
                    # label line is added; previously the wrong label was taken
                    label = int(current_line[0])
                    self.profile.append([label, []]) 
        # Add number of profiles.
        self.num_profs = utils.multiset_coefficient(len(self.in_consistent), self.number_voters)

    def clean_outcome(self, outcomes):
        for i, outcome in enumerate(outcomes):
            translated_outcomes = {}
            for formula in outcome.keys():
                if formula[0] == 'l':
                    # original: label = int(formula[1]) [wrong if num issues > 9]
                    label = int(formula[1:])
                    translation = self.agenda[label]
                    translated_outcomes[translation] = outcome[formula]
            outcomes[i] = utils.order_dict(self, translated_outcomes)
        # Remove duplicates from outcomes.
        final = [dict(t) for t in {tuple(outcome.items()) for outcome in outcomes}]
        return final

    def pretty_repr(self):
        """Returns string that represents the scenario object in a readable way"""
        scenario_string = "Variables:"
        for variable in self.variables:
            scenario_string += f"\n{variable}"
        scenario_string += "\n\nAgenda (label, formula):"
        for key in self.agenda:
            scenario_string += f"\n{key}, {self.agenda[key]}"
        scenario_string += "\n\nInput constraints:"
        for constraint in self.input_constraints:
            scenario_string += f"\n{constraint}"
        scenario_string +=  "\n\nOutput constraints:"
        for constraint in self.output_constraints:
            scenario_string += f"\n{constraint}"
        scenario_string += "\n\nProfile (times selected, accepted formulas):"
        for judgment_set in self.profile:
            accepted = "("
            for variable in judgment_set[1]:
                if accepted == "(":
                    accepted += variable
                else:
                    accepted += ", " + variable
            accepted += ")"
            scenario_string += (f"\n{judgment_set[0]}, " + accepted)
        return scenario_string

# A solver class with an enumerate_outcomes function that enumerates
# all the outcomes given a scenario and an aggregation rule.
class Solver(ABC):
    """The abstract class for solvers."""
    @abstractmethod
    def all_outcomes(self, scenario, rule):
        """Given a scenario and an aggregation rule, yields a generator
        with the corresponding outcomes."""

    def outcomes(self, scenario, rule, num=1):
        """Given a scenario, an aggregation rule and an integer `num`,
        yields the first `num` corresponding outcomes."""
        return islice(self.all_outcomes(scenario, rule), num)

