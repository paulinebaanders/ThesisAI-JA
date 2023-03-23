from fractions import Fraction
import textwrap

# Kemeny rule (using optimisation) 
# Borrows from implementation kemeny3-opt.lp in JA-ASP [License-(JA-ASP)] 
def kemeny():
    asp_program = """
        % determine the Hamming distance from each voter's judgment set to the outcome
        dist(V,D) :- voter(V), D = #count { X : ilit(X), js(col,X), js(V,-X) }.
        agr(V,C) :- numissues(N), voter(V), dist(V,D), C = N-D.
        % sum the distances over all voters
        agr_sum(1,C) :- agr(1,C).
        agr_sum(V,C) :- V1 = V-1, agr_sum(V1,C1), agr(V,C2), C = C1+C2.
        agr_sum(C) :- agr_sum(N,C), numvoters(N).
        % maximize cumulated sum of agreements
        #maximize { C@10,agr_sum(C) : agr_sum(C) }.
        """
    return asp_program

# Kemeny-Nash rule (using optimisation) 
# Borrows from implementation kemeny3-opt.lp in JA-ASP [License-(JA-ASP)]
def kemnash(lamb=0):
    # Convert lamb value to (integer) fraction. 
    lamb = list((Fraction(lamb).limit_denominator()).as_integer_ratio())
    asp_program = f"#const ln={lamb[0]}.\n"
    asp_program += textwrap.dedent(f"#const ld={lamb[1]}.\n")
    asp_program += textwrap.dedent("""
        % determine the Hamming distance from each voter's judgment set to the outcome
        dist(V,D) :- voternum(V), D = #count { X : ilit(X), js(col,X), js(V,-X) }.
        agr(V,C) :- numissues(N), voternum(V), dist(V,D), C = N-D.
        % lamb_agr encodes the non-zero agreement of voters
        agr_lamb(V,C) :- agr(V,C1), C1 > 0, C = C1*ld.
        agr_lamb(V,ln) :- agr(V,C1), C1 = 0.
        % 2-ary predicate to iteratively multiply Lambda agreements.
        agr_lamb_prod(1,C) :- agr_lamb(1,C), voternum(1).
        agr_lamb_prod(V,C) :- voternum(V), voternum(V1), V1 = V-1, agr_lamb_prod(V1,C1), agr_lamb(V,C2), C = C1*C2.
        % introduce 1-ary predicate to encode final product.
        agr_lamb_prod(C) :- agr_lamb_prod(N,C), numvoters(N).
        % maximize product of lambda agreements.
        #maximize { C@10,agr_lamb_prod(C) : agr_lamb_prod(C) }.""")
    return asp_program

# Kemeny rule (using saturation) 
# Based on implementation kemeny.lp in JA-ASP [License-(JA-ASP)]
# use the technique of saturation (from Eiter & Gottlob 1995) 
def kemeny_sat():
    asp_program = """
        % Kemeny rule with saturation
        w :- not w.
        virtual(X) :- lit(X), w. 
        % guess a virtual assignment (issues and variables from clauses)
        virtual(X) ; virtual(-X) :- variable(X).
        % remove virtual assignments that are contradictory
        w :- variable(X), virtual(X), virtual(-X).
        % remove virtual assignments that don't satisfy output constraint
        w :- outputClause(C), virtual(-L) : outputClause(C,L).

        % order the variables alphabetically.
        1 { varorder(X,O) : varnum(O) } 1 :- var(X).
        1 { varorder(X,O) : var(X) } 1 :- varnum(O).
        :- varorder(X1,O1), varorder(X2,O2), X1 < X2, O1 > O2.

        % order the voters alphabetically.
        1 { voterorder(V,O) : voternum(O) } 1 :- voter(V).
        1 { voterorder(V,O) : voter(V) } 1 :- voternum(O).
        :- voterorder(V1,O1), voterorder(V2,O2), V1 < V2, O1 > O2.

        % compute the agreement with the virtual assignment for every voter.
        virtagr(0,N,0) :- voternum(N).
        % For agreement only the issue literals are relevant.
        % If virtual and voter both accept.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,D), C = D + 1, virtual(X), js(V,X), ilit(X).
        % If virtual accepts and voter rejects.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,C), virtual(X), js(V,-X), ilit(X).
        % If virtual and voter both reject.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,D), C = D + 1, virtual(-X), js(V,-X), ilit(X).
        % If virtual rejects and voter accepts.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,C), virtual(-X), js(V,X), ilit(X).

        % Add 2-ary predicate to encode the total agreement for each voter.
        virtagr(Vn,C) :- virtagr(NI,Vn,C), numissues(NI).
        % Introduce 2-ary predicate to encode sum of agreement scores.
        virtagr_sum(1,C) :- virtagr(1,C).
        virtagr_sum(V,C) :- V1 = V - 1, virtagr_sum(V1,C1), virtagr(V,C2), C = C1 + C2.         

        % Make predicate for final virtual agreement
        virtagr(C) :- virtagr_sum(N,C), numvoters(N).           

        % Saturate all virtual/1, virtagr/3, virtagr/2, virtagr_prod/2 in case w 
        % is derived.
        virtual(X) :- w, lit(X).
        virtagr(Xn,Vn,0..C) :- w, varnum(Xn), voternum(Vn), numvars(M), C = M + 1. 
        virtagr(Vn,0..C) :- w, voternum(Vn), numvars(M), C = M + 1.
        virtagr_sum(Vn,0..C) :- w, voternum(Vn), numvoters(M), C = M + 1.         

        % compute the agreement between the collective assignment and the profile.
        agr(V,C) :- voter(V), C = #count { X : ilit(X), js(col,X), js(V,X) }.
        % calculate collective agreement.
        colagr(C) :- C = #sum { C1,agr(V,C1) : agr(V,C1) }.            

        % remove virtual assignments that have agreement that is weakly smaller than 
        % agreement of collective decision.
        w :- virtagr(C1), colagr(C2), C1 <= C2."""
    return asp_program

