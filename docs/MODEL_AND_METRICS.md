# Model and Evaluation Notes

This note describes the equations used by the current lightweight 2D prototype. It is intended to make the implementation explainable during a class or research demo.

## Coordinate system

- \(x\): forward position along the route, in meters.
- \(y\): lateral position, in meters.
- \(\psi\): vehicle heading, in radians.
- \(v\): vehicle speed, in meters per second.
- \(\delta\): front-wheel steering angle, in radians.

The road centerline is a deterministic sinusoidal curve:

\[
y_c(x) = A \sin(kx)
\]

where \(A\) is curve amplitude and \(k\) is curve frequency. Lane boundaries are offset from the centerline by half the configured lane width.

## Vehicle model

The vehicle uses a kinematic bicycle approximation. For normalized throttle \(u_t\), brake \(u_b\), steering \(u_s\), and time step \(\Delta t\):

\[
a = u_t a_{\max} - u_b b_{\max}
\]

\[
v_{t+\Delta t} = \max(0, v_t + a\Delta t)
\]

The normalized steering input is mapped to a physical steering angle:

\[
\delta = u_s \delta_{\max}
\]

The heading and position are advanced using:

\[
\psi_{t+\Delta t} = \psi_t + \frac{v}{L}\tan(\delta)\Delta t
\]

\[
x_{t+\Delta t} = x_t + v\cos(\psi_{t+\Delta t})\Delta t
\]

\[
y_{t+\Delta t} = y_t + v\sin(\psi_{t+\Delta t})\Delta t
\]

Here \(L\) is the vehicle wheelbase. This is a simplified low-speed kinematic model; it does not simulate tire forces, slip, suspension, or complex vehicle dynamics.

## Pure-pursuit lane follower

The controller selects a target point on the road centerline a fixed look-ahead distance \(L_d\) ahead. Let \(\alpha\) be the angle between the vehicle heading and the line from the vehicle to that target point.

\[
\kappa = \frac{2\sin(\alpha)}{L_d}
\]

\[
\delta = \arctan(L\kappa)
\]

The requested steering angle is normalized by the vehicle's maximum steering angle and clamped to the allowed control range. Speed uses a proportional controller around the configured target speed.

## Planar range sensor and safety controller

The optional range sensor casts evenly spaced rays across a configurable field of view. Each ray is intersected with the circular obstacle approximations in world coordinates. A hit reports the distance to the obstacle surface; a ray with no hit reports the configured maximum range.

The safety controller first computes the pure-pursuit steering and speed command. It then estimates stopping distance using

\\[
d_{stop} = \\frac{v^2}{2b_{max}} + d_{margin}
\\]

where \\(v\\) is current speed, \\(b_{max}\\) is maximum braking deceleration, and \\(d_{margin}\\) is a configurable safety margin. When a detected obstacle in the vehicle's forward path is within this distance, the controller requests full braking and retains the baseline steering command.

This is a deterministic geometric range-sensing approximation. It is not physical LiDAR, does not model sensor noise or occlusion, and is not a complete collision-avoidance planner.

## Metrics

- **Mean lane deviation:** average absolute lateral distance between the vehicle and road centerline, in meters.
- **Collision events:** count of modeled contacts between the vehicle footprint approximation and stationary circular obstacles.
- **Collision rate per kilometer:** collision events divided by traveled kilometers. It is undefined when no distance has been traveled.
- **Route completion:** forward route distance completed divided by total route length, expressed as a percentage.
- **Steering MAE:** average absolute difference between predicted and expert steering. It remains unavailable until paired expert/predicted steering samples exist.

## Important limitations

These equations and metrics describe the current 2D prototype only. They do not imply CARLA integration, camera perception, dynamic traffic, a trained neural network, or real-vehicle capability. The model is useful for testing software structure and demonstrating a transparent controller before moving to a higher-fidelity simulator.
