import os
import shutil
import time
import numpy
import json
import bisect
import plot
import distribution
import spike_train
import synapse
import datalgo
import utility


class TestInfo:
    def __init__(self, test_name, output_dir):
        self.test_name = test_name
        self.output_dir = output_dir


def _test_distribution(info):
    """
    The test builds 5 distributions. Four of them are with numeric events
    and one is with string events. For each distribution there is generated
    a sequence of events and then histogram of counts of the events is
    build, which should match the histogram the distribution was built from.
    """
    assert isinstance(info, TestInfo)

    def doit(hist, n, ofile):
        xhist = hist.copy()
        for k in xhist.keys():
            xhist[k] = 0
        isi = distribution.Distribution(hist)
        print(isi)
        ofile.write(str(isi) + "\n")
        for _ in range(n):
            e = isi.next_event()
            assert e in hist.keys()
            xhist[e] += 1
        osum = 0.0
        xsum = 0.0
        for k in hist.keys():
            osum += hist[k]
            xsum += xhist[k]
        if xsum > 0:
            for k in xhist.keys():
                xhist[k] *= osum / xsum
        return xhist

    def show(hist, xhist, ofile):
        for k in sorted(hist.keys()):
            msg = str(k) + ": " + str(hist[k]) + " ; " + str(xhist[k])
            print(msg)
            ofile.write(msg + "\n")

    with open(os.path.join(info.output_dir, "results.txt"), "w") as ofile:
        for hist in [
                {1: 1},
                {123: 10},
                {1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
                {"A": 2, "B": 4, "C": 10, "D": 2, "E": 3},
                {10: 60, 20: 100, 30: 65, 40: 35, 50: 20, 60: 10, 70: 5, 80: 3, 90: 2, 100: 1}
                ]:
            print("*******************************************************")
            ofile.write("*******************************************************\n")
            show(hist, doit(hist, 10000, ofile), ofile)
    return 0


def _test_hermit_distribution(info):
    """
    The test build 10 hermit distributions, each for a different
    peek. Curves and histograms and normalised histograms are build
    and corresponding plots are saved.
    """
    assert isinstance(info, TestInfo)
    print("  Generating graph " + os.path.join(info.output_dir, "ns_curve.png"))
    plot.curve(
        distribution.make_points_of_normal_distribution(
            num_points=100,
            nu=0.0,
            sigma=1.0,
            normalise=True
            ),
        os.path.join(info.output_dir, "ns_curve.png")
        )
    for peek_x in numpy.arange(0.1, 0.95, 0.1, float):
        print("  Computing points of hermit cubic at peek " + str(peek_x) + ".")
        points = datalgo.move_scale_curve_points(
                    distribution.make_points_of_hermit_cubic_approximation_of_normal_distribution(
                        peek_x=peek_x,
                        mult_m01=1.0,
                        mult_mx=1.0,
                        num_points=100
                        ),
                    scale_x=0.298,
                    scale_y=10,
                    pow_y=1.5,
                    shift_x=0.002
                    )
        print("  Saving " + os.path.join(info.output_dir, "ns_curve_hermit_adapted_" + format(peek_x, ".2f") + ".png"))
        plot.curve(
            points,
            os.path.join(info.output_dir, "ns_curve_hermit_adapted_" + format(peek_x, ".2f") + ".png")
            )
        print("  Computing histogram from the hermit cubic.")
        hist = datalgo.make_histogram_from_points(points)
        print("  Saving " + os.path.join(info.output_dir, "ns_hist_adapted_" + format(peek_x, ".2f") + ".png"))
        plot.histogram(
            hist,
            os.path.join(info.output_dir, "ns_hist_adapted_" + format(peek_x, ".2f") + ".png"),
            normalised=False
            )
        print("  Saving " + os.path.join(info.output_dir, "ns_hist_normalised_adapted_" +
                                         format(peek_x, ".2f") + ".png"))
        plot.histogram(
            hist,
            os.path.join(info.output_dir, "ns_hist_normalised_adapted_" + format(peek_x, ".2f") + ".png"),
            normalised=True
            )
        print("  Saving " + os.path.join(info.output_dir, "hd_" + format(peek_x, ".2f") + ".png"))
        plot.histogram(
            distribution.hermit_distribution(peek_x),
            os.path.join(info.output_dir, "hd_" + format(peek_x, ".2f") + ".png"),
            )

    return 0


def _test_synapse(info):
    """
    The test checks functionality of all four supported plastic
    synapses (namely, 'np','pn','pp', and 'nn'). For each type
    there are generated plots of progress of input variables,
    synaptic weights, and changes of weights w.r.t pre- and
    post- spikes.
    """
    assert isinstance(info, TestInfo)
    for the_synapse in [
            synapse.Synapse.plastic_peek_np(),
            synapse.Synapse.plastic_peek_pn(),
            synapse.Synapse.plastic_peek_pp(),
            synapse.Synapse.plastic_peek_nn(),
            ]:
        print("  Starting simulation of '" + the_synapse.get_name() + "'.")

        start_time = 0.0
        dt = 0.001
        nsteps = 20000

        pre_spikes_train = spike_train.create(distribution.default_excitatory_isi_distribution(), 0.0)
        post_spikes_train = spike_train.create(distribution.default_excitatory_isi_distribution(), 0.0)
        # pre_spikes_train = spike_train.spike_train(
        #     distribution.distribution({}),
        #     [0.001],
        #     start_time
        #     )
        # post_spikes_train = spike_train.spike_train(
        #     distribution.distribution({}),
        #     [0.002],
        #     start_time
        #     )

        synapse_recording = {"last_pre_times": [], "last_post_times": []}
        for var, value in the_synapse.get_variables().items():
            synapse_recording[var] = []

        last_pre_spike_time = start_time
        last_post_spike_time = start_time
        t = start_time
        for step in range(nsteps):
            utility.print_progress_string(step, nsteps)

            the_synapse.integrate(dt)

            was_pre_spike_generated = pre_spikes_train.on_time_step(t, dt)
            if was_pre_spike_generated:
                the_synapse.on_pre_synaptic_spike()
                last_pre_spike_time = t + dt
            was_post_spike_generated = post_spikes_train.on_time_step(t, dt)
            if was_post_spike_generated:
                the_synapse.on_post_synaptic_spike()
                last_post_spike_time = t + dt

            for var, value in the_synapse.get_variables().items():
                synapse_recording[var].append((t + dt, value))
            synapse_recording["last_pre_times"].append(last_pre_spike_time)
            synapse_recording["last_post_times"].append(last_post_spike_time)

            t += dt

        print("  Saving results.")

        output_dir = os.path.join(info.output_dir, the_synapse.get_name())

        for var in the_synapse.get_variables().keys():
            pathname = os.path.join(output_dir, "synapse_var_" + var + ".png")
            if var == the_synapse.get_weight_variable_name():
                title = the_synapse.get_short_description()
            else:
                title = None
            print("    Saving plot " + pathname)
            plot.curve(
                synapse_recording[var],
                pathname,
                title=title,
                colours="C1"
                )

        weights_delta = []
        for i in range(1, len(synapse_recording[the_synapse.get_weight_variable_name()])):
            t, w = synapse_recording[the_synapse.get_weight_variable_name()][i]
            pre_t = synapse_recording["last_pre_times"][i]
            post_t = synapse_recording["last_post_times"][i]
            w0 = synapse_recording[the_synapse.get_weight_variable_name()][i - 1][1]
            weights_delta.append((post_t - pre_t, w - w0))
        weights_delta.sort(key=lambda pair: pair[0])

        pathname = os.path.join(output_dir, "plasticity.png")
        print("    Saving plot " + pathname)
        plot.scatter(
            datalgo.merge_close_points_by_add(weights_delta, dt),
            pathname,
            xaxis_name="post_t - pre_t",
            faxis_name="weight delta"
            )

    return 0


def _test_default_excitatory_isi_distribution(info):
    """
    The test creates the default excitatory ISI distribution, and
    uses it to generate 10000 events (ISIs). Then plot of the ISI
    histogram is saved.
    """
    assert isinstance(info, TestInfo)
    plot.histogram(
        datalgo.make_histogram(
            distribution.default_excitatory_isi_distribution().generate(100000),
            0.001,
            0.0,
            ),
        os.path.join(info.output_dir, "default_excitatory_isi_distribution.png"),
        normalised=False,
        title="default_excitatory_isi_distribution " + plot.get_title_placeholder()
        )
    return 0


def _test_default_inhibitory_isi_distribution(info):
    """
    The test creates the default inhibitory ISI distribution, and
    uses it to generate 10000 events (ISIs). Then plot of the ISI
    histogram is saved.
    """
    assert isinstance(info, TestInfo)
    plot.histogram(
        datalgo.make_histogram(
            distribution.default_inhibitory_isi_distribution().generate(100000),
            0.00025,
            0.0,
            ),
        os.path.join(info.output_dir, "default_inhibitory_isi_distribution.png"),
        normalised=False,
        title="default_inhibitory_isi_distribution " + plot.get_title_placeholder()
        )
    return 0


def _test_spike_trains(info):
    """
    The test generates several excitatory and inhibitory spike strains.
    Each excitatory/inhibitory spike train differs from another one by
    a different level of noise in time intervals between individual
    spikes. Nevertheless, spiking distribution is preserved for each
    spike train for any chosen level of noise.
    """
    assert isinstance(info, TestInfo)

    start_time = 0.0
    dt = 0.001
    nsteps = 5 * 60 * 1000
    num_spikers_per_kind = 11

    trains = [spike_train.create(distribution.default_excitatory_isi_distribution(), 10.0 * i)
              for i in range(num_spikers_per_kind)] +\
             [spike_train.create(distribution.default_inhibitory_isi_distribution(), 10.0 * i)
              for i in range(num_spikers_per_kind)]

    t = start_time
    for step in range(nsteps):
        utility.print_progress_string(step, nsteps)
        for train in trains:
            train.on_time_step(t, dt)
        t += dt

    print("  Saving results.")

    for i, train in enumerate(trains):
        if i < num_spikers_per_kind:
            train_id = "excitatory[" + str(i) + "]"
            colour = plot.get_colour_pre_excitatory(0.75)
        else:
            train_id = "inhibitory[" + str(i - num_spikers_per_kind) + "]"
            colour = plot.get_colour_pre_inhibitory(0.75)

        file_name = train_id + "_info.json"
        pathname = os.path.join(info.output_dir, file_name)
        print("    Saving info " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps({"configuration": train.get_configuration(), "statistics": train.get_statistics()},
                                   sort_keys=True,
                                   indent=4))

        file_name = train_id + "_isi_histogram.png"
        pathname = os.path.join(info.output_dir, file_name)
        print("    Saving plot " + pathname)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(
                    train.get_spikes_history()
                    ),
                dt,
                start_time
                ),
            pathname,
            False,
            colour,
            plot.get_title_placeholder()
            )

        # file_name = train_id + "_histogram_reguatory_lengths.png"
        # pathname = os.path.join(info.output_dir, file_name)
        # print("    Saving plot " + pathname)
        # plot.histogram(
        #     train.get_regularity_length_distribution(),
        #     pathname,
        #     False,
        #     colour,
        #     plot.get_title_placeholder()
        #     )
        #
        # file_name = train_id + "_histogram_noise_lengths.png"
        # pathname = os.path.join(info.output_dir, file_name)
        # print("    Saving plot " + pathname)
        # plot.histogram(
        #     train.get_noise_length_distribution(),
        #     pathname,
        #     False,
        #     colour,
        #     plot.get_title_placeholder()
        #     )

        isi_delta =\
            datalgo.make_function_from_events(
                datalgo.make_difference_events(
                    datalgo.make_difference_events(
                        train.get_spikes_history()
                        )
                    )
                )
        plot.curve_per_partes(
            isi_delta,
            os.path.join(info.output_dir, train_id + "_isi_delta_curve.png"),
            0,
            len(isi_delta),
            1000,
            None,
            lambda p: print("    Saving plot " + p),
            colour,
            plot.get_title_placeholder()
            )

    return 0


