import matplotlib.pyplot as plt
import numpy as np
import scipy.constants as constants
import time
plt.rcParams['font.family'] = ['Arial']
plt.rcParams['font.size'] = 14

class Estimator:
    """A base class to represent an estimator.

    This module contains the basic elements of an estimator, on which the
    subsequent DeadReckoning, Kalman Filter, and Extended Kalman Filter classes
    will be based on. A plotting function is provided to visualize the
    estimation results in real time.

    Attributes:
    ----------
        u : list
            A list of system inputs, where, for the ith data point u[i],
            u[i][1] is the thrust of the quadrotor
            u[i][2] is right wheel rotational speed (rad/s).
        x : list
            A list of system states, where, for the ith data point x[i],
            x[i][0] is translational position in x (m),
            x[i][1] is translational position in z (m),
            x[i][2] is the bearing (rad) of the quadrotor
            x[i][3] is translational velocity in x (m/s),
            x[i][4] is translational velocity in z (m/s),
            x[i][5] is angular velocity (rad/s),
        y : list
            A list of system outputs, where, for the ith data point y[i],
            y[i][1] is distance to the landmark (m)
            y[i][2] is relative bearing (rad) w.r.t. the landmark
        x_hat : list
            A list of estimated system states. It should follow the same format
            as x.
        dt : float
            Update frequency of the estimator.
        fig : Figure
            matplotlib Figure for real-time plotting.
        axd : dict
            A dictionary of matplotlib Axis for real-time plotting.
        ln* : Line
            matplotlib Line object for ground truth states.
        ln_*_hat : Line
            matplotlib Line object for estimated states.
        canvas_title : str
            Title of the real-time plot, which is chosen to be estimator type.

    Notes
    ----------
        The landmark is positioned at (0, 5, 5).
    """
    # noinspection PyTypeChecker
    def __init__(self, is_noisy=False):
        self.u = []
        self.x = []
        self.y = []
        self.x_hat = []  # Your estimates go here!
        self.t = []
        self.fig, self.axd = plt.subplot_mosaic(
            [['xz', 'phi'],
             ['xz', 'x'],
             ['xz', 'z']], figsize=(20.0, 10.0))
        self.ln_xz, = self.axd['xz'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_xz_hat, = self.axd['xz'].plot([], 'o-c', label='Estimated')
        self.ln_phi, = self.axd['phi'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_phi_hat, = self.axd['phi'].plot([], 'o-c', label='Estimated')
        self.ln_x, = self.axd['x'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_x_hat, = self.axd['x'].plot([], 'o-c', label='Estimated')
        self.ln_z, = self.axd['z'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_z_hat, = self.axd['z'].plot([], 'o-c', label='Estimated')
        self.canvas_title = 'N/A'

        # Defined in dynamics.py for the dynamics model
        # m is the mass and J is the moment of inertia of the quadrotor 
        self.gr = 9.81 
        self.m = 0.92
        self.J = 0.0023
        # These are the X, Y, Z coordinates of the landmark
        self.landmark = (0, 5, 5)

        # This is a (N,12) where it's time, x, u, then y_obs 
        if is_noisy:
            with open('noisy_data.npy', 'rb') as f:
                self.data = np.load(f)
        else:
            with open('data.npy', 'rb') as f:
                self.data = np.load(f)

        self.dt = self.data[-1][0]/self.data.shape[0]


    def run(self):
        for i, data in enumerate(self.data):
            self.t.append(np.array(data[0]))
            self.x.append(np.array(data[1:7]))
            self.u.append(np.array(data[7:9]))
            self.y.append(np.array(data[9:12]))
            if i == 0:
                self.x_hat.append(self.x[-1])
            else:
                self.update(i)
        return self.x_hat

    def update(self, _):
        raise NotImplementedError

    def plot_init(self):
        self.axd['xz'].set_title(self.canvas_title)
        self.axd['xz'].set_xlabel('x (m)')
        self.axd['xz'].set_ylabel('z (m)')
        self.axd['xz'].set_aspect('equal', adjustable='box')
        self.axd['xz'].legend()
        self.axd['phi'].set_ylabel('phi (rad)')
        self.axd['phi'].set_xlabel('t (s)')
        self.axd['phi'].legend()
        self.axd['x'].set_ylabel('x (m)')
        self.axd['x'].set_xlabel('t (s)')
        self.axd['x'].legend()
        self.axd['z'].set_ylabel('z (m)')
        self.axd['z'].set_xlabel('t (s)')
        self.axd['z'].legend()
        plt.tight_layout()

    def plot_update(self, _):
        self.plot_xzline(self.ln_xz, self.x)
        self.plot_xzline(self.ln_xz_hat, self.x_hat)
        self.plot_philine(self.ln_phi, self.x)
        self.plot_philine(self.ln_phi_hat, self.x_hat)
        self.plot_xline(self.ln_x, self.x)
        self.plot_xline(self.ln_x_hat, self.x_hat)
        self.plot_zline(self.ln_z, self.x)
        self.plot_zline(self.ln_z_hat, self.x_hat)

    def plot_xzline(self, ln, data):
        if len(data):
            x = [d[0] for d in data]
            z = [d[1] for d in data]
            ln.set_data(x, z)
            self.resize_lim(self.axd['xz'], x, z)

    def plot_philine(self, ln, data):
        if len(data):
            t = self.t
            phi = [d[2] for d in data]
            ln.set_data(t, phi)
            self.resize_lim(self.axd['phi'], t, phi)

    def plot_xline(self, ln, data):
        if len(data):
            t = self.t
            x = [d[0] for d in data]
            ln.set_data(t, x)
            self.resize_lim(self.axd['x'], t, x)

    def plot_zline(self, ln, data):
        if len(data):
            t = self.t
            z = [d[1] for d in data]
            ln.set_data(t, z)
            self.resize_lim(self.axd['z'], t, z)

    # noinspection PyMethodMayBeStatic
    def resize_lim(self, ax, x, y):
        xlim = ax.get_xlim()
        ax.set_xlim([min(min(x) * 1.05, xlim[0]), max(max(x) * 1.05, xlim[1])])
        ylim = ax.get_ylim()
        ax.set_ylim([min(min(y) * 1.05, ylim[0]), max(max(y) * 1.05, ylim[1])])

class OracleObserver(Estimator):
    """Oracle observer which has access to the true state.

    This class is intended as a bare minimum example for you to understand how
    to work with the code.

    Example
    ----------
    To run the oracle observer:
        $ python drone_estimator_node.py --estimator oracle_observer
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Oracle Observer'

    def update(self, _):
        self.x_hat.append(self.x[-1])


class DeadReckoning(Estimator):
    """Dead reckoning estimator.

    Your task is to implement the update method of this class using only the
    u attribute and x0. You will need to build a model of the unicycle model
    with the parameters provided to you in the lab doc. After building the
    model, use the provided inputs to estimate system state over time.

    The method should closely predict the state evolution if the system is
    free of noise. You may use this knowledge to verify your implementation.

    Example
    ----------
    To run dead reckoning:
        $ python drone_estimator_node.py --estimator dead_reckoning
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Dead Reckoning'
        self.time_step = 0
        self.old_x = None
        self.start_time = time.time()

    def update(self, _):
        if len(self.x_hat) > 0 and len(self.u) > self.time_step:
        # TODO: Your implementation goes here!
        # You may ONLY use self.u and self.x[0] for estimation
            if self.time_step == 0:
                self.old_x = self.x[0]
            u_1, u_2 = self.u[self.time_step][0], self.u[self.time_step][1]
            phi = self.old_x[2]
            term0 = self.old_x[3]
            term1 = self.old_x[4]
            term2 = self.old_x[5]
            term3 = (-u_1 * np.sin(phi)) / self.m
            term4 = -constants.g + (u_1 * np.cos(phi)) / self.m
            term5 = u_2 / self.J
            new_x = self.old_x + np.array([term0, term1, term2, term3, term4, term5]) * self.dt
            self.x_hat.append(new_x)
            self.old_x = new_x
            self.time_step += 1

            # calculate error
            all_errors = []
            for ground_truth, estimate in zip(self.x, self.x_hat):
                all_errors.append(np.linalg.norm(np.array(ground_truth[2:4]) - np.array(estimate[2:4])))
            all_errors = np.array(all_errors)
            avg_time = (time.time() - self.start_time) / self.time_step
            print(np.sqrt(np.mean(all_errors**2)), np.mean(np.abs(all_errors)), avg_time)

# noinspection PyPep8Naming
class ExtendedKalmanFilter(Estimator):
    """Extended Kalman filter estimator.

    Your task is to implement the update method of this class using the u
    attribute, y attribute, and x0. You will need to build a model of the
    unicycle model and linearize it at every operating point. After building the
    model, use the provided inputs and outputs to estimate system state over
    time via the recursive extended Kalman filter update rule.

    Hint: You may want to reuse your code from DeadReckoning class and
    KalmanFilter class.

    Attributes:
    ----------
        landmark : tuple
            A tuple of the coordinates of the landmark.
            landmark[0] is the x coordinate.
            landmark[1] is the y coordinate.
            landmark[2] is the z coordinate.

    Example
    ----------
    To run the extended Kalman filter:
        $ python drone_estimator_node.py --estimator extended_kalman_filter
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Extended Kalman Filter'
        # TODO: Your implementation goes here!
        # You may define the Q, R, and P matrices below.
        self.time_step = 0
        self.lx, self.ly, self.lz = self.landmark
        self.old_x = None
        self.start_time = time.time()
        self.A = np.eye(6)
        self.Q = np.diag([1, 1, 1, 0.1, 0.1, 0.1])
        self.R = np.diag([30, 10])
        self.P = np.diag([5, 5, 5, 1, 1, 1])
    # noinspection DuplicatedCode
    def update(self, i):
        if len(self.x_hat) > 0:
            # TODO: Your implementation goes here!
            # You may use self.u, self.y, and self.x[0] for estimation
            if i == 1:
                self.old_x = self.x_hat[0]
            u = self.u[i - 1]
            conditional_x = self.g(self.old_x, u) # extrapolated state 
            self.A = self.approx_A(self.old_x, u)
            P = self.A @ self.P @ self.A.T + self.Q
            self.C = self.approx_C(conditional_x)
            K = P @ self.C.T @ np.linalg.inv(self.C @ P @ self.C.T + self.R)
            new_x = conditional_x + K @ (self.h(conditional_x, self.y[i]))
            self.P = (np.eye(6) - K @ self.C) @ P
            self.x_hat.append(new_x)
            self.old_x = new_x

            # calculate error
            all_errors = []
            for ground_truth, estimate in zip(self.x, self.x_hat):
                all_errors.append(np.linalg.norm(np.array(ground_truth[2:4]) - np.array(estimate[2:4])))
            all_errors = np.array(all_errors)
            avg_time = (time.time() - self.start_time) / i
            print(np.sqrt(np.mean(all_errors**2)), np.mean(np.abs(all_errors)), avg_time)


    def g(self, x, u):
        u_1, u_2 = u
        phi = x[2]
        dv = x[3]
        dz = x[4]
        dphi = x[5]
        ddv = (-u_1 * np.sin(phi)) / self.m
        ddz = -constants.g + (u_1 * np.cos(phi)) / self.m
        ddphi = u_2 / self.J
        new_x = x + np.array([dv, dz, dphi, ddv, ddz, ddphi]) * self.dt
        return new_x

    def h(self, x_hat, y_obs):
        x, z, phi = x_hat[0], x_hat[1], x_hat[2]
        dist = ((self.lx - x) ** 2 + self.ly ** 2 + (self.lz - z) ** 2) ** 0.5
        h_x_hat = np.zeros((2, ))

        h_x_hat[0] = dist
        h_x_hat[1] = phi
        return y_obs - h_x_hat
  
    def approx_A(self, x, u):
        u_1, _ = u
        phi, dphi = x[2], x[5]
        dg = np.eye(6)
        dg[0, 3] = dg[1, 4] = dg[2, 5] = self.dt
        dg[3, 2] = -(u_1 * np.cos(phi) * dphi * self.dt) / self.m
        dg[4, 2] = -(u_1 * np.sin(phi) * dphi * self.dt) / self.m
        
        return dg

    
    def approx_C(self, x):
        x_i, z = x[0], x[1]
        dist = ((self.lx - x_i) ** 2 + (self.ly ** 2)+ (self.lz - z) ** 2) ** 0.5
        dh1_dx1 = -(self.lx - x_i)/dist
        dh1_dx2 = -(self.lz - z)/dist
        dh2_dx3 = 1
        dh_dx = np.zeros((2, 6))
        dh_dx[0, 0] = dh1_dx1
        dh_dx[0, 1] = dh1_dx2
        dh_dx[1, 2] = dh2_dx3
        return dh_dx
