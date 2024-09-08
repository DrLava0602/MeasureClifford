from qiskit import *
from qiskit.quantum_info.operators import Operator
from numpy import conjugate, pi, sqrt
#from qiskit.execute_function import execute
from qiskit.circuit.library import XGate, SGate, SdgGate, CPhaseGate
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace
#from qiskit.extensions import UnitaryGate
from qiskit.quantum_info import random_statevector
import random
import numpy as np
from qiskit import qasm2, qasm3
from qiskit.quantum_info import StabilizerState, Pauli
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
# XGate().control(num_ctrl_qubits=3,ctrl_state='000')
#font: Lucida Console

import builtins as __builtin__
import sys

def myprint(*args, **kwargs):
    new_args = []
    for item in args:
        if type(item) == np.ndarray and item.dtype == np.dtype('bool'):
            new_args.append(item.astype(int))
        else:
            new_args.append(item)
    new_args = tuple(new_args)
    
    return __builtin__.print(*new_args, **kwargs)

def measure(qc, shots=1000):
    aer_sim = Aer.get_backend('aer_simulator')
    transpiled = transpile(qc, aer_sim)
    qobj = assemble(transpiled)
    results = aer_sim.run(qobj, shots=shots).result()
    counts = results.get_counts()
    return counts

# ===========================================================

def isCommute(row_1, row_2):
    n_qubit = len(row_1) // 2
    
    answer = True
    for i in range(n_qubit):
        answer ^= (row_1[i] & row_2[n_qubit + i]) ^ (row_2[i] & row_1[n_qubit + i])

    return answer

def rowSum(row_1, row_2):
    """
    Calculate tableau(Pauli(row_1) * Pauli(row_2)).
    """
    n_qubit = len(row_1) // 2

    X = [True, False]
    Y = [True, True]
    Z = [False, True]

    new_row = np.array([False] * (2 * n_qubit + 1))

    phase_shift = 0
    if row_1[2 * n_qubit] == True:
        phase_shift += 2
    if row_2[2 * n_qubit] == True:
        phase_shift += 2
    for i in range(n_qubit):
        new_row[i] = row_1[i] ^ row_2[i]
        new_row[n_qubit + i] = row_1[n_qubit + i] ^ row_2[n_qubit + i]
        if [row_1[i], row_1[n_qubit + i], row_2[i], row_2[n_qubit + i]] in [ X+Y, Y+Z, Z+X ]:
            phase_shift += 1                                                #TFTT TTFT FTTF
        elif [row_1[i], row_1[n_qubit + i], row_2[i], row_2[n_qubit + i]] in [ X+Z, Z+Y, Y+X ]:
            phase_shift -= 1                                                #TFFT FTTT TTTF
    assert(phase_shift % 2 == 0) #### when does this happen
    # print(phase_shift)
    phase_shift = phase_shift % 4
    if phase_shift == 2:
        new_row[n_qubit * 2] = True

    return new_row
        
    
def observableToTableau(observable):
    n_qubit = len(observable)

    row = np.array([False] * (2 * n_qubit + 1))
    for i in range(n_qubit):
        if observable[i] == 'X' or observable[i] == 'Y':
            row[i] = True
        if observable[i] == 'Z' or observable[i] == 'Y':
            row[n_qubit + i] = True
### Can this be simplified if only Z measures?
    return row