def _test_surface_under_function(info):
    """
    Test of the function 'utility.compute_surface_under_function'
    on constant, linear, and quadratic functions.
    """
    assert isinstance(info, TestInfo)
    data = [
        # Each element is a tuple (function, x_lo, x_hi, delta_x, correct_result, func_text)
        (lambda x: 2.0, -1.0, 2.0, 0.01, 6.0, "lambda x: 2.0"),
        (lambda x: 3 - x, 0.0, 3.0, 0.0005, 4.5, "lambda x: 3 - x"),
        (lambda x: x**2 - 1, -2.0, 2.0, 0.001, 2.0*(-2.0/3.0 + 4.0/3.0), "lambda x: x**2 - 1")
        ]
    num_failures = 0
    for func, x_lo, x_hi, delta_x, correct_result, func_text in data:
        result = utility.compute_surface_under_function(func, x_lo, x_hi, None, delta_x)
        if abs(result - correct_result) > 0.001:
            print("FAILURE: func=" + func_text +
                  ", x_lo=" + str(x_lo) +
                  ", x_hi=" + str(x_hi) +
                  ", delta_x=" + str(delta_x) +
                  ", correct_result=" + str(correct_result) +
                  ", computed_result=" + str(result)
                  )
            num_failures += 1
    return num_failures


