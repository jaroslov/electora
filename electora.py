#!/usr/bin/env python

import argparse
import json
import math
import os
import sys

POPULATION_2013 = {
    "California"            :   38332521,
    "Texas"                 :   26448193,
    "New York"              :   19651127,
    "Florida"               :   19552860,
    "Illinois"              :   12882135,
    "Pennsylvania"          :   12773801,
    "Ohio"                  :   11570808,
    "Georgia"               :   9992167,
    "Michigan"              :   9895622,
    "North Carolina"        :   9848060,
    "New Jersey"            :   8899339,
    "Virginia"              :   8260405,
    "Washington"            :   6971406,
    "Massachusetts"         :   6692824,
    "Arizona"               :   6626624,
    "Indiana"               :   6570902,
    "Tennessee"             :   6495978,
    "Missouri"              :   6044171,
    "Maryland"              :   5928814,
    "Wisconsin"             :   5742713,
    "Minnesota"             :   5420380,
    "Colorado"              :   5268367,
    "Alabama"               :   4833722,
    "South Carolina"        :   4774839,
    "Louisiana"             :   4625470,
    "Kentucky"              :   4395295,
    "Oregon"                :   3930065,
    "Oklahoma"              :   3850568,
    "Connecticut"           :   3596080,
    "Iowa"                  :   3090416,
    "Mississippi"           :   2991207,
    "Arkansas"              :   2959373,
    "Utah"                  :   2900872,
    "Kansas"                :   2893957,
    "Nevada"                :   2790136,
    "New Mexico"            :   2085287,
    "Nebraska"              :   1868516,
    "West Virginia"         :   1854304,
    "Idaho"                 :   1612136,
    "Hawaii"                :   1404054,
    "Maine"                 :   1328302,
    "New Hampshire"         :   1323459,
    "Rhode Island"          :   1051511,
    "Montana"               :   1015165,
    "Delaware"              :   925749,
    "South Dakota"          :   844877,
    "Alaska"                :   735132,
    "North Dakota"          :   723393,
    #"District of Columbia"  :   646449,
    "Vermont"               :   626630,
    "Wyoming"               :   582658,
}

USA_TOTAL   = sum([v for k,v in POPULATION_2013.items()])

def HamiltonApportionment(population, house_seats):
    # Get population and initial divisor.
    pcount      = sum([v for k,v in population.items()])
    D           = pcount / house_seats

    # Perform initial allocation and get remainder.
    state_quota = {}
    for name, pop in population.items():
        state_quota[name] = (pop / D, float(pop) / D - pop / D)
    remainder   = house_seats - sum([D for name,(D,F) in state_quota.items()])

    # Sort by fractional part.
    state_order = [(name,F) for name,(D,F) in state_quota.items()]
    state_order.sort(key=lambda (n,f): f)
    state_order.reverse()
    for r,(name,F) in zip(xrange(remainder), state_order):
        apportion, fraction = state_quota[name]
        state_quota[name]   = (apportion+1,fraction)

    return dict([(name,apportion) for name,(apportion,fraction) in state_quota.items()])

def JeffersonApportionment(population, house_seats):
    # Get population and initial divisor.
    pcount      = sum([v for k,v in population.items()])
    D           = pcount / house_seats

    remainder   = house_seats

    # Perform initial allocation and get remainder.
    # I guess I could do a binary search, but I'd have to be pretty
    # carefuly about the 'direction' of the search, so we'll just
    # brute-force this bad-boy.
    state_quota = {}
    while remainder != 0:
        if D <= 30000:
            break
        for name, pop in population.items():
            state_quota[name] = max(pop / D, 1)
        remainder   = house_seats - sum([d for name,d in state_quota.items()])
        D           = D - 1

    return state_quota

#def WebsterApportionment(population, house_seats):
#    # Get population and initial divisor.
#    pcount      = sum([v for k,v in population.items()])
#    D           = pcount / house_seats
#
#    remainder   = house_seats
#
#    # Perform initial allocation and get remainder.
#    # I guess I could do a binary search, but I'd have to be pretty
#    # carefuly about the 'direction' of the search, so we'll just
#    # brute-force this bad-boy.
#    while remainder != 0:
#        if D <= 30000:
#            return state_quota
#        state_quota = {}
#        for name, pop in population.items():
#            state_quota[name] = max(1, round(float(pop) / D))
#        remainder   = house_seats - sum([d for name,d in state_quota.items()])
#        D           = D - 1
#
#    return state_quota


def HuntingtonHillApportionment(population, house_seats):
    # Get population.
    pcount      = sum([v for k,v in population.items()])

    state_quota = dict([(name,1) for name in population.keys()])

    remainder   = house_seats - sum([D for N,D in state_quota.items()])

    while remainder >= 0:
        priority    = [(population[name]/math.sqrt(D*(D+1)),name) for name,D in state_quota.items()]
        priority.sort()
        priority.reverse()
        state_quota[priority[0][1]] += 1
        remainder   = house_seats - sum([D for N,D in state_quota.items()])

    return state_quota

def Check(population, house_seats, method):
    res         = method(population, house_seats)
    pcount      = sum([v for k,v in population.items()])
    fairrep     = pcount / float(house_seats)
    fairelc     = pcount / (float(house_seats+100))
    if sum([x for n,x in res.items()]) != HOUSE_SEATS:
        print "Failed to apportion the House for the '%s' method!"%method.__name__
    print method.__name__
    print '    %-15s : #seats           electors    rep over rep       electoral over rep'%'State'
    print '    '+'-'*84
    states      = res.keys()
    states.sort()
    for state in states:
        assert res[state] > 0, state + ' in ' + method.__name__
        if res[state] > 0:
            repfair     = fairrep - population[state] / float(res[state])
            elcfair     = fairelc - population[state] / float(res[state]+2)
            print '    %-15s :  %8d     %8d       %+10.2f       %+10.2f'%(state, res[state], res[state]+2, 100*repfair/fairrep, 100*elcfair/fairelc)
        else:
            print '    %-15s : has zero representatives'%state
    print ''

ALLOWED_METHODS = [name for name,thing in locals().items() if name.endswith('Apportionment')]

parser      = argparse.ArgumentParser(description="Demonstrate several historical apportionment methods, and the effect of the number of representatives on apportionment and fairness.")
parser.add_argument('--method', metavar='METHODS', help='Which apportionment method(s) to use. The allowed methods are: '+', '.join(ALLOWED_METHODS), default=','.join(ALLOWED_METHODS))
parser.add_argument('--num-reps', metavar='NUMREPS', help='The number of representatives.', default=435)

args        = parser.parse_args()

METHODS     = [locals()[m] for m in args.method.split(',')]
HOUSE_SEATS = int(args.num_reps)
POPULATION  = POPULATION_2013

for house_seats in [HOUSE_SEATS]:
    for method in METHODS:
        Check(POPULATION, house_seats, method)
