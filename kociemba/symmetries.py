# #################### Symmetry related functions. Symmetry considerations increase the performance of the solver.######

from os import path
import numpy as np
from numpy import uint, ushort, ubyte
import array as ar
from . import cubie as cb
from .defs import N_TWIST, N_SYM, N_SYM_D4h, N_FLIP, N_SLICE, N_CORNERS, N_UD_EDGES, N_MOVE, N_FLIPSLICE_CLASS, \
    N_CORNERS_CLASS
from .enums import Corner as Co, Edge as Ed, Move as Mv, BS

INVALID = 65535

relative_path = path.join(path.dirname(__file__), "tables/")

#  #################### Permutations and orientation changes of the basic symmetries ###################################

# 120° clockwise rotation around the long diagonal URF-DBL
cpROT_URF3 = [Co.URF, Co.DFR, Co.DLF, Co.UFL, Co.UBR, Co.DRB, Co.DBL, Co.ULB]
coROT_URF3 = [1, 2, 1, 2, 2, 1, 2, 1]
epROT_URF3 = [Ed.UF, Ed.FR, Ed.DF, Ed.FL, Ed.UB, Ed.BR, Ed.DB, Ed.BL, Ed.UR, Ed.DR, Ed.DL, Ed.UL]
eoROT_URF3 = [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1]

# 180° rotation around the axis through the F and B centers
cpROT_F2 = [Co.DLF, Co.DFR, Co.DRB, Co.DBL, Co.UFL, Co.URF, Co.UBR, Co.ULB]
coROT_F2 = [0, 0, 0, 0, 0, 0, 0, 0]
epROT_F2 = [Ed.DL, Ed.DF, Ed.DR, Ed.DB, Ed.UL, Ed.UF, Ed.UR, Ed.UB, Ed.FL, Ed.FR, Ed.BR, Ed.BL]
eoROT_F2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# 90° clockwise rotation around the axis through the U and D centers
cpROT_U4 = [Co.UBR, Co.URF, Co.UFL, Co.ULB, Co.DRB, Co.DFR, Co.DLF, Co.DBL]
coROT_U4 = [0, 0, 0, 0, 0, 0, 0, 0]
epROT_U4 = [Ed.UB, Ed.UR, Ed.UF, Ed.UL, Ed.DB, Ed.DR, Ed.DF, Ed.DL, Ed.BR, Ed.FR, Ed.FL, Ed.BL]
eoROT_U4 = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]

# reflection at the plane through the U, D, F, B centers
cpMIRR_LR2 = [Co.UFL, Co.URF, Co.UBR, Co.ULB, Co.DLF, Co.DFR, Co.DRB, Co.DBL]
coMIRR_LR2 = [3, 3, 3, 3, 3, 3, 3, 3]
epMIRR_LR2 = [Ed.UL, Ed.UF, Ed.UR, Ed.UB, Ed.DL, Ed.DF, Ed.DR, Ed.DB, Ed.FL, Ed.FR, Ed.BR, Ed.BL]
eoMIRR_LR2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

basicSymCube = [cb.CubieCube()] * 4
basicSymCube[BS.ROT_URF3] = cb.CubieCube(cpROT_URF3, coROT_URF3, epROT_URF3, eoROT_URF3)
basicSymCube[BS.ROT_F2] = cb.CubieCube(cpROT_F2, coROT_F2, epROT_F2, eoROT_F2)
basicSymCube[BS.ROT_U4] = cb.CubieCube(cpROT_U4, coROT_U4, epROT_U4, eoROT_U4)
basicSymCube[BS.MIRR_LR2] = cb.CubieCube(cpMIRR_LR2, coMIRR_LR2, epMIRR_LR2, eoMIRR_LR2)
# ######################################################################################################################

# ######################################## Fill SymCube list ###########################################################

# 48 CubieCubes will represent the 48 cube symmetries
symCube = []
cc = cb.CubieCube()  # Identity cube
idx = 0
for urf3 in range(3):
    for f2 in range(2):
        for u4 in range(4):
            for lr2 in range(2):
                symCube.append(cb.CubieCube(cc.cp, cc.co, cc.ep, cc.eo))
                idx += 1
                cc.multiply(basicSymCube[BS.MIRR_LR2])
            cc.multiply(basicSymCube[BS.ROT_U4])
        cc.multiply(basicSymCube[BS.ROT_F2])
    cc.multiply(basicSymCube[BS.ROT_URF3])
########################################################################################################################

# ########################################## Fill the inv_idx array ####################################################

# Indices for the inverse symmetries: SymCube[inv_idx[idx]] == SymCube[idx]^(-1)
inv_idx = [0] * N_SYM
for j in range(N_SYM):
    for i in range(N_SYM):
        cc = cb.CubieCube(symCube[j].cp, symCube[j].co, symCube[j].ep, symCube[j].eo)
        cc.corner_multiply(symCube[i])
        if cc.cp[Co.URF] == Co.URF and cc.cp[Co.UFL] == Co.UFL and cc.cp[Co.ULB] == Co.ULB:
            inv_idx[j] = i
            break