# class SpikesWindow:
#     def __init__(
#             self,
#             spiking_distribution,
#             percentage_of_regularity_phases,
#             noise_length_distribution,
#             regularity_length_distribution,
#             max_spikes_buffer_size,
#             regularity_chunk_size
#             ):
#         self._train = spike_train.SpikeTrain(
#                             spiking_distribution,
#                             percentage_of_regularity_phases,
#                             noise_length_distribution,
#                             regularity_length_distribution,
#                             max_spikes_buffer_size,
#                             regularity_chunk_size,
#                             lambda last_recording_time, current_time: True
#                             )
#
#     def get_next_spike_time_after(self, t):
#         pass


class CorrelatingSpikeTrain:
    def __init__(self, pivot, deviation, ideal_buffer_size=100):
        assert isinstance(pivot, spike_train.SpikeTrain) or isinstance(pivot, CorrelatingSpikeTrain)
        assert isinstance(deviation, distribution.Distribution)
        assert min(deviation.get_events()) >= -1 and max(deviation.get_events()) <= 1
        assert isinstance(ideal_buffer_size, int) and ideal_buffer_size > 0
        self._pivot = pivot
        self._deviation = deviation
        self._event_buffer = []
        self._ideal_buffer_size = ideal_buffer_size
        self._next_spike_time = None
        self._last_pivot_index = 0
        self._spikes_history = []

    def get_spikes_history(self):
        return self._spikes_history

    def get_next_spike_time(self):
        return self._next_spike_time

    @staticmethod
    def choose_event_index(events, pivot_event, correlation_coefficient):
        assert isinstance(events, list) and len(events) > 0
        assert isinstance(pivot_event, float) and pivot_event > 0
        assert isinstance(correlation_coefficient, float) and -1 <= correlation_coefficient and correlation_coefficient <= 1
        random_event = numpy.random.uniform(events[0], events[-1])
        if correlation_coefficient < 0:
            correlated_event = events[(bisect.bisect_left(events, pivot_event) + len(events) // 2) % len(events)]
            # correlated_event = events[-bisect.bisect_left(events, pivot_event)]
            # if abs(events[0] - pivot_event) < abs(events[-1] - pivot_event):
            #     correlated_event = events[-1]
            # else:
            #     correlated_event = events[0]
        else:
            correlated_event = pivot_event
        param = abs(correlation_coefficient)
        selected_event = (1 - param) * random_event + param * correlated_event
        idx = bisect.bisect_left(events, selected_event)
        return min(idx, len(events) - 1)

    def on_time_step(self, t, dt):
        if self._next_spike_time is None:
            self._next_spike_time = t
            if self._pivot.get_next_spike_time() is None:
                self._pivot.on_time_step(t, dt)
        elif self._next_spike_time > t + 1.5 * dt:
            return False
        else:
            self._spikes_history.append(t + dt)
        while len(self._event_buffer) < self._ideal_buffer_size:
            while self._last_pivot_index >= len(self._pivot.get_spikes_history()):
                t0 = t
                while t0 + dt < self._pivot.get_next_spike_time():
                    t0 += dt
                old_len = len(self._pivot.get_spikes_history())
                self._pivot.on_time_step(t0, dt)
                assert old_len + 1 == len(self._pivot.get_spikes_history())
            prev = self._pivot.get_spikes_history()[self._last_pivot_index - 1] if self._last_pivot_index > 0 else 0.0
            bisect.insort_left(self._event_buffer, self._pivot.get_spikes_history()[self._last_pivot_index] - prev)
            self._last_pivot_index += 1
        pivot_next_time = self._pivot.get_spikes_history()[
            bisect.bisect_left(self._pivot.get_spikes_history(), self._next_spike_time + dt)
            ]
        to_pivot_time = pivot_next_time - self._next_spike_time
        assert to_pivot_time > 0
        correlation_coefficient = self._deviation.next_event()
        idx = self.choose_event_index(self._event_buffer, to_pivot_time, correlation_coefficient)
        assert idx >= 0 and idx < len(self._event_buffer)
        # assert abs(self._next_spike_time + self._event_buffer[idx] - pivot_next_time) < 0.0001
        self._next_spike_time += self._event_buffer[idx]

        self._event_buffer.pop(idx)
        assert self._next_spike_time > t + dt
        return True


def _test_aligned_spike_trains(info):
    """
    Checks alignment of spike trains for different alignment coefficients.
    """
    assert isinstance(info, TestInfo)


    # def make_alignment_histogram(name, lo_event, hi_event, dt, num_events=None):
    #     if num_events is None:
    #         num_events = int((hi_event - lo_event) / dt) + 1
    #     raw_events = [lo_event + (i / float(num_events - 1)) * (hi_event - lo_event) for i in range(0, num_events)]
    #     events = []
    #     for e in raw_events:
    #         t = 0.0
    #         while e > t + 1.5 * dt:
    #             t += dt
    #         events.append(t)
    #     half_epsilon = 0.5 * (dt / 10)
    #     coefs = []
    #     for i in range(len(events)):
    #         for j in range(i + 1, len(events)):
    #             dist = events[j] - events[i]
    #             shift = dt
    #             while shift < dist:
    #                 if not (shift < half_epsilon or shift > dist - half_epsilon):
    #                     # print(format(shift, ".3f") + " / " + format(dist, ".3f") + " = " + format(shift/dist, ".3f") +
    #                     #       "  --->  " +
    #                     #       format(shift/dt, ".3f") + " / " + format(dist / dt, ".3f") + " = " + format((shift/dt)/(dist/dt), ".3f"))
    #                     coef = max(-1.0, min(2.0 * shift / dist - 1.0, 1.0))
    #                     coefs.append(coef)
    #                 shift += dt
    #     coefs = sorted(coefs)
    #     hist = datalgo.make_histogram(coefs, 0.005, 0.0, 1)
    #     plot.histogram(
    #         hist,
    #         os.path.join(info.output_dir, name + ".png"),
    #         normalised=False
    #         )
    #     return 0
    # make_alignment_histogram("xhist", 0.003, 0.030, 0.0001)
    # make_alignment_histogram("yhist", 0.003, 0.130, 0.0001)
    # return 0

    seed = 0

    def get_next_seed():
        nonlocal seed
        seed += 1
        return seed

    numpy.random.seed(get_next_seed())

    def make_spike_train(is_excitatory=True, mean_frequency=None, percentage_of_regularity_phases=None, seed=None):
        # min_event = 0.003
        # max_event = 0.030
        # num_events = 28
        # return spike_train.create(
        #             distribution.Distribution(
        #                 {(min_event + (i / float(num_events - 1)) * (max_event - min_event)): 1.0 / float(num_events)
        #                  for i in range(0, num_events)},
        #                 seed
        #                 ),
        #             0.0
        #             )
        if mean_frequency is None:
            mean_frequency = 15.0 if is_excitatory else 60.0
        if percentage_of_regularity_phases is None:
            percentage_of_regularity_phases = 0.0
        return spike_train.create(
                    distribution.hermit_distribution_with_desired_mean(1.0 / mean_frequency, 0.003, 0.3, 0.0001, pow_y=2, seed=seed)
                        if is_excitatory
                        else distribution.hermit_distribution_with_desired_mean(1.0 / mean_frequency, 0.001, 0.08, 0.0001, bin_size=0.0002, pow_y=2, seed=seed),
                    percentage_of_regularity_phases
                    )

    pivot_trains = [
        (make_spike_train(True, seed=get_next_seed()), "epivot"),
        (make_spike_train(False, seed=get_next_seed()), "ipivot"),
        ]

    nsteps = 1000000
    dt = 0.0001
    start_time = 0.0

    def simulate_trains(trains):
        t = start_time
        for step in range(nsteps):
            utility.print_progress_string(step, nsteps)
            for train, _ in trains:
                train.on_time_step(t, dt)
            t += dt

    print("Simulating pivot trains")
    simulate_trains(pivot_trains)

    def make_aligned_train(
            pivot, alignment_coefficient, dispersion_fn,
            is_excitatory=True, mean_frequency=None, seed=None
            ):
        assert isinstance(pivot, spike_train.SpikeTrain)
        train = make_spike_train(is_excitatory, mean_frequency, 0.0, seed)
        train.set_spike_history_alignment(pivot.get_spikes_history(), alignment_coefficient, dispersion_fn)
        return train

    dispersion_fn = datalgo.AlignmentDispersionToSpikesHistory(2.0)

    other_trains = [
        (make_spike_train(True, seed=get_next_seed()), "eunaligned"),
        (make_spike_train(False, seed=get_next_seed()), "iunaligned"),
        ] + [
        (make_aligned_train(pivot, coef, dispersion_fn, kind, seed=get_next_seed()),
         kname + "aligned(" + desc + "," + format(coef, ".2f") + ")")
            for pivot, desc in pivot_trains
            for kind, kname in [(True, "e"), (False, "i")]
            for coef in [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
        ]

    print("Simulating other trains")
    simulate_trains(other_trains)

    print("Saving results:")
    for pivot, pivot_desc in pivot_trains:
        print("    Saving statistics of spike train: " + pivot_desc)
        with open(os.path.join(info.output_dir, "stats_" + pivot_desc + ".json"), "w") as ofile:
            ofile.write(json.dumps({"configuration": pivot.get_configuration(), "statistics": pivot.get_statistics()},
                                   sort_keys=True,
                                   indent=4))
        print("    Saving spike event distributions of spike train: " + pivot_desc)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(pivot.get_spikes_history()),
                dt,
                start_time
                ),
            os.path.join(info.output_dir, "distrib_" + pivot_desc + ".png"),
            normalised=False
            )
    for other, other_desc in other_trains:
        print("    Saving statistics of spike train: " + other_desc)
        with open(os.path.join(info.output_dir, "stats_" + other_desc + ".json"), "w") as ofile:
            ofile.write(json.dumps({"configuration": other.get_configuration(), "statistics": other.get_statistics()},
                                   sort_keys=True,
                                   indent=4))
        print("    Saving spike event distributions of spike train: " + other_desc)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(other.get_spikes_history()),
                dt,
                start_time
                ),
            os.path.join(info.output_dir, "distrib_" + other_desc + ".png"),
            normalised=False
            )
    for pivot, pivot_desc in pivot_trains:
        for other, other_desc in other_trains:
            print("    Saving alignment histograms: " + pivot_desc + " VS " + other_desc)
            hist_pair = datalgo.make_alignment_histograms_of_spike_histories(
                                pivot.get_spikes_history(),
                                other.get_spikes_history(),
                                0.005,
                                dt / 2.0
                                )
            plot.histogram(
                hist_pair[0],
                os.path.join(info.output_dir, "hist_" + pivot_desc + "_vs_" + other_desc + ".png"),
                normalised=False
                )
            plot.histogram(
                hist_pair[1],
                os.path.join(info.output_dir, "hist_" + pivot_desc + "_vs_" + other_desc + "_inv.png")
                )
            print("    Saving alignment curve: " + pivot_desc + " VS " + other_desc)
            with plot.Plot(os.path.join(info.output_dir, "curve_" + pivot_desc + "_vs_" + other_desc + ".png")) as plt:
                plt.curve(
                    datalgo.interpolate_discrete_function(
                        datalgo.approximate_discrete_function(
                            distribution.Distribution(hist_pair[0]).get_probability_points()
                            )
                        ),
                    legend=pivot_desc + " -> " + other_desc
                    )
                plt.curve(
                    datalgo.interpolate_discrete_function(
                        datalgo.approximate_discrete_function(
                            distribution.Distribution(hist_pair[1]).get_probability_points()
                            )
                        ),
                    legend=other_desc + " -> " + pivot_desc
                    )
        plot.event_board_per_partes(
            [pivot.get_spikes_history()] + [other.get_spikes_history() for other, _ in other_trains],
            os.path.join(info.output_dir, "spikes_board_" + pivot_desc + ".png"),
            start_time,
            start_time + nsteps * dt,
            1.0,
            5,
            lambda p: print("    Saving spikes board part: " + os.path.basename(p)),
            [[plot.get_random_rgb_colour()] * len(pivot.get_spikes_history())] +
                [[plot.get_random_rgb_colour()] * len(other.get_spikes_history())
                 for other, _ in other_trains],
            " " + plot.get_title_placeholder() + " SPIKES BOARD"
            )

    return 0    # No failures


