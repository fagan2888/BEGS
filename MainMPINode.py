# -*- coding: utf-8 -*-
"""
Created on Sat May  4 19:33:24 2013

@author: dgevans
"""
from primitives import BGP_parameters
import numpy as np
from Spline import Spline
from mpi4py import MPI

Para = BGP_parameters()
Para.P = np.array([[7.0/11.0, 4.0/11.0],[3.0/19.0,16.0/19.0]])
Para.psi = 0.6994
Para.theta_1 = np.array([3.9725,4.1379])
Para.theta_2 = np.array([0.9642,1.0358])
Para.g = .4199
Para.beta = np.array([0.98,.92])
Para.xmin = -3.0
Para.xmax = 3.0
Para.Rmin = 2.7
Para.Rmax = 3.7
Para.POLICY_TAG = 5
Para.approxOrder = [2,2]
xgrid =np.linspace(Para.xmin,Para.xmax,25)
Rgrid = np.linspace(Para.Rmin,Para.Rmax,25)
X = Spline.makeGrid([xgrid,Rgrid])
domain = np.vstack((X,X))
domain = zip(domain[:,0],domain[:,1],[0]*len(X)+[1]*len(X))
Para.domain = domain


comm = MPI.COMM_SELF.Spawn('python',
                           args=['mpiworker.py'],
                           maxprocs=2)
comm.bcast(Para,root=MPI.ROOT)
#Vf,Vf_old,Vfprime,c1_policy,c2_policy,Rprime_policy,xprime_policy = Bellman.solveBellmanMPI(Vf,c1_policy,c2_policy,Rprime_policy,xprime_policy,Para)
        