def measureClifford(tableau, observable):
    """
    Example: Observable IX001YYZ means
             the probability of --001-- times
             the expectation of IX---YYX under --001--.
    """
    n_qubit = len(tableau) // 2
    observable = list(observable)
    value = 1
    orig_observable = observable.copy()
    # step 0: transform to Z basis
    for jth_row in range(n_qubit * 2):
        for ith_qubit in range(n_qubit):
            if observable[ith_qubit] in ['i', 'j', 'Y']: # apply Sdg
                tableau[jth_row][2 * n_qubit] ^= tableau[jth_row][ith_qubit]
                tableau[jth_row][ith_qubit + n_qubit] ^= tableau[jth_row][ith_qubit]
                (tableau[jth_row][ith_qubit], tableau[jth_row][ith_qubit + n_qubit]) = (tableau[jth_row][ith_qubit + n_qubit], tableau[jth_row][ith_qubit])
                # [ith_qubit + n_qubit]_nxt = [ith_qubit]
                # [ith_qubit]_nxt = [ith_qubit + n_qubit] ^ [ith_qubit]
                # [2 * n_qubit]_nxt = [2 * n_qubit] ^ [ith_qubit]
            if observable[ith_qubit] in ['+', '-', 'X']: # apply H
                tableau[jth_row][2 * n_qubit] ^= tableau[jth_row][ith_qubit] & tableau[jth_row][ith_qubit + n_qubit]
                (tableau[jth_row][ith_qubit], tableau[jth_row][ith_qubit + n_qubit]) = (tableau[jth_row][ith_qubit + n_qubit], tableau[jth_row][ith_qubit])
                # [ith_qubit + n_qubit]_nxt = [ith_qubit]
                # [ith_qubit]_nxt = [ith_qubit + n_qubit]
                # [2 * n_qubit]_nxt = [2 * n_qubit] ^ ([ith_qubit] & [ith_qubit + n_qubit])

    for ith_qubit in range(n_qubit):
        if observable[ith_qubit] in ['X', 'Y']:
            observable[ith_qubit] = 'Z'
        elif observable[ith_qubit] in ['+', 'i']:
            observable[ith_qubit] = '0'
        elif observable[ith_qubit] in ['-', 'j']:
            observable[ith_qubit] = '1'
    # print("After step 0: ")
    # print(tableau)
    # step 1: handle probability calculation
    for ith_qubit in range(len(observable)):
        if observable[ith_qubit] in ['0', '1']: # do Z-basis measurement
            has_anticommute = False
            first_anticommute_row_idx = None
            # first_anticommute_row = np.array([False] * (2 * n_qubit + 1))
            
            for jth_row in range(n_qubit, n_qubit * 2):
                if tableau[jth_row][ith_qubit] == True:
                    # tableau[jth_row] = rowSum(first_anticommute_row, tableau[jth_row])
                    if has_anticommute == False:
                        first_anticommute_row_idx = jth_row
                    has_anticommute = True
            first_anticommute_row = tableau[first_anticommute_row_idx].copy()
            # print(first_anticommute_row)
            if has_anticommute: # case 1: 50%-50%
                value *= 0.5
                # handle destabilizer rows
                for jth_row in range(n_qubit*2):
                    if jth_row == first_anticommute_row_idx - n_qubit:
                        continue    ## not mentioned in paper
                    if tableau[jth_row][ith_qubit] == True:
                        tableau[jth_row] = rowSum(first_anticommute_row, tableau[jth_row])
                    # print(jth_row, ": ", rowSum(first_anticommute_row, tableau[jth_row]))
                tableau[first_anticommute_row_idx - n_qubit] = rowSum(np.array([False] * (2 * n_qubit + 1)), first_anticommute_row)
                # print(first_anticommute_row_idx - n_qubit, ": ", rowSum(np.array([False] * (2 * n_qubit + 1)), first_anticommute_row))
                tableau[first_anticommute_row_idx] = np.array([False] * (2 * n_qubit + 1))
                tableau[first_anticommute_row_idx][ith_qubit + n_qubit] = True # zpa = 1
                tableau[first_anticommute_row_idx][n_qubit * 2] = (observable[ith_qubit] == '1') # collapse
                # print("hi")
            else:               # case 2: deterministic
                # print(orig_observable)
                ancilla_row = np.array([False] * (2 * n_qubit + 1))
                for jth_row in range(n_qubit):
                    if tableau[jth_row][ith_qubit] == True:
                        # print("hi")
                        ancilla_row = rowSum(tableau[jth_row + n_qubit], ancilla_row)
                        # print(ancilla_row)
                # print(ancilla_row)
                if ancilla_row[n_qubit * 2] != (observable[ith_qubit] == '1'):
                    value = 0
                    print(orig_observable, ith_qubit)
                    return value # such measurement result never happens
                # otherwise, such measurement result always happens
            observable[ith_qubit] = 'I'
        
    # print(tableau)

    # step 2: handle expectation value calculation
    observable_row = observableToTableau(observable)
    # for jth_row in range(2*n_qubit):
        # print(isCommute(observable_row, tableau[jth_row]))
    for jth_row in range(n_qubit, n_qubit * 2):
        if isCommute(observable_row, tableau[jth_row]) == False:
            # print(orig_observable)
            return 0    # expectation value must be 0; no need to futher update the tableau 
    

    ancilla_row = np.array([False] * (2 * n_qubit + 1))
    for jth_row in range(n_qubit):
        # print(ancilla_row)
        if isCommute(observable_row, tableau[jth_row]) == False:
            ancilla_row = rowSum(tableau[jth_row + n_qubit], ancilla_row)
            # print("idx: ", jth_row)
    # print(ancilla_row)
            
    
            
    if ancilla_row[n_qubit * 2] == True:
        value *= -1
        
    return value

# =============================================================

if True:
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.t(0)
    qc.h(0)
    qc.cx(0, 1)
    qc.h(2)
    qc.cx(2, 1)
    qc.t(1)
    # print(qc)

    # Qiskit method
    state = Statevector(qc)
    for i in range(8):
        myprint(bin(i)[2:].rjust(3, '0'), abs(state[i])**2)
    myprint()

    # Our method
    qc = QuantumCircuit(5)
    qc.h(0)

    qc.h(3)
    qc.cx(3, 4)

    qc.h(3)
    qc.cx(3, 1)
    qc.h(2)
    qc.cx(2, 1)
    qc.draw('mpl').show()
    # print(qc)
    stab = StabilizerState(qc)
    tableau = stab.clifford.tableau
    print(tableau)
    value = measureClifford(tableau, 'XZ101')
    print(value)

    sys.exit()