def _test_alignment_of_aligned_spike_trains(info):
    """
    Checks alignment of spike trains all aligned to a pivot
    spike train. Test is conducted for several alignment
    coefficients.
    """
    assert isinstance(info, TestInfo)

    seed = 0

    def get_next_seed():
        nonlocal seed
        seed += 1
        return seed

    numpy.random.seed(get_next_seed())

    def make_spike_train(is_excitatory=True, mean_frequency=None, percentage_of_regularity_phases=None, seed=None):
        if mean_frequency is None:
            mean_frequency = 15.0 if is_excitatory else 60.0
        if percentage_of_regularity_phases is None:
            percentage_of_regularity_phases = 0.0
        return spike_train.create(
                    distribution.hermit_distribution_with_desired_mean(1.0 / mean_frequency, 0.003, 0.3, 0.0001, pow_y=2, seed=seed)
                        if is_excitatory
                        else distribution.hermit_distribution_with_desired_mean(1.0 / mean_frequency, 0.001, 0.08, 0.0001, bin_size=0.0002, pow_y=2, seed=seed),
                    percentage_of_regularity_phases
                    )

    pivot_trains = [
        (make_spike_train(True, seed=get_next_seed()), "epivot"),
        (make_spike_train(False, seed=get_next_seed()), "ipivot"),
        ]

    nsteps = 1000000
    dt = 0.0001
    start_time = 0.0

    def simulate_trains(trains):
        t = start_time
        for step in range(nsteps):
            utility.print_progress_string(step, nsteps)
            for train, _ in trains:
                train.on_time_step(t, dt)
            t += dt

    print("Simulating pivot trains")
    simulate_trains(pivot_trains)

    def make_aligned_train(
            pivot, alignment_coefficient, dispersion_fn,
            is_excitatory=True, mean_frequency=None, seed=None
            ):
        assert isinstance(pivot, spike_train.SpikeTrain)
        train = make_spike_train(is_excitatory, mean_frequency, 0.0, seed)
        train.set_spike_history_alignment(pivot.get_spikes_history(), alignment_coefficient, dispersion_fn)
        return train

    dispersion_fn = datalgo.AlignmentDispersionToSpikesHistory(2.0)

    other_trains = [[(make_aligned_train(pivot, coef, dispersion_fn, kind, seed=get_next_seed()),
                      kname + str(idx) + "_" + format(coef, ".2f"))
                        for kind, kname in [(True, "e"), (False, "i")]
                        for idx in range(2)
                        for coef in [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
                        ] for pivot, _ in pivot_trains]

    print("Simulating other trains")
    simulate_trains([train for pivot_trains in other_trains for train in pivot_trains])

    print("Saving results:")
    for pivot_desc_pair, pivot_trains in zip(pivot_trains, other_trains):
        pivot = pivot_desc_pair[0]
        pivot_desc = pivot_desc_pair[1]
        outdir = os.path.join(info.output_dir, pivot_desc)
        os.makedirs(outdir, exist_ok=True)
        print("    Saving statistics of spike train: " + pivot_desc)
        with open(os.path.join(outdir, "stats_" + pivot_desc + ".json"), "w") as ofile:
            ofile.write(json.dumps({"configuration": pivot.get_configuration(), "statistics": pivot.get_statistics()},
                                   sort_keys=True,
                                   indent=4))
        print("    Saving spike event distributions of spike train: " + pivot_desc)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(pivot.get_spikes_history()),
                dt,
                start_time
                ),
            os.path.join(outdir, "distrib_" + pivot_desc + ".png"),
            normalised=False
            )
        for i in range(len(pivot_trains)):
            train_i, desc_i = pivot_trains[i]
            print("    Saving statistics of spike train: " + desc_i)
            with open(os.path.join(outdir, "stats_" + desc_i + ".json"), "w") as ofile:
                ofile.write(json.dumps({"configuration": train_i.get_configuration(),
                                        "statistics": train_i.get_statistics()},
                                       sort_keys=True,
                                       indent=4))
            print("    Saving spike event distributions of spike train: " + desc_i)
            plot.histogram(
                datalgo.make_histogram(
                    datalgo.make_difference_events(train_i.get_spikes_history()),
                    dt,
                    start_time
                    ),
                os.path.join(outdir, "distrib_" + desc_i + ".png"),
                normalised=False
                )

            print("    Saving alignment histogram: " + desc_i + " VS " + pivot_desc)
            hist_pair = datalgo.make_alignment_histograms_of_spike_histories(
                                train_i.get_spikes_history(),
                                pivot.get_spikes_history(),
                                0.005,
                                dt / 2.0
                                )
            plot.histogram(
                hist_pair[0],
                os.path.join(outdir, "hist_" + desc_i + "_vs_" + pivot_desc + ".png"),
                normalised=False
                )

            for j in range(i + 1, len(pivot_trains)):
                train_j, desc_j = pivot_trains[j]

                print("    Saving alignment histogram: " + desc_i + " VS " + desc_j)
                hist_pair = datalgo.make_alignment_histograms_of_spike_histories(
                                    train_i.get_spikes_history(),
                                    train_j.get_spikes_history(),
                                    0.005,
                                    dt / 2.0
                                    )
                # plot.histogram(
                #     hist_pair[0],
                #     os.path.join(outdir, "hist_" + desc_i + "_vs_" + desc_j + ".png"),
                #     normalised=False
                #     )
                # plot.histogram(
                #     hist_pair[1],
                #     os.path.join(outdir, "hist_" + desc_j + "_vs_" + desc_i + ".png")
                #     )

                print("    Saving alignment curve: " + desc_i + " VS " + desc_j)
                with plot.Plot(os.path.join(outdir, "curve_" + desc_i + "_vs_" + desc_j + ".png")) as plt:
                    plt.curve(
                        datalgo.interpolate_discrete_function(
                            datalgo.approximate_discrete_function(
                                distribution.Distribution(hist_pair[0]).get_probability_points()
                                )
                            ),
                        legend=desc_i + " -> " + desc_j
                        )
                    plt.curve(
                        datalgo.interpolate_discrete_function(
                            datalgo.approximate_discrete_function(
                                distribution.Distribution(hist_pair[1]).get_probability_points()
                                )
                            ),
                        legend=desc_j + " -> " + desc_i
                        )
        plot.event_board_per_partes(
            [pivot.get_spikes_history()] + [train.get_spikes_history() for train, _ in pivot_trains],
            os.path.join(outdir, "spikes_board.png"),
            start_time,
            start_time + nsteps * dt,
            1.0,
            5,
            lambda p: print("    Saving spikes board part: " + os.path.basename(p)),
            [[plot.get_random_rgb_colour()] * len(pivot.get_spikes_history())] +
                [[plot.get_random_rgb_colour()] * len(train.get_spikes_history())
                 for train, _ in pivot_trains],
            " " + plot.get_title_placeholder() + " SPIKES BOARD"
            )

    return 0    # No failures


####################################################################################################
####################################################################################################
####################################################################################################


_automatically_registered_tests_ = sorted([{"name": elem.__name__[len("_test_"):],
                                            "function_ptr": elem,
                                            "description": str(elem.__doc__)}
                                           for elem in list(map(eval, dir()))
                                           if callable(elem) and elem.__name__.startswith("_test_")],
                                          key=lambda x: x["name"])


def get_registered_tests():
    return _automatically_registered_tests_


def run_test(test_info):
    assert isinstance(test_info, dict)
    assert "function_ptr" in test_info and callable(test_info["function_ptr"])
    assert "name" in test_info
    print("Starting test '" + test_info["name"] + "':")
    out_dir = os.path.join(os.path.join(test_info["output_dir"], "tests", test_info["name"]))
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    start_time = time.time()
    retval = test_info["function_ptr"](TestInfo(test_info["name"], out_dir))
    end_time = time.time()
    print("The test has finished " + ("successfully" if retval == 0 else "with an error") +
          " in " + utility.duration_string(start_time, end_time) + " seconds.")
    return retval
