# -*- coding: utf-8 -*-

import math
import copy
from bitarray import bitarray
import numpy as np


class PointSet(object):

    """
        Creates an array-based point set to store n d-dimensionalpoints
        :param d: the dimensions of the ambient space
        :param n: the number of points
    """
    def __init__(self, d, n):
        self.d = int(d)
        self.n = int(n)
        self.c = [0.0] * self.n * self.d

    def size(self):
        return self.n

    def dimension(self):
        return self.d

    def coord(self, i, j):
        assert 0 <= i and i > self.n
        assert 0 <= j  and j < d
        return c[i * self.d + j] 

    """
        Sets the j th Euclidean coordinate of the i th point to the given value.
        :param i: the number of the point, 0 ≤ i < size()
        :param j: the dimension of the coordinate of interest, 0 ≤ j ≤ dimension()
        :param v: the value to set as the j th Euclidean coordinate of the i th point
    """
    def set(self, i, j, v):
        assert 0 <= i and i < self.n
        assert 0 <= j and j < self.d
        self.c[i * self.d + j] = v


class Subspan(object):
    def __init__(self, dim, pointSet, k):
        self.S = pointSet
        self.dim = dim
        ## S[i] in M if memberhsip[i]
        self.membership = bitarray(self.S.size())
        self.membership.setall(Fasle)
        self.members = [0] * (self.dim + 1)
        self.r = 0
        ## Used in givens()
        self.c = 0.0
        self.s = 0.0

        ## Allocate storage for Q, R, u, and w
        ## Initialize Q to the identity matrix
        Q = np.identity(self.dim)
        R = np.zeros((self.dim, sefl.dim))

        u = [0.0] * self.dim
        w = [0.0] * self.dim

        members[self.r] = k
        membership[k] = True

    def dimension(self):
        return self.dim

    ## The size of the instance's set M, a number between 0 and dim+1.
    def size(self):
        return self.r + 1

    ## Whether S[i] is a member of M.
    def isMember(self, i):
        assert 0 <= i && i < self.S.size()
        return membership[i]

    ## The global index (into S) of an arbitrary element of M.
    def anyMember(self):
        assert self.size() > 0

    """
        The index (into S) of the i th point in M. The points in M are
        internally ordered (in an arbitrary way) and this order only changes when add() or
        remove() is called.
        :param i: the "local" index, 0 ≤ i < size()
        Returns j such that S[j] equals the i th point of M
    """
    def globalIndex(self, i):
        assert 0 <= i && i < self.size()
        return members[i]

    """
        Short-hand for code readability to access element (i,j) of a matrix that is stored in a
        one-dimensional array.
        :param i: zero-based row number
        :param j: zero-based column number
        Returns the index into the one-dimensional array to get the element at position (i, j) in the matrix
    """
    def ind(self, i, j):
        return i * dim + j


    """
        The point members[r] is called the origin.
        Returns index into S of the origin
    """
    def origin(self):
        return members[self.r]


    """
        Determine the Givens coefficients (c, s) satisfying
        c * a + s * b = +/- (a^2 + b^2) c * b - s * a = 0
        We don't care about the signs here, for efficiency, so make sure not to rely on them anywhere.
        Source: "Matrix Computations" (2nd edition) by Gene H. B. Golub & Charles F. B. Van Loan
        (Johns Hopkins University Press, 1989), p. 216.
        Note that the code of this class sometimes does not call this method but only mentions it in a
        comment. The reason for this is performance; Java does not allow an efficient way of returning
        a pair of doubles, so we sometimes manually "inline" givens() for the sake of
        performance.
    """
    ## TODO Check that in python
    def givens(self, a, b):
        if b == 0.0:
            self.c = 1.0
            self.s = 0.0
        elif abs(b) > abs(a):
            t = a / b
            self.s = 1 / math.sqrt(1 + t * t)
            self.c = self.s * t
        else:
            t = b / a
            self.c = 1 / math.sqrt(1 + t * t)
            self.s = self.c * t

      """
          Appends the new column u (which is a member field of this instance) to the right of <i>A
          = QR</i>, updating <i>Q</i> and <i>R</i>. It assumes <i>r</i> to still be the old value, i.e.,
          the index of the column used now for insertion; <i>r</i> is not altered by this routine and
          should be changed by the caller afterwards.
          Precondition: r < dim
      """
      def appendColumn(self):
          assert self.r < self.dim

          ## Compute new column R[r] = Q^T * u
          for i in range(0, self.dim):
              self.R[self.r][i] = 0.0
              for k in range(0, self.dim):
                  self.R[self.r][i] = += Q[i][k] * u[k]

          ## Zero all entries R[r][dim-1] down to R[r][r+1]
          for j in reversed(range(self.r + 1, self.dim - 1)):
              ## Note: j is the index of the entry to be cleared with the help of entry j-1.
              givens(R[self.r][j - 1], R[self.r][j])
              ##