########################################################################################################################

# ################################# Generate the group table for the 48 cube symmetries ################################
mult_sym = np.empty([N_SYM, N_SYM], dtype=np.uint8)
for i in range(N_SYM):
    for j in range(N_SYM):
        cc = cb.CubieCube(symCube[i].cp, symCube[i].co, symCube[i].ep, symCube[i].eo)
        cc.multiply(symCube[j])
        for k in range(N_SYM):
            if cc == symCube[k]:  # SymCube[i]*SymCube[j] == SymCube[k]
                mult_sym[i][j] = k
                break
########################################################################################################################

# #### Generate the table for the conjugation of a move m by a symmetry s. conj_move[m, s] = s*m*s^-1 ##################
conj_move = np.empty([N_MOVE, N_SYM], dtype=np.uint8)
for s in range(N_SYM):
    for m in Mv:
        ss = cb.CubieCube(symCube[s].cp, symCube[s].co, symCube[s].ep, symCube[s].eo)  # copy cube
        ss.multiply(cb.moveCube[m])  # s*m
        ss.multiply(symCube[inv_idx[s]])  # s*m*s^-1
        for m2 in Mv:
            if ss == cb.moveCube[m2]:
                conj_move[m][s] = m2
########################################################################################################################

# ###### Generate the phase 1 table for the conjugation of the twist t by a symmetry s. twist_conj[t, s] = s*t*s^-1 ####
fname = path.join(relative_path, "conj_twist")
if not path.isfile(fname):
    print('On the first run, several tables will be created. This takes from 1/2 hour (e.g. PC) to 6 hours '
          '(e.g. RaspberryPi3), depending on the hardware.')
    print("creating " + fname + " table...")
    twist_conj = ar.array('H', [0] * (N_TWIST * N_SYM_D4h))
    for t in range(N_TWIST):
        cc = cb.CubieCube()
        cc.set_twist(t)
        for s in range(N_SYM_D4h):
            ss = cb.CubieCube(symCube[s].cp, symCube[s].co, symCube[s].ep, symCube[s].eo)  # copy cube
            ss.corner_multiply(cc)  # s*t
            ss.corner_multiply(symCube[inv_idx[s]])  # s*t*s^-1
            twist_conj[N_SYM_D4h * t + s] = ss.get_twist()
    with open(fname, "wb") as fh:
        np.save(fh, twist_conj, allow_pickle=False)
else:
    # print("loading " + fname + " table...")
    with open(fname, 'rb') as fh:
        # twist_conj = np.asarray(ar.array("H"))
        twist_conj = np.asarray(np.load(fh, allow_pickle=False), dtype=ushort)

# ######################################################################################################################

# #################### Generate the phase 2 table for the conjugation of the URtoDB coordinate by a symmetrie ##########
fname = path.join(relative_path, "conj_ud_edges")
if not path.isfile(fname):
    print("creating " + fname + " table...")
    ud_edges_conj = ar.array('H', [0] * (N_UD_EDGES * N_SYM_D4h))
    for t in range(N_UD_EDGES):
        if (t + 1) % 400 == 0:
            print('.', end='', flush=True)
        if (t + 1) % 32000 == 0:
            print('')
        cc = cb.CubieCube()
        cc.set_ud_edges(t)
        for s in range(N_SYM_D4h):
            ss = cb.CubieCube(symCube[s].cp, symCube[s].co, symCube[s].ep, symCube[s].eo)  # copy cube
            ss.edge_multiply(cc)  # s*t
            ss.edge_multiply(symCube[inv_idx[s]])  # s*t*s^-1
            ud_edges_conj[N_SYM_D4h * t + s] = ss.get_ud_edges()
    print('')
    with open(fname, "wb") as fh:
        np.save(fh, ud_edges_conj, allow_pickle=False)
else:
    # print("loading " + fname + " table...")
    with open(fname, "rb") as fh:
        # ud_edges_conj = np.asarray(ar.array("H"))
        ud_edges_conj = np.asarray(np.load(fh, allow_pickle=False), dtype=ushort)
# ######################################################################################################################