# Kemeny-Nash rule (using saturation)
# Based on implementation kemeny.lp in JA-ASP [License-(JA-ASP)]
def kemnash_sat(lamb=0):
    # Convert lamb value to (integer) fraction. 
    lamb = list((Fraction(lamb).limit_denominator()).as_integer_ratio())
    asp_program = f"#const ln={lamb[0]}.\n"
    asp_program += textwrap.dedent(f"#const ld={lamb[1]}.\n")
    asp_program += textwrap.dedent("""
        % use the technique of saturation (see Eiter & Gottlob '95)
        w :- not w.
        virtual(X) :- lit(X), w. 
        % guess a virtual assignment (issues and variables from clauses)
        virtual(X) ; virtual(-X) :- variable(X).
        % remove virtual assignments that are contradictory
        w :- variable(X), virtual(X), virtual(-X).
        % remove virtual assignments that don't satisfy output constraint
        w :- outputClause(C), virtual(-L) : outputClause(C,L).

        % order the variables alphabetically.
        1 { varorder(X,O) : varnum(O) } 1 :- var(X).
        1 { varorder(X,O) : var(X) } 1 :- varnum(O).
        :- varorder(X1,O1), varorder(X2,O2), X1 < X2, O1 > O2.

        % order the voters alphabetically.
        1 { voterorder(V,O) : voternum(O) } 1 :- voter(V).
        1 { voterorder(V,O) : voter(V) } 1 :- voternum(O).
        :- voterorder(V1,O1), voterorder(V2,O2), V1 < V2, O1 > O2.

        % compute the agreement with the virtual assignment for every voter.
        virtagr(0,N,0) :- voternum(N).
        % for agreement only the issue literals are relevant.
        % if virtual and voter both accept.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,D), C = D + 1, virtual(X), js(V,X), ilit(X).
        % if virtual accepts and voter rejects.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,C), virtual(X), js(V,-X), ilit(X).
        % if virtual and voter both reject.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,D), C = D + 1, virtual(-X), js(V,-X), ilit(X).
        % if virtual rejects and voter accepts.
        virtagr(Xn,Vn,C) :- varnum(Xn), varorder(X,Xn), voternum(Vn), voterorder(V,Vn),
          virtagr(Xn-1,Vn,C), virtual(-X), js(V,X), ilit(X).

        % add 2-ary predicate to encode the total agreement for each voter.
        virtagr(V,C) :- virtagr(NI,V,C), numissues(NI).
        % introduce 2-ary predicate to encode product of agreement scores.
        virtagr_lamb(V,C) :- virtagr(V,C1), C1 > 0, C = C1 * ld.
        virtagr_lamb(V,ln) :- virtagr(V,C), C = 0.

        % introduce 2-ary predicate virtagr_prod to calculate the product of the 
        % individual total agreement scores.
        virtagr_prod(1,C) :- virtagr_lamb(1,C).
        virtagr_prod(V,C) :- V1 = V - 1, virtagr_prod(V1,C1), virtagr_lamb(V,C2), 
          C = C1 * C2.

        % make predicate for final virtual agreement.
        virtagr(C) :- virtagr_prod(N,C), numvoters(N).

        % saturate all virtual/1, virtagr/3, virtagr/2, virtagr_prod/2 in case w 
        % is derived.
        virtual(X) :- w, lit(X).
        virtagr(Xn,Vn,0..C) :- w, varnum(Xn), voternum(Vn), numvars(M), C = M + 1. 
        virtagr(Vn,0..C) :- w, voternum(Vn), numvars(M), C = M + 1.
        virtagr_lamb(Vn,0..C) :- w, voternum(Vn), numvars(M), C = M + 1.
        virtagr_prod(Vn,0..C) :- w, voternum(Vn), numvoters(M), C = M + 1. 

        % compute the distance from the collective assignment to the profile.
        agr(V,C) :- voter(V), C = #count { X : ilit(X), js(col,X), js(V,X) }.
        agr_lamb(V,C) :- agr(V,C1), C1 > 0, C = C1 * ld.
        agr_lamb(V,ln) :- agr(V,C), C = 0.

        % calculate collective agreement, now product of individual agreements.
        colagr(1,C) :- agr_lamb(1,C).
        colagr(V,C) :- V1 = V - 1, colagr(V1,C1), agr_lamb(V,C2), C = C1 * C2.
        colagr(C) :- numvoters(N), colagr(N,C).

        % remove virtual assignments that have distance at least that of the  
        % collective outcome.
        w :- virtagr(C1), colagr(C2), C1 <= C2.
        """)
    return asp_program

