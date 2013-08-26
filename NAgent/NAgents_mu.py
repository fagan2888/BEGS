# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 17:43:46 2013

@author: dgevans
"""
from numpy import *
from copy import deepcopy
from scipy.optimize import root
import pycppad as ad
import pdb
import numdifftools as nd
import primitives

Para2 = primitives.CES_parameters()
Para3 = primitives.CES_parameters()
Para2.theta = array([[3.3,3.],[1.1,1.]])
Para3.theta = array([[3.3,3.],[1.1,1.],[1.1,1.]])
Para2.alpha = array([1.,2.])/3.
Para3.alpha = ones(3)
Para2.n = array([1.,2.])
Para3.n = ones(3)

def SSresiduals(z,Para):
    '''
    Steady State residuals
    '''
    theta_1 = Para.theta[0,:]
    theta_i = Para.theta[1:,:]
    alpha_1 = Para.alpha[0]
    alpha_i = Para.alpha[1:].reshape((-1,1))
    n_1 = Para.n[0]
    n_i = Para.n[1:].reshape((-1,1))
    beta = Para.beta
    g = Para.g
    
    c1,ci,l1,li,x_i,rho_i,mu_i,lambda_i,xi,phi_i,eta_i = getSSQuantities(z,Para)
    
    uc1 = Para.Uc(c1)
    ucc1 = Para.Ucc(c1)
    uci = Para.Uc(ci)
    Euci = (Para.P.dot(uci.T)).T
    ucci = Para.Ucc(ci)
    ul1 = Para.Ul(l1)
    ull1 = Para.Ull(l1)
    uli = Para.Ul(li)
    ulli = Para.Ull(li)
     
    res = array([])
    con = x_i*(uci/Euci-beta) - (uci*ci+uli*li)+rho_i*(uc1*c1+ul1*l1)
    res = hstack((res,con.flatten()))
    
    con = rho_i*ul1/theta_1-uli/theta_i
    res = hstack((res,con.flatten()))
    
    con = n_1*theta_1*l1 + sum(n_i*theta_i*li,axis=0)-g-n_1*c1-sum(n_i*ci,0)
    res = hstack((res,con.flatten()))
    
    con = rho_i*uc1-uci
    res = hstack((res,con.flatten()))
    
    foc = alpha_i*uci-mu_i*( ucci*ci+uci )-n_i*xi-eta_i*ucci
    res = hstack((res,foc.flatten()))
    
    foc = alpha_1*uc1+sum(mu_i*rho_i,0)*( ucc1*c1+uc1 )-n_1*xi + sum(eta_i*rho_i,0)*ucc1
    res = hstack((res,foc.flatten()))
    
    foc = alpha_i*uli - mu_i*( ulli*li+uli ) - phi_i*ulli/theta_i + n_i*theta_i*xi
    res = hstack((res,foc.flatten()))
    
    foc = alpha_1*ul1 + sum(mu_i*rho_i,0)*( ull1*l1 + ul1 ) + sum(phi_i*rho_i,0)*ull1/theta_1 + n_1*theta_1*xi
    res = hstack((res,foc.flatten()))
    
    foc = lambda_i*Euci*( uci/Euci-beta )+mu_i*( uc1*c1+ul1*l1 ) + phi_i*ul1/theta_1 + eta_i*uc1
    res = hstack((res,foc.flatten()))
    
    return res
    
def getSSQuantities(z,Para):
    '''
    Gets quantities from z
    '''
    N = len(Para.theta)
    S = len(Para.P)
    c1 = z[0:S]
    
    ci = z[S:N*S].reshape((N-1,S))
    
    l1 = z[N*S:(N+1)*S]
    
    li = z[(N+1)*S:2*N*S].reshape((N-1,S))
    
    zi = 2*N*S
    x_i = z[zi:zi+N-1].reshape((N-1,1))
    zi+= N-1
    
    rho_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1
    
    mu_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1
    
    lambda_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1

    xi = z[zi:zi+S].reshape(S)
    zi += S    
    
    phi_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    eta_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    return c1,ci,l1,li,x_i,rho_i,mu_i,lambda_i,xi,phi_i,eta_i
    
def getSSNz(Para):
    '''
    Finds the number of elements in the steady state
    '''
    N = len(Para.theta)
    S = len(Para.P)
    zi = 2*N*S
    zi+= N-1
    zi += N-1
    zi += N-1
    zi += N-1
    zi += S    
    zi += S*(N-1)
    zi += S*(N-1)
    return zi
    
def findSteadyState(Para,x0,rho0):
    '''
    Finds the steady state for given Para
    '''
    Para2 = deepcopy(Para)
    Para2.theta = zeros(Para.theta.shape)
    Para2.theta[0,:] = Para.theta[0,:]
    Para2.theta[1:,:] = Para.theta[1,:]
    z0 = getInitialGuess(Para2,x0,rho0)
    res = root(lambda z: SSresiduals(z,Para2),z0)
    if not res.success:
        raise Exception(res.message)
    z1 = res.x
    
    res = root(lambda z: SSresiduals(z,Para),z1,tol=1e-12)
    if not res.success:
        raise Exception(res.message)
    return res.x
    
def getInitialGuess(Para,x,rho):
    '''
    Find the steady State
    '''
    N = len(Para.theta)
    S = len(Para.P)
    Para2 = deepcopy(Para)
    Para2.theta = Para.theta[0:2,:]
    Para2.n = array([Para.n[0],sum(Para.n[1:])])
    Para2.alpha = array([Para.alpha[0],sum(Para.alpha[1:])])
    def f(q):
        z = zeros(getSSNz(Para2))
        z[0:4*S+2] = hstack((q,[x,rho]))
        return SSresiduals(z,Para2)[0:4*S]
    res = root(f,0.5*ones(4*S))
    if not res.success:
        raise Exception(res.message)
    q=res.x
    z = zeros(getSSNz(Para))
    z[0:S] = q[0:S]
    z[S:N*S] = tile(q[S:2*S],N-1)
    z[N*S:N*S+S] = q[2*S:3*S]
    z[N*S+S:2*N*S] = tile(q[3*S:4*S],N-1)
    z[2*N*S:2*N*S+N-1] = x
    z[2*N*S+N-1:2*N*S+2*(N-1)] = rho
    return z
        
        
def FOCResiduals(z,mu_i,rho_i,xprime,V_rho,Para):
    '''
    Compute the residuals of the first order 
    '''
    N = len(Para.theta)
    theta_1 = Para.theta[0,:]
    theta_i = Para.theta[1:,:]
    alpha_1 = Para.alpha[0]
    alpha_i = Para.alpha[1:].reshape((-1,1))
    n_1 = Para.n[0]
    n_i = Para.n[1:].reshape((-1,1))
    beta = Para.beta
    g = Para.g
    P = Para.P[0,:]
    
    c1,ci,l1,li,x_i,muprime,rhoprime,lambda_i,xi,phi_i,eta_i = getFOCQuantities(z,Para)
    
    uc1 = Para.Uc(c1)
    ucc1 = Para.Ucc(c1)
    uci = Para.Uc(ci)
    Euci = uci.dot(P).reshape((N-1,-1))
    Emu_uci = (muprime*uci).dot(P).reshape((N-1,-1))
    ucci = Para.Ucc(ci)
    ul1 = Para.Ul(l1)
    ull1 = Para.Ull(l1)
    uli = Para.Ul(li)
    ulli = Para.Ull(li)
    
    res = alpha_1*uc1 + sum(rhoprime*muprime,0)*(ucc1*c1+uc1) - n_1*xi + sum(eta_i*rhoprime,0)*ucc1
    res = res.flatten()
    
    foc = alpha_i*uci -muprime*( ucci*ci+uci ) + x_i*ucci/Euci*( muprime - mu_i )\
    +lambda_i*ucci*(rhoprime-rho_i)-n_i*xi-eta_i*ucci
    res = hstack((res,foc.flatten()))

    foc = alpha_1*ul1 + sum(muprime*rhoprime,0)*(ull1*l1+ul1) + sum(phi_i*rhoprime,0)*ull1/theta_1 + n_1*theta_1*xi
    res = hstack((res,foc.flatten()))
    
    foc = alpha_i*uli -muprime*( ulli*li+uli ) - phi_i*ulli/theta_i + n_i*theta_i*xi
    res = hstack((res,foc.flatten()))

    foc = Emu_uci-mu_i
    res = hstack((res,foc.flatten()))    
    
    foc = beta*V_rho + muprime*(uc1*c1+ul1*l1) + phi_i*ul1/theta_1 + lambda_i*uci + eta_i*uc1
    res = hstack((res,foc.flatten()))
    
    con = x_i*uci/Euci - beta*xprime - (uci*ci+uli*li) + rhoprime*( uc1*c1+ul1*l1 )
    res = hstack((res,con.flatten()))
    
    con = (uc1*(rhoprime-rho_i)).dot(P)
    res = hstack((res,con.flatten()))
    
    con = rhoprime*ul1/theta_1-uli/theta_i
    res = hstack((res,con.flatten()))
    
    con = n_1*theta_1*l1+sum(n_i*theta_i*li,0)-g-c1*n_1 - sum(n_i*ci,0)
    res = hstack((res,con.flatten()))
    
    con = rhoprime*uc1-uci
    res = hstack((res,con.flatten()))
    
    
    return res
    
def envelopeCondition(z,Para):
    '''
    Computes V_x and V_rho from the envelope condition
    '''
    N = len(Para.theta)
    P = Para.P[0,:]
    c1,ci,l1,li,x_i,muprime,rhoprime,lambda_i,xi,phi_i,eta_i = getFOCQuantities(z,Para)
    
    uci = Para.Uc(ci)
    Euci = uci.dot(P).reshape((N-1,-1))

    V_rho = -lambda_i*Euci
    return V_rho
        
def getFOCQuantities(z,Para):
    '''
    Gets quantities from z
    '''
    N = len(Para.theta)
    S = len(Para.P)
    c1 = z[0:S]
    
    ci = z[S:N*S].reshape((N-1,S))
    
    l1 = z[N*S:(N+1)*S]
    
    li = z[(N+1)*S:2*N*S].reshape((N-1,S))
    
    zi = 2*N*S
    x_i = z[zi:zi+(N-1)].reshape((N-1,1))
    zi+= N-1
    
    muprime = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    rho_prime = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    
    lambda_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1

    xi = z[zi:zi+S].reshape(S)
    zi += S    
    
    phi_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    eta_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    return c1,ci,l1,li,x_i,muprime,rho_prime,lambda_i,xi,phi_i,eta_i
    
def getFOCNz(Para):
    '''
    Computes number of elements in z for FOC equations
    '''
    N = len(Para.theta)
    S = len(Para.P)
    zi = 2*N*S
    zi += (N-1)
    zi += S*(N-1)
    zi += S*(N-1)
    zi += N-1
    zi += S
    zi += S*(N-1)
    zi += S*(N-1)
    return zi
    
def SSz_to_FOCz(SSz,Para):
    '''
    Transforms the quantities and multipliers of the steady state into the quantities and
    multipliers  
    '''
    N = len(Para.theta)
    S = len(Para.P)
    q = SSz[0:2*S*N]
    zi = 2*N*S    
    x_i = SSz[zi:zi+N-1].reshape((N-1,1))
    xprime = tile(x_i,S)
    zi+= N-1
    
    rho_i = SSz[zi:zi+N-1].reshape((N-1,1))
    rhoprime = tile(rho_i,S)
    zi += N-1
    
    mu_i = SSz[zi:zi+N-1].reshape((N-1,1))
    muprime = tile(mu_i,S)
    zi += N-1

    mult = SSz[zi:]    
    
    #c1,ci,l1,li,x_i,muprime,rho_prime,lambda_i,xi,phi_i,eta_i
    return hstack((q,x_i.flatten(),muprime.flatten(),rhoprime.flatten(),mult))
    
def getPartialDerivativesFOC(Para,x0,rho0):
    '''
    Compute the partial derivatives of the FOC map and Envelope conditions
    '''    
    N = len(Para.theta)
    S = len(Para.P)
    
    assert S==2    
    
    SSz = findSteadyState(Para,x0,rho0)
    _,_,_,_,x_i,rho_i,mu_i,_,_,_,_ = getSSQuantities(SSz,Para)
    zbar = SSz_to_FOCz(SSz,Para)
    ybar = hstack((mu_i.flatten(),rho_i.flatten()))
    V_rho = envelopeCondition(zbar,Para)
    wbar = tile(hstack((x_i.flatten(),V_rho.flatten())),2)
    Phi = getPhi(N,len(zbar))
    
    #define functions to use when taking derivatives
    def w_fun(z):
        x_i = z[2*N*S:2*N*S+(N-1)]
        V_rho = envelopeCondition(z,Para)
        return hstack((x_i,V_rho.flatten()))
    def F(z,y,w):
        mu_i = y[0:N-1].reshape((N-1,1))
        rho_i = y[N-1:2*(N-1)].T.reshape((N-1,1))
        xprime = vstack((w[0:N-1],w[2*(N-1):3*(N-1)])).T
        V_rho = vstack((w[N-1:2*(N-1)],w[3*(N-1):4*(N-1)])).T
        return FOCResiduals(z,mu_i,rho_i,xprime,V_rho,Para)
        
    #take derivatives using auto-differentiation
    '''
    a_z = ad.independent(zbar)
    a_F = F(a_z,ybar,vbar)
    DzF = ad.adfun(a_z,a_F).jacobian(zbar)
    
    a_y = ad.independent(ybar)
    a_F = F(zbar,a_y,vbar)
    DyF = ad.adfun(a_y,a_F).jacobian(ybar)
    
    a_v = ad.independent(vbar)
    a_F = F(zbar,ybar,a_v)
    DvF = ad.adfun(a_v,a_F).jacobian(vbar)
    
    a_z = ad.independent(zbar)
    a_F = v(zbar)
    Dv = ad.adfun(a_z,a_F).jacobian(zbar)'''
    DzF = nd.Jacobian(lambda z: F(z,ybar,wbar))(zbar)
    DyF = nd.Jacobian(lambda y: F(zbar,y,wbar))(ybar)
    DvF = nd.Jacobian(lambda v: F(zbar,ybar,v))(wbar)
    Dv = nd.Jacobian(w_fun)(zbar)
    
    return DzF,DyF,DvF,Dv,Phi
 

def linearization(Para,x0,rho0):
    '''
    Finds and computes the linearization around the steady state
    '''
    N = len(Para.theta)
    DzF,DyF,DvF,Dv,Phi = getPartialDerivativesFOC(Para,x0,rho0)
    '''
    def MatrixEquation(Dyz_flat):
        Dyz = Dyz_flat.reshape((len(zbar),len(ybar)))
        return (DzF.dot(Dyz)+DyF+DvF.dot(kron(eye(2),Dv).dot(kron(eye(2),Dyz).dot(Phi.dot(Dyz))))).flatten()
        
    def MatrixEquation2(Bflat,test=None):
        B = Bflat.reshape((2*len(ybar),len(ybar)))
        def f(Dyz_flat):
            Dyz = Dyz_flat.reshape((len(zbar),len(ybar)))
            return (DzF.dot(Dyz) + DvF.dot(kron(eye(2),Dv).dot(kron(eye(2),Dyz).dot(B)))).flatten()
        nM = len(zbar)*len(ybar)
        M = zeros((nM,nM))
        for i in range(0,nM):
            M[:,i] = f(eye(nM)[i,:])
        Dyz_flat = linalg.solve(M,-DyF.flatten())
        pdb.set_trace()
        return Phi.dot(Dyz_flat.reshape((len(zbar),len(ybar)))).flatten()-Bflat
    ''' 
    def MatrixEquation(HV):
        HV = HV.reshape((2*(N-1),2*(N-1))) #constructHessianSymmetric(HVpartial,N)
        M = DzF+DvF.dot(kron(eye(2),HV)).dot(Phi)
        Dyz = linalg.solve(M,-DyF)
        HVnew =Dv.dot(Dyz)
        return (HVnew-HV).flatten()
    diff = 1
    HV = 0
    for i in range(0,100):
        HV0 = 0.1*random.randn(4*(N-1)**2)
        res = root(MatrixEquation,HV0)
        if res.success:
            HVtemp = res.x.reshape((2*(N-1),2*(N-1)))
            diffnew = max(abs(MatrixEquation(res.x)))
            if diffnew < diff:
                diff = diffnew
                HV = HVtemp
                print diff   
            #goodRoot = max(abs(MatrixEquation(res.x))) < diff
            #for i in range(0,N-1):
            #    if abs(HVtemp[i,i])<1e-6:
            #        goodRoot = False
            #if goodRoot:
            #    M = DzF+DvF.dot(kron(eye(2),HVtemp)).dot(Phi)
            #    Dyz = linalg.solve(M,-DyF)
            #    B = Phi.dot(Dyz)
            #    Bbar = Para.P[0,0]*B[:2*(N-1),:]+Para.P[0,1]*B[2*(N-1):,:]
            #    print linalg.eig(Bbar)[0][0],linalg.eig(Bbar)[1][:,0]
            #    HV =constructHessianSymmetric(res.x,N)
            #    diff = max(abs(MatrixEquation(res.x)))
            #    print diff    
    M = DzF+DvF.dot(kron(eye(2),HV)).dot(Phi)
    Dyz = linalg.solve(M,-DyF)

    H = (DzF +(DvF.dot(kron(eye(2),Dv)).dot(kron(eye(2),Dyz)).dot(Phi)))#Constructs the bordered Hessian
    return Dyz,H,DzF,DyF,DvF,Dv,HV,MatrixEquation
    
def linearization_2agent(Para,x0,rho0):
    '''
    Finds and computes the linearization around the steady state
    '''
    N = len(Para.theta)
    DzF,DyF,DvF,Dv,Phi = getPartialDerivativesFOC(Para,x0,rho0)

    def MatrixEquation(HVpartial):
        HV = constructHessianSymmetric_2agent(HVpartial,N)
        M = DzF+DvF.dot(kron(eye(2),HV)).dot(Phi)
        Dyz = linalg.solve(M,-DyF)
        HVnew =Dv.dot(Dyz)
        return getHVpartial_2agent(HVnew,N)-HVpartial
    diff = 1
    HV = 0
    for i in range(0,1000):
        HVpartial0 = 0.2*random.randn(6)
        res = root(MatrixEquation,HVpartial0,method='lm',tol=1e-14)
        if res.success:
            HVtemp =constructHessianSymmetric_2agent(res.x,N)
            M = DzF+DvF.dot(kron(eye(2),HVtemp)).dot(Phi)
            Dyz = linalg.solve(M,-DyF)
            B = Phi.dot(Dyz)
            Bbar = Para.P[0,0]*B[:2*(N-1),:]+Para.P[0,1]*B[2*(N-1):,:]
            if max(abs(MatrixEquation(res.x))) < diff  and abs(res.x[0]) >1e-5 :
                HV =constructHessianSymmetric_2agent(res.x,N)
                diff = max(abs(MatrixEquation(res.x)))
                print abs(HV[0,0])
                print diff    
    print HV
    M = DzF+DvF.dot(kron(eye(2),HV)).dot(Phi)
    Dyz = linalg.solve(M,-DyF)

    H = (DzF +(DvF.dot(kron(eye(2),Dv)).dot(kron(eye(2),Dyz)).dot(Phi)))#Constructs the bordered Hessian
    return Dyz,H,DzF,DyF,DvF,Dv,HV,MatrixEquation
    

def Check2ndOrder(Para,x0,rho0):
    '''
    Check the Bordered Hessian 2nd order conition
    '''
    N = len(Para.theta)
    S = len(Para.P)
    nQuant = 2*S*N+2*(N-1)*S
    k = getFOCNz(Para)-nQuant
    Nz = getFOCNz(Para)
    test = []
    Dyz,H = linearization(Para,x0,rho0)[0:2]
    H = fliplr(flipud(H)) #need to flip it to get it to match statement f the proof
    #(as it currently set up took derivatives of quantities first then Lagrange Multipliers )
    for j in range(2*k+1,Nz+1):
        test.append((-1)**(j-k)*linalg.det(H[:j,:j]))
    return all(test>0)
        
    
def getPhi(N,Nz):
    '''
    Computes the Phi matrix
    '''
    S = 2
    Phi_0 = zeros((2*(N-1),Nz))
    Phi_1 = zeros((2*(N-1),Nz))
    base = 2*2*N+N-1
    for i in range(0,N-1):
        Phi_0[i,base+i*S] = 1
        Phi_0[(N-1)+i,base+(N-1)*S+i*S] = 1
        Phi_1[i,base+i*S+1] = 1
        Phi_1[(N-1)+i,base+(N-1)*S+i*S+1] = 1
    return vstack((Phi_0,Phi_1))
    
def CMResiduals(z,x_i,rho_i,Para):
    '''
    Computest the complete market solution for the iid case
    '''
    theta_1 = Para.theta[0,:]
    theta_i = Para.theta[1:,:]
    alpha_1 = Para.alpha[0]
    alpha_i = Para.alpha[1:].reshape((-1,1))
    n_1 = Para.n[0]
    n_i = Para.n[1:].reshape((-1,1))
    beta = Para.beta
    g = Para.g
    P = Para.P[0,:]
    
    c1,ci,l1,li,mu_i,xi,phi_i,eta_i = getCMQuantities(z,Para)
    
    uc1 = Para.Uc(c1)
    ucc1 = Para.Ucc(c1)
    uci = Para.Uc(ci)
    ucci = Para.Ucc(ci)
    ul1 = Para.Ul(l1)
    ull1 = Para.Ull(l1)
    uli = Para.Ul(li)
    ulli = Para.Ull(li)
     
    res = array([])
    con = x_i - ((uci*ci+uli*li)-rho_i*(uc1*c1+ul1*l1)).dot(P).reshape((-1,1))/(1.-beta)
    res = hstack((res,con.flatten()))
    
    con = rho_i*ul1/theta_1-uli/theta_i
    res = hstack((res,con.flatten()))
    
    con = n_1*theta_1*l1 + sum(n_i*theta_i*li,axis=0)-g-n_1*c1-sum(n_i*ci,0)
    res = hstack((res,con.flatten()))
    
    con = rho_i*uc1-uci
    res = hstack((res,con.flatten()))
    
    foc = alpha_i*uci-mu_i*( ucci*ci+uci )-n_i*xi-eta_i*ucci
    res = hstack((res,foc.flatten()))
    
    foc = alpha_1*uc1+sum(mu_i*rho_i,0)*( ucc1*c1+uc1 )-n_1*xi + sum(eta_i*rho_i,0)*ucc1
    res = hstack((res,foc.flatten()))
    
    foc = alpha_i*uli - mu_i*( ulli*li+uli ) - phi_i*ulli/theta_i + n_i*theta_i*xi
    res = hstack((res,foc.flatten()))
    
    foc = alpha_1*ul1 + sum(mu_i*rho_i,0)*( ull1*l1 + ul1 ) + sum(phi_i*rho_i,0)*ull1/theta_1 + n_1*theta_1*xi
    res = hstack((res,foc.flatten()))
    
    return res
    
def CMfromMu(mu_i,x_i,rho_i,Para,z0):
    '''
    Given Mu computes complete markets outcomes
    '''
    beta = Para.beta

    P = Para.P[0,:]
    N = len(Para.theta)
    S = len(Para.P)
    zhat0= hstack((z0[:2*N*S],z0[2*N*S+N-1:]))
    def residuals(zhat):
        z = hstack((zhat[:2*N*S],mu_i.flatten(),zhat[2*N*S:]))
        return CMResiduals(z,x_i,rho_i,Para)[N-1:]
        
    sol = root(residuals,zhat0,tol=1e-14)
    if sol.success:
        zCM = hstack((sol.x[:2*N*S],mu_i.flatten(),sol.x[2*N*S:]))
        c1,ci,l1,li,mu_i,xi,phi_i,eta_i = getCMQuantities(zCM,Para)
        uc1 = Para.Uc(c1)
        uci = Para.Uc(ci)
        ul1 = Para.Ul(l1)
        uli = Para.Ul(li)
        return x_i - ((uci*ci+uli*li)-rho_i*(uc1*c1+ul1*l1)).dot(P).reshape((-1,1))/(1.-beta)
    else:
        return None

def getCMQuantities(z,Para):
    '''
    Gets quantities from z
    '''
    N = len(Para.theta)
    S = len(Para.P)
    c1 = z[0:S]
    
    ci = z[S:N*S].reshape((N-1,S))
    
    l1 = z[N*S:(N+1)*S]
    
    li = z[(N+1)*S:2*N*S].reshape((N-1,S))
    
    zi = 2*N*S
    
    mu_i = z[zi:zi+(N-1)].reshape((N-1,1))
    zi += (N-1)

    xi = z[zi:zi+S].reshape(S)
    zi += S    
    
    phi_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    eta_i = z[zi:zi+S*(N-1)].reshape((N-1,S))
    zi += S*(N-1)
    
    return c1,ci,l1,li,mu_i,xi,phi_i,eta_i
    
def SSz_to_CMz(z,Para):
    '''
    Transforms SS z to CM z
    '''
    N = len(Para.theta)
    S = len(Para.P)
    c1 = z[0:S]
    
    ci = z[S:N*S].reshape((N-1,S))
    
    l1 = z[N*S:(N+1)*S]
    
    li = z[(N+1)*S:2*N*S].reshape((N-1,S))
    
    zi = 2*N*S
    x_i = z[zi:zi+N-1].reshape((N-1,1))
    zi+= N-1
    
    rho_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1
    
    mu_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1
    
    lambda_i = z[zi:zi+N-1].reshape((N-1,1))
    zi += N-1
    
    mult = z[zi:]
    
    return hstack((c1,ci.flatten(),l1,li.flatten(),mu_i.flatten(),mult)),x_i,rho_i
    
def VCM(y,CMzbar,Para):
    N = len(Para.theta)
    x = y[0:N-1].reshape((-1,1))
    rho = y[N-1:].reshape((-1,1))
    sol = root(lambda z: CMResiduals(z,x,rho,Para),CMzbar)
    CMz = sol.x
    c1,ci,l1,li,mu_i,xi,phi_i,eta_i = getCMQuantities(CMz,Para)
    P = Para.P[0,:]
    alpha_1 = Para.alpha[0]
    alpha_i = Para.alpha[1:]
    U = alpha_1*Para.U(c1,l1)+alpha_i.dot(Para.U(ci,li))
    return hstack((P.dot(U)/(1-Para.beta),c1,ci.flatten())),sol.success
 
    
def constructHessianSymmetric(HVpartial,N):
    '''
    Constructs the Hessian matrix
    '''
    HV = zeros((2*(N-1),2*(N-1)))
    tiu = triu_indices(2*(N-1))
    dii = diag_indices(2*(N-1))
    HV[tiu] = HVpartial
    HV += HV.T
    HV[dii] /=2
    return HV
    
def constructHessianSymmetric_2agent(HVpartial,N):
    '''
    Constructs the Hessian from a partial sequence assumming 2 agent symmetries
    HVpartial = [V_xx,V_xx',V_xR,V_xR',V_RR,V_RR']
    '''
    HV = zeros((2*(N-1),2*(N-1)))
    dii = diag_indices(N-1)
    
    temp = HVpartial[1]*ones((N-1,N-1))
    temp[dii] = HVpartial[0]
    HV[:N-1,:N-1] = temp
    
    temp = HVpartial[3]*ones((N-1,N-1))
    temp[dii] = HVpartial[2]
    HV[N-1:,:N-1] = temp
    HV[:N-1,N-1:] = temp
    
    temp = HVpartial[5]*ones((N-1,N-1))
    temp[dii] = HVpartial[4]
    HV[N-1:,N-1:] = temp
    return HV
    
def getHVpartial_2agent(HV,N):
    '''
    Constructs the partial hessian list for two agents
    '''
    ret = zeros(6)
    ret[0] = HV[0,0]
    ret[1] = HV[0,1]
    ret[2] = HV[0,N-1]
    ret[3] = HV[0,N]
    ret[4] = HV[N-1,N-1]
    ret[5] = HV[N-1,N]
    return ret
    
def varianceEigenvalues(B,Para):
    '''
    Computes the eigenvalues of the variance map
    '''
    N = len(Para.theta)
    B1 = B[:2*(N-1),:]
    B2 = B[2*(N-1),:]
    P = Para.P[0,:]
    def fSigma(Sigma):
        Sigma = Sigma.reshape((2*(N-1),2*(N-1)))
        return (P[0]*B1.dot(Sigma).dot(B1.T) +P[1]*B2.dot(Sigma).dot(B2.T)).flatten()
        
    IS = eye(4*(N-1)**2)
    M = zeros(IS.shape)
    for i in range(0,len(IS)):
        M[:,i] = fSigma(IS[i,:])
    return linalg.eig(M)[0]        

    