# ############## Generate the tables to handle the symmetry reduced flip-slice coordinate in  phase 1 ##################
fname1 = path.join(relative_path, "fs_classidx")
fname2 = path.join(relative_path, "fs_sym")
fname3 = path.join(relative_path, "fs_rep")
if not (path.isfile(fname1) and path.isfile(fname2) and path.isfile(fname3)):
    print("creating " + "flipslice sym-tables...")
    flipslice_classidx = ar.array('H', [INVALID] * (N_FLIP * N_SLICE))  # idx -> classidx
    flipslice_sym = ar.array('B', [0] * (N_FLIP * N_SLICE))  # idx -> symmetry
    flipslice_rep = ar.array('L', [0] * N_FLIPSLICE_CLASS)  # classidx -> idx of representant

    classidx = 0
    cc = cb.CubieCube()
    for slc in range(N_SLICE):
        cc.set_slice(slc)
        for flip in range(N_FLIP):
            cc.set_flip(flip)
            idx = N_FLIP * slc + flip
            if (idx + 1) % 4000 == 0:
                print('.', end='', flush=True)
            if (idx + 1) % 320000 == 0:
                print('')

            if flipslice_classidx[idx] == INVALID:
                flipslice_classidx[idx] = classidx
                flipslice_sym[idx] = 0
                flipslice_rep[classidx] = idx
            else:
                continue
            for s in range(N_SYM_D4h):  # conjugate representant by all 16 symmetries
                ss = cb.CubieCube(symCube[inv_idx[s]].cp, symCube[inv_idx[s]].co, symCube[inv_idx[s]].ep,
                                  symCube[inv_idx[s]].eo)  # copy cube
                ss.edge_multiply(cc)
                ss.edge_multiply(symCube[s])  # s^-1*cc*s
                idx_new = N_FLIP * ss.get_slice() + ss.get_flip()
                if flipslice_classidx[idx_new] == INVALID:
                    flipslice_classidx[idx_new] = classidx
                    flipslice_sym[idx_new] = s
            classidx += 1
    print('')
    with open(fname1, 'wb') as fh:
        np.save(fh, flipslice_classidx, allow_pickle=False)
    with open(fname2, 'wb') as fh:
        np.save(fh, flipslice_sym, allow_pickle=False)
    with open(fname3, 'wb') as fh:
        np.save(fh, flipslice_rep, allow_pickle=False)

else:
    # print("loading " + "flipslice sym-tables...")

    with open(fname1, 'rb') as fh:
        # flipslice_classidx = np.asarray(ar.array("H"))
        flipslice_classidx = np.asarray(np.load(fh, allow_pickle=False), dtype=ushort)
    with open(fname2, 'rb') as fh:
        # flipslice_sym = np.asarray(ar.array("B"))
        flipslice_sym = np.asarray(np.load(fh, allow_pickle=False), dtype=ubyte)
    with open(fname3, 'rb') as fh:
        # flipslice_rep = np.asarray(ar.array("L"))
        flipslice_rep = np.asarray(np.load(fh, allow_pickle=False), dtype=uint)
########################################################################################################################

# ############ Generate the tables to handle the symmetry reduced corner permutation coordinate in phase 2 #############
fname1 = path.join(relative_path, "co_classidx")
fname2 = path.join(relative_path, "co_sym")
fname3 = path.join(relative_path, "co_rep")
if not (path.isfile(fname1) and path.isfile(fname2) and path.isfile(fname3)):
    print("creating " + "corner sym-tables...")
    corner_classidx = ar.array('H', [INVALID] * N_CORNERS)  # idx -> classidx
    corner_sym = ar.array('B', [0] * N_CORNERS)  # idx -> symmetry
    corner_rep = ar.array('H', [0] * N_CORNERS_CLASS)  # classidx -> idx of representant

    classidx = 0
    cc = cb.CubieCube()
    for cp in range(N_CORNERS):
        cc.set_corners(cp)
        if (cp + 1) % 8000 == 0:
            print('.', end='', flush=True)

        if corner_classidx[cp] == INVALID:
            corner_classidx[cp] = classidx
            corner_sym[cp] = 0
            corner_rep[classidx] = cp
        else:
            continue
        for s in range(N_SYM_D4h):  # conjugate representant by all 16 symmetries
            ss = cb.CubieCube(symCube[inv_idx[s]].cp, symCube[inv_idx[s]].co, symCube[inv_idx[s]].ep,
                              symCube[inv_idx[s]].eo)  # copy cube
            ss.corner_multiply(cc)
            ss.corner_multiply(symCube[s])  # s^-1*cc*s
            cp_new = ss.get_corners()
            if corner_classidx[cp_new] == INVALID:
                corner_classidx[cp_new] = classidx
                corner_sym[cp_new] = s
        classidx += 1
    print('')
    with open(fname1, 'wb') as fh:
        np.save(fh, corner_classidx, allow_pickle=False)
    with open(fname2, 'wb') as fh:
        np.save(fh, corner_sym, allow_pickle=False)
    with open(fname3, 'wb') as fh:
        np.save(fh, corner_rep, allow_pickle=False)

else:
    # print("loading " + "corner sym-tables...")

    with open(fname1, 'rb') as fh:
        # corner_classidx = np.asarray(ar.array("H"))
        corner_classidx = np.asarray(np.load(fh, allow_pickle=False), dtype=ushort)
    with open(fname2, 'rb') as fh:
        # corner_sym = np.asarray(ar.array("B"))
        corner_sym = np.asarray(np.load(fh, allow_pickle=False), dtype=ubyte)
    with open(fname3, 'rb') as fh:
        # corner_rep = np.asarray(ar.array("H"))
        corner_rep = np.asarray(np.load(fh, allow_pickle=False), dtype=ushort)
########################################################################################################################