"""Exact finite checks supporting, not replacing, the proofs in main.tex.

No third-party packages or network access are required. All pass/fail numerical
claims use integers or Fraction; logarithms are presentation only.
"""
from fractions import Fraction as F
from itertools import permutations
from math import comb, factorial, log2
from pathlib import Path
import json


def falling(n, k):
    out = 1
    for j in range(k):
        out *= n-j
    return out


def pow2(e):
    return F(2**e) if e >= 0 else F(1, 2**(-e))


def main():
    checks = {}
    N, b, t, r = 2**128, 4096, 2**49, 2**48
    L = b+3
    D, H = falling(N-b, 2), falling(N-b, 3)
    di = F(comb(t, 2)*(2*L-1), H)
    do = F(comb(t, 2)*L*L, N*D)
    dm = F(comb(r, 6)*b**6, N**5)
    delta = di+do+dm
    alpha = F(6, D)+F(3*(t-1), D*(N-b-2))+F(t*L, H)
    gamma = F(falling(N, 3), H)
    pstar = F(1, (N-1)*(N-2))
    assert delta < pow2(-262)
    assert alpha < pow2(-253)
    assert gamma < 1+pow2(-110)
    assert alpha+gamma*pstar < pow2(-253)
    stats = F(r*b*(b-1), 2*N)+delta
    assert stats < pow2(-57)
    eta = F(b*(b+3), N)
    assert eta < pow2(-103)
    assert 1/(1-eta) < 1+pow2(-100)
    assert r*eta < 1
    assert 1/(1-r*eta) < 1+pow2(-54)
    checks['exact_full_volume_inequalities'] = True

    # Exact inverse-triple count, including modular wraparound. Every ordered
    # distinct target triple is checked, not just one convenient target.
    inv_cases = 0
    for n in (3, 4, 5, 6):
        tables = list(permutations(range(n)))
        for target in permutations(range(n), 3):
            count = 0
            for table in tables:
                inverse = [table.index(y) for y in target]
                count += (inverse[1] == (inverse[0]+1) % n and
                          inverse[2] == (inverse[0]+2) % n)
            assert F(count, factorial(n)) == F(1, (n-1)*(n-2))
            inv_cases += 1
    checks['inverse_alignment_all_targets'] = inv_cases

    # Verify the conditional triple law by exact permutation enumeration.
    n, q = 6, 2
    fixed_outputs = (0, 1)
    triples = {}
    for table in permutations(range(n)):
        if table[:q] == fixed_outputs:
            triple = table[q:q+3]
            triples[triple] = triples.get(triple, 0)+1
    assert len(triples) == falling(n-q, 3)
    assert set(triples.values()) == {factorial(n-q-3)}
    assert F(max(triples.values()), sum(triples.values())) == F(1, falling(n-q, 3))
    checks['conditional_sampling_enumeration'] = True

    # XOR preserves masses and the number of counter candidates. Check every
    # mask and pair of modular intervals in a small power-of-two space.
    n, interval_cases = 8, 0
    for length1 in range(1, 4):
        for length2 in range(1, 4):
            for v1 in range(n):
                first = {(v1+j+1) % n for j in range(length1)}
                for mask in range(n):
                    candidates = []
                    for hidden in range(n):
                        v2 = hidden ^ mask
                        second = {(v2+j+1) % n for j in range(length2)}
                        if first & second:
                            candidates.append(hidden)
                    assert len(candidates) <= length1+length2-1
                    interval_cases += 1
    checks['xor_interval_cardinality'] = interval_cases
    for width in range(1, 8):
        values = range(2**width)
        for mask in values:
            assert sorted(x ^ mask for x in values) == list(values)
            assert all(((x ^ mask) ^ mask) == x for x in values)
    checks['xor_bijection'] = True

    # Sequential resampling marginal: own record excludes A; another record
    # excludes B disjoint from A. A virtual candidate in B triggers a uniform
    # real resample outside A union B. Each admissible real result must have
    # exactly the uniform merged-table law. This checks forward and inverse
    # marginals, since the rule is symmetric in the two permutation axes.
    resample_cases = 0
    for n in range(3, 10):
        for own in range(n):
            for other in range(n-own):
                admissible = n-own-other
                for _ in range(admissible):
                    mass = F(1, n-own)+F(other, n-own)*F(1, admissible)
                    assert mass == F(1, admissible)
                    resample_cases += 1
    checks['partial_table_resampling_marginals'] = resample_cases

    # Density correction for adaptive stopping: for every small distinct
    # public output set, compare the exact conditional triple probability with
    # a distinct uniform triple. This checks the factor, not a stopping theorem.
    density_cases = 0
    for n in range(4, 9):
        for visible in range(n-2):
            ratio = F(falling(n, 3), falling(n-visible, 3))
            for triple in permutations(range(n), 3):
                actual = (F(1, falling(n-visible, 3))
                          if all(x >= visible for x in triple) else F(0))
                reference = F(1, falling(n, 3))
                assert actual <= ratio*reference
                density_cases += 1
    checks['terminal_density_domination'] = density_cases

    # Sampling-product lower bound, exactly, over a range including endpoints.
    for n in range(8, 25):
        for s in range(n-3):
            for u in range(1, n-s-2):
                product = F(falling(n-s-3, u), n**u)
                lower = 1-sum((F(s+3+j, n) for j in range(u)), F(0))
                assert product >= lower
    checks['finite_sampling_product'] = True

    # Regression for the review's adaptive-target counterexample. Reveal all
    # but the last bit of q distinct blocks. A repeated prefix identifies a
    # pair whose last bits are opposite; choose one of those bits as target.
    # Count prefix-collision probability exactly, avoiding huge enumeration.
    n, q = 256, 16
    no_prefix_pair = F(falling(n//2, q)*2**q, falling(n, q))
    selection_success = F(1, 2)+F(1, 2)*(1-no_prefix_pair)
    invalid_local_bound = F(n, 2*(n-(q-1)-3))
    valid_global_bound = F(n**q, 2*falling(n-3, q))
    assert selection_success > invalid_local_bound
    assert selection_success <= valid_global_bound
    checks['adaptive_target_selection_regression'] = True

    def displayed(value):
        return {'numerator': str(value.numerator), 'denominator': str(value.denominator),
                'log2_approx': log2(value.numerator)-log2(value.denominator)}

    report = {
        'status': 'all exact assertions passed',
        'scope': 'numerical inequalities and reduced-model consistency checks; written proofs remain necessary',
        'parameters': {'N': str(N), 'b': b, 'max_batches': str(t), 'max_requests': str(r)},
        'checks': checks,
        'bounds': {name: displayed(value) for name, value in {
            'private_input': di, 'private_output': do, 'public_multiplicity': dm,
            'delta_total': delta, 'alpha': alpha, 'gamma_minus_one': gamma-1,
            'inverse_alignment_probability': pstar, 'statistical_distance': stats,
            'epsilon_at_Q_2pow240': delta+2**240*alpha,
        }.items()},
    }
    Path(__file__).with_name('verification.json').write_bytes(
        (json.dumps(report, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'status': report['status'], 'checks': checks,
                      'delta_log2': report['bounds']['delta_total']['log2_approx'],
                      'alpha_log2': report['bounds']['alpha']['log2_approx']}, indent=2))


if __name__ == '__main__':
    main()