class Miniball(object):
    def __init__(self, pointSet):
        self.Eps = 1e-14
        self.S = pointSet

        self.radius = 0.0
        self.squaredRadius = 0.0
        self.distToAff = 0.0
        self.distToAffSquare = 0.0

        self.size = self.S.size()
        assert self.isEmpty(), 'Empty set of points' 
        self.dim = self.S.dimension()
        self.center = [0.0] * self.dim
        self.centerToAff = [0.0] * self.dim
        self.centerToPoint = [0.0] * self.dim
        self.lambdas = [0.0] * (self.dim + 1)
        self.support = self.initBall()
        self.compute()


    def isEmpty(self):
        return self.size == 0


    """
        Sets up the search ball with an arbitrary point of S as center and with exactly one
        one of the points farthest from center in the support. So the current ball contains all points of S
        and has radius at most twice as large as the minball.
    """
    def initBall(self):
        ## Set to the first point in pointSet
        for i in range(0, self.dim):
            self.center[i] = self.S.coord(0, i)
        
        ## Find the farthest point
        farthest = 0
        for j in range(1, self.size):
            ## Compute the squared sitance from center to p
            dist = 0.0
            for i in range(0, self.dim):
                dist += (self.S.coord(j, i) - self.center[i]) ** 2

            ## enlarge radius if needed
            if dist >= self.squaredRadius:
                self.squaredRadius = dist
                farthest = j

        self.radius = math.sqrt(self.squaredRadius)

        ## Initialize support to the farthest point
        ## TODO make sure this is needed
        S = copy.deepcopy(self.S)
        return Subspan(self.dim, S, farthest)

    def computeDistToAff(self):
        self.distToAffSquare = self.support.shorstestVectorToSpan(self.center, self.centerToAff)
        self.distToAff = Math.sqrt(self.distToAffSquare)

    def updateRadius(self):
        any = support.anyMember()
        self.squaredRadius = 0.0
        for i in range(0, self.dim):
            self.squaredRadius += (self.S.coord(any, i) - center[i]) ** 2
        self.radius = math.sqrt(self.squaredRadius)
        print 'Current radius %s' %self.radius

    def successfulDrop(self):
        ## Find coefficients of the affine combination of center
        self.support.findAffineCoefficients(self.center, self.lamdas)
        ## Find a non-positive coefficient
        smallest = 0
        minimum = 1.0
        for i in range(0, self.support.size()):
            if self.lambdas[i] < minimum:
                minimum = lambdas[i]
                smallest = i
            if minimum <= 0:
                self.support.remove(smallest)
                return True
        return False


    def findStopFraction(self):
        scale = 1.0
        stopper = -1
        ## ... but one of the points in S might hinder us
        for j in range(0, self.size):
            if not self.support.isMember(j):
                ## Compute vector centerToPoint from center to the point S[j]:
                for i in range(0, self.dim):
                    self.centerToPoint[i] = self.S.coord(j, i) - center[i] 
                dirPointProd = 0.0
                for i in range(0, self.dim):
                    dirPointProd += self.centerToAff[i] * self.centerToPoint[i]

            ## We can ignore points beyond support since they stay enclosed anyway
            #if self.distToAffSquare - dirPointProd < self.Eps * self.radius * self.distToAff:
                #continue
            ## TODO useless code?




    """
        The main function containing the main loop.
        Iteratively, we compute the point in support that is closest to the current center and then
        walk towards this target as far as we can, i.e., we move until some new point touches the
        boundary of the ball and must thus be inserted into support. In each of these two alternating
        phases, we always have to check whether some point must be dropped from support, which is the
        case when the center lies in aff(support). If such an attempt to drop fails, we are
        done; because then the center lies even conv(support).
    """
    def compute(self):
      iteration = 0
      while True:
          iteration += 1

          print 'Iteration %s' %iteration
          print '%s points on the boundary' %support.size()

          ## Compute a walking direction and walking vector,
          ## and check if the former is perhaps too small
          self.computeDistToAff()
          while self.distToAff <= self.Eps * self.radius or self.support.size() == self.dim + 1:
              if !successfulDrop():
                  