# Original implementation kemeny3-opt.lp in JA-ASP [License-(JA-ASP)]
def kemeny_original():
    asp_program = """
        % determine the Hamming distance from each voter's judgment set to the outcome
        dist(A,D) :- voter(A), D = #count { X : ilit(X), js(col,X), js(A,-X) }.
        % sum the distances over all voters.
        dist(E) :- E = #sum { D,dist(A,D) : dist(A,D) }.
        % minimize the cumulative distance.
        #minimize { E@10,dist(E) : dist(E) }."""
    return asp_program

# Original implementation kemeny3.lp in JA-ASP [License-(JA-ASP)]
# Some modifications were necessary to be compatible with this implementation.
# The modifications are shown as comments.
def kemeny_original_sat():
    asp_program = """
        % determine support for each issue literal. 
        pc(X,N) :- ilit(X), N = #count { A : voter(A), js(A,X) }.       

        % use the technique of saturation (see Eiter & Gottlob '95)
        w :- not w.
        virtual(X) :- lit(X), w. % ilit(X) to lit(X) [MODIFIED]
        % guess a virtual assignment
        % virtual(X) ; virtual(-X) :- var(X). MODIFIED:
        virtual(X) ; virtual(-X) :- variable(X).
        % remove virtual assignments that are contradictory
        % w :- var(X), virtual(X), virtual(-X). MODIFIED:
        w :- variable(X), virtual(X), virtual(-X).
        % remove virtual assignments that don't satisfy integrity constraint
        % w :- clause(C), virtual(-L) : clause(C,L). MODIFIED:
        w :- outputClause(C), virtual(-L) : outputClause(C,L).

        % order the variables alphabetically
        1 { varorder(X,O) : varnum(O) } 1 :- var(X).
        1 { varorder(X,O) : var(X) } 1 :- varnum(O).
        :- varorder(X1,O1), varorder(X2,O2), X1 < X2, O1 > O2.      

        % order the voters alphabetically
        1 { voterorder(A,O) : voternum(O) } 1 :- voter(A).
        1 { voterorder(A,O) : voter(A) } 1 :- voternum(O).
        :- voterorder(A1,O1), voterorder(A2,O2), A1 < A2, O1 > O2.

        % compute the distance from the virtual assignment to the profile
        % virtdist(Var,Voter,Ans)
        virtdist(0,N,0) :- numvoters(N).
        % MODIFICATION: ilit(X) clause added to four rules below.
        virtdist(Xn,An,C) :-
          varnum(Xn), varorder(X,Xn),
          voternum(An), voterorder(A,An),
          virtdist(Xn,An-1,C), virtual(X), js(A,X), ilit(X).
        virtdist(Xn,An,C) :-
          varnum(Xn), varorder(X,Xn),
          voternum(An), voterorder(A,An),
          virtdist(Xn,An-1,D), C = D+1, virtual(X), js(A,-X), ilit(X).
        virtdist(Xn,An,C) :-
          varnum(Xn), varorder(X,Xn),
          voternum(An), voterorder(A,An),
          virtdist(Xn,An-1,C), virtual(-X), js(A,-X), ilit(X).
        virtdist(Xn,An,C) :-
          varnum(Xn), varorder(X,Xn),
          voternum(An), voterorder(A,An),
          virtdist(Xn,An-1,D), C = D+1, virtual(-X), js(A,X), ilit(X).
        virtdist(Xn,0,C) :- varnum(Xn), numvoters(N), virtdist(Xn-1,N,C).
        virtdist(D) :- virtdist(M,N,D), numvars(M), numvoters(N).
        % saturate all virtdist/3 in case w is derived
        %virtdist(0..M,0..N,0..C) :- w, numvars(M), numvoters(N), C = N*M.
        virtdist(Xn,An,0..C) :- w, varnum(Xn), voternum(An), numvars(M), C = M*Xn.

        % compute the distance from the collective assignment to the profile
        coldist(D) :- D = #sum { N,pc(X,N) : js(col,-X), pc(X,N) }.     

        % remove virtual assignments that have distance at least that of the collective outcome
        w :- virtdist(D1), coldist(D2), D1 >= D2."""
    return asp_program



