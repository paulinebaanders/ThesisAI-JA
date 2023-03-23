% We first add the scenario to our ASP program.

% Adding the labels that represent the issues.
issue(l1).
issue(l2).
issue(l3).
issue(l4).

% Adding voters and specifying how they voted.
voter(1..15).
js(1,l1;-l2;l3;-l4).
js(2,l1;-l2;l3;-l4).
js(3,l1;-l2;l3;-l4).
js(4,l1;-l2;-l3;l4).
js(5,-l1;l2;-l3;l4).
js(6,-l1;l2;-l3;l4).
js(7,-l1;l2;-l3;l4).
js(8,-l1;-l2;l3;-l4).
js(9,-l1;-l2;l3;-l4).
js(10,-l1;l2;l3;-l4).
js(11,-l1;l2;l3;-l4).
js(12,l1;l2;-l3;-l4).
js(13,l1;l2;-l3;-l4).
js(14,l1;l2;-l3;-l4).
js(15,l1;l2;-l3;-l4).

% Declare input constraints (in CNF)
inputClause(1, aa57e).
inputClause(1, x1).
inputClause(2, aa57e).
inputClause(2, x2).
inputClause(3, -x1).
inputClause(3, l1).
inputClause(4, -aa57e).
inputClause(4, -x1).
inputClause(4, -x2).
inputClause(5, -a3e89).
inputClause(5, -x1).
inputClause(5, -x3).
inputClause(6, -l2).
inputClause(6, x2).
inputClause(7, a3e89).
inputClause(7, x3).
inputClause(8, -l1).
inputClause(8, x1).
inputClause(9, x3).
inputClause(9, -l3).
inputClause(10, -x2).
inputClause(10, l2).
inputClause(11, a3e89).
inputClause(11, -x4).
inputClause(12, a3e89).
inputClause(12, x1).
inputClause(13, x4).
inputClause(13, -l4).
inputClause(14, -x3).
inputClause(14, l3).
inputClause(15, l4).
inputClause(15, -x4).
inputClause(16, -x3).
inputClause(16, aa57e).

% Declare output constraints (in CNF)
outputClause(1, -x3).
outputClause(1, l3).
outputClause(2, a5048).
outputClause(2, x1).
outputClause(3, -x1).
outputClause(3, l1).
outputClause(4, a5048).
outputClause(4, x3).
outputClause(5, -l2).
outputClause(5, x2).
outputClause(6, a5048).
outputClause(6, -x4).
outputClause(7, a7d32).
outputClause(7, x2).
outputClause(8, -l1).
outputClause(8, x1).
outputClause(9, x3).
outputClause(9, -l3).
outputClause(10, -a5048).
outputClause(10, -x1).
outputClause(10, -x3).
outputClause(11, -x2).
outputClause(11, l2).
outputClause(12, -a7d32).
outputClause(12, -x1).
outputClause(12, -x2).
outputClause(13, x4).
outputClause(13, -l4).
outputClause(14, -x3).
outputClause(14, a7d32).
outputClause(15, l4).
outputClause(15, -x4).
outputClause(16, a7d32).
outputClause(16, x1).

variable(aa57e).
variable(a3e89).
variable(l1).
variable(x4).
variable(l2).
variable(x3).
variable(l3).
variable(a5048).
variable(l4).
variable(x2).
variable(a7d32).
variable(x1).

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

% determine the Hamming distance from each voter's judgment set to the outcome
dist(V,D) :- voter(V), D = #count { X : ilit(X), js(col,X), js(V,-X) }.
agr(V,C) :- numissues(N), voter(V), dist(V,D), C = N-D.
% sum the distances over all voters
agr_sum(1,C) :- agr(1,C).
agr_sum(V,C) :- V1 = V-1, agr_sum(V1,C1), agr(V,C2), C = C1+C2.
agr_sum(C) :- agr_sum(N,C), numvoters(N).
% maximize cumulated sum of agreements
#maximize { C@10,agr_sum(C) : agr_sum(C) }.


