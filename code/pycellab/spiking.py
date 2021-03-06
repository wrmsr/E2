import os
import shutil
import argparse
import math
import time
import json
import config
from plot import get_colour_pre_inhibitory
import tests
import neuron
import synapse
import spike_train
import datalgo
import plot
import utility
import distribution


def get_colour_pre_excitatory():
    return 'C0'     # blue


def get_colour_pre_inhibitory():
    return 'C2'     # green


def get_colour_pre_excitatory_and_inhibitory():
    return 'C4'     # purple


def get_colour_post():
    return 'k'      # black


def get_colour_soma():
    return 'k'      # black


def get_colour_synapse():
    return 'k'      # black


def save_pre_isi_distributions(cfg):
    assert isinstance(cfg, config.NeuronWithInputSynapses)
    if cfg.are_equal_noise_distributions:
        pathname = os.path.join(cfg.output_dir, "pre_isi_all" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.histogram(
            cfg.excitatory_noise_distributions[0],
            pathname,
            colours=get_colour_pre_excitatory_and_inhibitory()
            )
    else:
        if cfg.are_equal_excitatory_noise_distributions:
            pathname = os.path.join(cfg.output_dir, "pre_isi_excitatory" + cfg.plot_files_extension)
            print("    Saving plot " + pathname)
            plot.histogram(
                cfg.excitatory_noise_distributions[0],
                pathname,
                colours=get_colour_pre_excitatory()
                )
        if cfg.are_equal_inhibitory_noise_distributions:
            pathname = os.path.join(cfg.output_dir, "pre_isi_inhibitory" + cfg.plot_files_extension)
            print("    Saving plot " + pathname)
            plot.histogram(
                cfg.inhibitory_noise_distributions[0],
                pathname,
                colours=get_colour_pre_inhibitory()
                )


def save_post_isi_distribution(cfg, post_spikes, subdir):
    assert isinstance(cfg, config.CommonProps)
    pathname = os.path.join(cfg.output_dir, subdir, "post_isi" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.make_histogram(
            datalgo.make_difference_events(post_spikes),
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        normalised=False,
        colours=get_colour_post()
        )


def save_spikes_board(
        cfg,
        pre_spikes_excitatory,
        pre_spikes_inhibitory,
        pre_weights_excitatory,
        pre_weights_inhibitory,
        post_spikes,
        soma_name,
        sub_dir,
        suffix,
        title=None
        ):
    assert isinstance(cfg, config.CommonProps)
    pathname = os.path.join(cfg.output_dir, sub_dir, "spikes_board" + suffix + cfg.plot_files_extension)
    print("    Saving plot " + pathname)

    if len(pre_spikes_excitatory) == 1 and len(pre_spikes_inhibitory) == 0 and len(post_spikes) == 1:
        stride = 0
        base_shift = -1
        if title is None:
            title = (
                "pre[0]=" + str(len(pre_spikes_excitatory[0])) +
                ", post[" + str(base_shift + stride) + "]=" + str(len(post_spikes[0]))
                )
        colours = ([get_colour_pre_excitatory() for _ in range(len(pre_spikes_excitatory[0]))] +
                   [get_colour_post() for _ in range(len(post_spikes[0]))])
    else:
        stride = -max(int((len(pre_spikes_excitatory) + len(pre_spikes_inhibitory))/100), 5)
        base_shift = -max(int((len(pre_spikes_excitatory) + len(pre_spikes_inhibitory))/10 + stride / 2), 5)
        if title is None:
            title = (
                "pre-total=" +
                        str(len(pre_spikes_excitatory) + len(pre_spikes_inhibitory)) +
                ", pre-excitatory[0," +
                        str(len(pre_spikes_excitatory)) + ")=" +
                        str(len(pre_spikes_excitatory)) +
                ", pre-inhibitory[" +
                        str(len(pre_spikes_excitatory)) + "," +
                        str(len(pre_spikes_excitatory) + len(pre_spikes_inhibitory)) + ")=" +
                        str(len(pre_spikes_inhibitory)) +
                ", post[" + str(base_shift + stride) + "]=" + soma_name
                )
        colours = ([(weight, 0.1, 1.0 - weight) for weights in pre_weights_excitatory for weight in weights] +
                   [(0.0, weight, 1.0 - weight) for weights in pre_weights_inhibitory for weight in weights] +
                   [(0.0, 0.0, 0.0) for spikes in post_spikes for _ in spikes])

    plot.scatter(
        points=[(pre_spikes_excitatory[i][j], i)
                for i in range(len(pre_spikes_excitatory))
                for j in range(len(pre_spikes_excitatory[i]))] +
               [(pre_spikes_inhibitory[i][j], i + len(pre_spikes_excitatory))
                for i in range(len(pre_spikes_inhibitory))
                for j in range(len(pre_spikes_inhibitory[i]))] +
               [(post_spikes[i][j], stride * i + base_shift)
                for i in range(len(post_spikes))
                for j in range(len(post_spikes[i]))],
        pathname=pathname,
        colours=colours,
        title=title
        )


def save_spikes_board_per_partes(
        cfg,
        pre_spikes_excitatory,
        pre_spikes_inhibitory,
        pre_weights_excitatory,
        pre_weights_inhibitory,
        post_spikes,
        soma_name,
        sub_dir,
        title=None
        ):
    assert isinstance(cfg, config.CommonProps)
    assert len(pre_spikes_excitatory) == len(pre_weights_excitatory)
    assert len(pre_spikes_inhibitory) == len(pre_weights_inhibitory)
    indices_excitatory = [0 for _ in pre_spikes_excitatory]
    indices_inhibitory = [0 for _ in pre_spikes_inhibitory]
    start_time = cfg.start_time
    end_time = cfg.start_time + cfg.nsteps * cfg.dt
    dt = cfg.plot_time_step
    indices_post = [0]
    idx = 0
    t = start_time
    while t < end_time:
        end = min(t + dt, end_time)

        def make_slice(spikes, weights, t_start, t_end, indices):
            assert weights is None or len(spikes) == len(weights)
            assert len(spikes) == len(indices)
            assert t_start <= t_end
            spikes_slice = []
            weights_slice = []
            for i, j in enumerate(indices):
                res_spikes = []
                res_weights = []
                while j < len(spikes[i]) and spikes[i][j] < t_end:
                    if spikes[i][j] >= t_start:
                        res_spikes.append(spikes[i][j])
                        if weights is not None:
                            res_weights.append(weights[i][j])
                    j += 1
                spikes_slice.append(res_spikes)
                if weights is not None:
                    weights_slice.append(res_weights)
                indices[i] = j
            if weights is not None:
                return spikes_slice, weights_slice
            else:
                return spikes_slice

        slice_spikes_excitatory, slice_weights_excitatory =\
            make_slice(pre_spikes_excitatory, pre_weights_excitatory, t, end, indices_excitatory)
        slice_spikes_inhibitory, slice_weights_inhibitory =\
            make_slice(pre_spikes_inhibitory, pre_weights_inhibitory, t, end, indices_inhibitory)

        save_spikes_board(
            cfg,
            slice_spikes_excitatory,
            slice_spikes_inhibitory,
            slice_weights_excitatory,
            slice_weights_inhibitory,
            make_slice([post_spikes], None, t, end, indices_post),
            soma_name,
            sub_dir,
            "_" + str(idx).zfill(4) + "_" + format(t, ".4f"),
            title
            )

        t += dt
        idx += 1


def save_pre_spike_counts_histograms(cfg, pre_spikes_excitatory, pre_spikes_inhibitory):
    assert isinstance(cfg, config.CommonProps)
    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_histogram" + cfg.plot_files_extension)
    print("    !!!!!!!!!!!!!!! TODO !!!!!!!!!!! Saving plot " + pathname)
    # plot.histogram(
    #     datalgo.make_histogram(
    #         [c for t, c in
    #             datalgo.make_histogram(
    #                 sorted([t for spikes in pre_spikes_excitatory + pre_spikes_inhibitory for t in spikes]),
    #                 bin_size=cfg.dt
    #                 ).items()]
    #         ),
    #     pathname,
    #     normalised=False,
    #     colours=get_colour_pre_excitatory_and_inhibitory()
    #     )

    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_histogram_excitatory" + cfg.plot_files_extension)
    print("    !!!!!!!!!!!!!!! TODO !!!!!!!!!!! Saving plot " + pathname)
    # plot.histogram(
    #     distribution.make_counts_histogram(
    #         [c for t, c in
    #             distribution.make_counts_histogram(
    #                 sorted([t for spikes in pre_spikes_excitatory for t in spikes]),
    #                 bin_size=cfg.dt
    #                 ).items()]),
    #     pathname,
    #     normalised=False,
    #     colours=get_colour_pre_excitatory()
    #     )

    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_histogram_inhibitory" + cfg.plot_files_extension)
    print("    !!!!!!!!!!!!!!! TODO !!!!!!!!!!! Saving plot " + pathname)
    # plot.histogram(
    #     distribution.make_counts_histogram(
    #         [c for t, c in
    #             distribution.make_counts_histogram(
    #                 sorted([t for spikes in pre_spikes_inhibitory for t in spikes]),
    #                 bin_size=cfg.dt
    #                 ).items()]),
    #     pathname,
    #     normalised=False,
    #     colours=get_colour_pre_inhibitory()
    #     )


def save_pre_spike_counts_curves(cfg, pre_spikes_excitatory, pre_spikes_inhibitory, suffix):
    assert isinstance(cfg, config.CommonProps)
    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_curve" + suffix + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.curve(
        datalgo.reduce_gaps_between_points_along_x_axis(
            datalgo.make_weighted_events(
                sorted([t for spikes in pre_spikes_excitatory + pre_spikes_inhibitory for t in spikes]),
                cfg.dt),
            cfg.dt
            ),
        pathname,
        colours=get_colour_pre_excitatory_and_inhibitory()
        )

    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_curve_excitatory" + suffix + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.curve(
        datalgo.reduce_gaps_between_points_along_x_axis(
            datalgo.make_weighted_events(
                sorted([t for spikes in pre_spikes_excitatory for t in spikes]),
                cfg.dt),
            cfg.dt
            ),
        pathname,
        colours=get_colour_pre_excitatory()
        )

    pathname = os.path.join(cfg.output_dir, "pre_spike_counts_curve_inhibitory" + suffix + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.curve(
        datalgo.reduce_gaps_between_points_along_x_axis(
            datalgo.make_weighted_events(
                sorted([t for spikes in pre_spikes_inhibitory for t in spikes]),
                cfg.dt),
            cfg.dt
            ),
        pathname,
        colours=get_colour_pre_inhibitory()
        )


def save_pre_spike_counts_curves_per_partes(
        cfg,
        pre_spikes_excitatory,
        pre_spikes_inhibitory,
        start_time,
        end_time,
        dt
        ):
    assert isinstance(cfg, config.CommonProps)
    assert start_time <= end_time and dt > 0.0
    idx = 0
    t = start_time
    while t < end_time:
        end = min(t + dt, end_time)

        def time_filer(event):
            return t <= event and event < end

        save_pre_spike_counts_curves(
            cfg,
            [list(filter(time_filer, spikes)) for spikes in pre_spikes_excitatory],
            [list(filter(time_filer, spikes)) for spikes in pre_spikes_inhibitory],
            "_" + str(idx).zfill(4) + "_" + format(t, ".4f")
            )

        t += dt
        idx += 1


def save_soma_recording(cfg, data, title, subdir, suffix):
    assert isinstance(cfg, config.CommonProps)
    for key, points in data.items():
        pathname = os.path.join(cfg.output_dir, subdir, "soma_" + key + suffix + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.curve(points, pathname, colours=get_colour_soma(), title=title)


def save_soma_recording_per_partes(
        cfg,
        data,
        title,
        subdir,
        start_time,
        end_time,
        dt
        ):
    assert isinstance(cfg, config.CommonProps)
    assert start_time <= end_time and dt > 0.0
    idx = 0
    t = start_time
    while t < end_time:
        end = min(t + dt, end_time)

        def time_filer(event):
            return t <= event and event < end

        save_soma_recording(
            cfg,
            dict([(key, list(filter(lambda p: time_filer(p[0]), points))) for key, points in data.items()]),
            title,
            subdir,
            "_" + str(idx).zfill(4) + "_" + format(t, ".4f")
            )

        t += dt
        idx += 1


def save_weights_recording_per_partes(
        cfg,
        weights_excitatory,
        weights_inhibitory,
        sub_dir
        ):
    assert isinstance(cfg, config.CommonProps)
    indices_excitatory = [0 for _ in weights_excitatory]
    indices_inhibitory = [0 for _ in weights_inhibitory]
    idx = 0
    end_time = cfg.start_time + cfg.nsteps * cfg.dt
    t = cfg.start_time
    while t < end_time:
        end = min(t + cfg.plot_time_step, end_time)

        def make_slice(weights, t_start, t_end, indices):
            assert len(weights) == len(indices)
            assert t_start <= t_end
            weights_slice = []
            for i, j in enumerate(indices):
                res_weights = []
                while j < len(weights[i]) and weights[i][j][0] < t_end:
                    if weights[i][j][0] >= t_start:
                        res_weights.append(weights[i][j])
                    j += 1
                weights_slice.append(res_weights)
                indices[i] = j
            return weights_slice

        def merge_lists_of_points(lists, merge_function, finalise_function=lambda x: x):
            assert all([isinstance(alist, list) for alist in lists])
            assert callable(merge_function)
            merge_result = []
            if len(lists) == 0:
                return []
            for i in range(max([len(x) for x in lists])):
                value = None
                for alist in lists:
                    if i < len(alist):
                        if value:
                            assert abs(value[0] - alist[i][0]) < 0.00001
                            value = (value[0], merge_function(value[1], alist[i][1]))
                        else:
                            value = alist[i]
                assert value is not None
                merge_result.append((value[0], finalise_function(value[1])))
            return merge_result

        plot_data = {}

        sliced_weights_excitatory = make_slice(weights_excitatory, t, end, indices_excitatory)
        plot_data["weights_excitatory_min"] = merge_lists_of_points(sliced_weights_excitatory, min)
        plot_data["weights_excitatory_max"] = merge_lists_of_points(sliced_weights_excitatory, max)
        plot_data["weights_excitatory_average"] = merge_lists_of_points(sliced_weights_excitatory, lambda x, y: x + y,
                                                                        lambda x: x / len(weights_excitatory))
        sliced_weights_inhibitory = make_slice(weights_inhibitory, t, end, indices_inhibitory)
        plot_data["weights_inhibitory_min"] = merge_lists_of_points(sliced_weights_inhibitory, min)
        plot_data["weights_inhibitory_max"] = merge_lists_of_points(sliced_weights_inhibitory, max)
        plot_data["weights_inhibitory_average"] = merge_lists_of_points(sliced_weights_inhibitory, lambda x, y: x + y,
                                                                        lambda x: x / len(weights_inhibitory))
        sliced_weights_both = sliced_weights_excitatory + sliced_weights_inhibitory
        plot_data["weights_both_min"] = merge_lists_of_points(sliced_weights_both, min)
        plot_data["weights_both_max"] = merge_lists_of_points(sliced_weights_both, max)
        plot_data["weights_both_average"] = merge_lists_of_points(sliced_weights_both, lambda x, y: x + y,
                                                                  lambda x: x / (len(weights_excitatory) +
                                                                                 len(weights_inhibitory)))
        suffix = "_" + str(idx).zfill(4) + "_" + format(t, ".4f")

        for name, points in plot_data.items():
            pathname = os.path.join(cfg.output_dir, sub_dir, name + suffix + cfg.plot_files_extension)
            print("    Saving plot " + pathname)
            plot.curve(points, pathname, colours=get_colour_pre_excitatory())

        t += cfg.plot_time_step
        idx += 1


def save_synapse_recording_per_partes(
        cfg,
        recording,
        title,
        sub_dir
        ):
    assert isinstance(cfg, config.CommonProps)
    if title is not None and len(title) == 0:
        xtitle = None
    else:
        xtitle = title
    idx = 0
    end_time = cfg.start_time + cfg.nsteps * cfg.dt
    t = cfg.start_time
    while t < end_time:
        end = min(t + cfg.plot_time_step, end_time)

        suffix = "_" + str(idx).zfill(4) + "_" + format(t, ".4f")
        for var, points in recording.items():
            pathname = os.path.join(cfg.output_dir, sub_dir, "synapse_" + title + "_" + var + "_" + suffix +
                                    cfg.plot_files_extension)
            print("    Saving plot " + pathname)
            if "excitatory" in title:
                colour = get_colour_pre_excitatory()
            elif "inhibitory" in title:
                colour = get_colour_pre_inhibitory()
            else:
                colour = get_colour_pre_excitatory_and_inhibitory()
            plot.curve(list(filter(lambda p: t <= p[0] and p[0] < end, points)), pathname, colours=colour, title=xtitle)

        t += cfg.plot_time_step
        idx += 1


def evaluate_neuron_with_input_synapses(cfg, force_recompute):
    assert isinstance(cfg, config.NeuronWithInputSynapses)

    if force_recompute is False and os.path.isdir(cfg.output_dir):
        print("Results of the configuration '" + cfg.name + "' already exit. skipping the computation.")
        return

    print("Evaluating the configuration '" + cfg.name + "'.")

    tmprof_begin_cells_construction = time.time()

    cells = [neuron.Neuron(
                cfg.cell_soma[i],
                cfg.excitatory_synapses[i],
                cfg.inhibitory_synapses[i],
                cfg.num_sub_iterations[i],
                cfg.start_time,
                cfg.recording_config
                )
             for i in range(len(cfg.cell_soma))]

    print("  Starting simulation.")

    tmprof_begin_simulation = time.time()

    t = cfg.start_time
    for step in range(cfg.nsteps):
        print("    " + format(100.0 * step / float(cfg.nsteps), '.1f') + "%", end='\r')

        # time step of cells
        for cell in cells:
            cell.integrate(t, cfg.dt)

        # time step of excitatory spike trains
        for i in range(len(cfg.excitatory_spike_trains)):
            was_spike_generated = cfg.excitatory_spike_trains[i].on_time_step(t, cfg.dt)
            if was_spike_generated:
                for cell in cells:
                    cell.on_excitatory_spike(i)

        # time step of inhibitory spike trains
        for i in range(len(cfg.inhibitory_spike_trains)):
            was_spike_generated = cfg.inhibitory_spike_trains[i].on_time_step(t, cfg.dt)
            if was_spike_generated:
                for cell in cells:
                    cell.on_inhibitory_spike(i)

        t += cfg.dt

    print("  Saving results.")

    tmprof_begin_save = time.time()

    if os.path.exists(cfg.output_dir):
        shutil.rmtree(cfg.output_dir)
    os.makedirs(cfg.output_dir)

    pathname = os.path.join(cfg.output_dir, "spike_trains__isi_pre_excitatory[ALL]" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.merge_histograms(
            [datalgo.make_histogram(
                datalgo.make_difference_events(
                    cfg.excitatory_spike_trains[idx].get_spikes_history()
                    ),
                cfg.dt,
                cfg.start_time
                )
             for idx in range(len(cfg.excitatory_spike_trains))],
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        colours=get_colour_pre_excitatory(),
        normalised=False
        )

    pathname = os.path.join(cfg.output_dir, "spike_trains__isi_pre_inhibitory[ALL]" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.merge_histograms(
            [datalgo.make_histogram(
                datalgo.make_difference_events(
                    cfg.inhibitory_spike_trains[idx].get_spikes_history()
                    ),
                cfg.dt,
                cfg.start_time
                )
             for idx in range(len(cfg.inhibitory_spike_trains))],
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        colours=get_colour_pre_inhibitory(),
        normalised=False
        )

    for idx in cfg.excitatory_plot_indices:
        file_name = "spike_trains__isi_pre_excitatory[" + str(idx) + "]"
        pathname = os.path.join(cfg.output_dir, file_name + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(
                    cfg.excitatory_spike_trains[idx].get_spikes_history()
                    ),
                cfg.dt,
                cfg.start_time
                ),
            pathname,
            colours=get_colour_pre_excitatory(),
            normalised=False
            )

    for idx in cfg.inhibitory_plot_indices:
        file_name = "spike_trains__isi_pre_inhibitory[" + str(idx) + "]"
        pathname = os.path.join(cfg.output_dir, file_name + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(
                    cfg.inhibitory_spike_trains[idx].get_spikes_history()
                    ),
                cfg.dt,
                cfg.start_time
                ),
            pathname,
            colours=get_colour_pre_inhibitory(),
            normalised=False
            )

    merged_excitatory_points =datalgo.reduce_gaps_between_points_along_x_axis(
        datalgo.make_weighted_events(
            datalgo.merge_sorted_lists_of_events(
                [cfg.excitatory_spike_trains[idx].get_spikes_history()
                 for idx in range(len(cfg.excitatory_spike_trains))]
                ),
            cfg.dt
            ),
        cfg.dt
        )
    plot.curve_per_partes(
        merged_excitatory_points,
        os.path.join(cfg.output_dir, "spike_trains__counts_excitatory" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        None,
        lambda p: print("    Saving plot " + p),
        get_colour_pre_excitatory(),
        plot.get_title_placeholder()
        )

    merged_inhibitory_points = datalgo.reduce_gaps_between_points_along_x_axis(
        datalgo.make_weighted_events(
            datalgo.merge_sorted_lists_of_events(
                [cfg.inhibitory_spike_trains[idx].get_spikes_history()
                 for idx in range(len(cfg.inhibitory_spike_trains))]
                ),
            cfg.dt
            ),
        cfg.dt
        )
    plot.curve_per_partes(
        merged_inhibitory_points,
        os.path.join(cfg.output_dir, "spike_trains__counts_inhibitory" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        None,
        lambda p: print("    Saving plot " + p),
        get_colour_pre_inhibitory(),
        plot.get_title_placeholder()
        )

    composed_excitatory_inhibitory_points = datalgo.compose_sorted_lists_of_points(
        [merged_excitatory_points, merged_inhibitory_points],
        [1, -1]
        )
    plot.curve_per_partes(
        composed_excitatory_inhibitory_points,
        os.path.join(cfg.output_dir, "spike_trains__counts_composed" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        None,
        lambda p: print("    Saving plot " + p),
        get_colour_pre_excitatory_and_inhibitory(),
        plot.get_title_placeholder()
        )

    for cell, sub_dir in list(zip(cells, map(lambda cell: cell.get_soma().get_name() * int(len(cells) > 1), cells))):
        cell_output_dir = os.path.join(cfg.output_dir, sub_dir)
        os.makedirs(cell_output_dir, exist_ok=True)

        if cfg.recording_config.post_synaptic_spikes:
            file_name = "spike_trains__isi_post_" + cell.get_soma().get_name()
            pathname = os.path.join(cfg.output_dir, file_name + cfg.plot_files_extension)
            print("    Saving plot " + pathname)
            plot.histogram(
                datalgo.make_histogram(
                    datalgo.make_difference_events(
                        cell.get_spikes()
                        ),
                    cfg.dt,
                    cfg.start_time
                    ),
                pathname,
                colours=get_colour_post(),
                normalised=False
                )

        if cfg.recording_config.soma:
            for var_name, points in cell.get_soma_recording().items():
                if len(points) != 0:
                    file_name = cell.get_soma().get_name() + "__VAR[" + var_name + "]"
                    plot.curve_per_partes(
                        points,
                        os.path.join(cell_output_dir, file_name + cfg.plot_files_extension),
                        cfg.start_time,
                        cfg.start_time + cfg.nsteps * cfg.dt,
                        cfg.plot_time_step,
                        None,
                        lambda p: print("    Saving plot " + p),
                        get_colour_soma(),
                        cell.get_soma().get_short_description()
                        )

        if cfg.recording_config.excitatory_synapses:
            for idx in cfg.excitatory_plot_indices:
                for var_name, points in cell.get_excitatory_synapses_recording()[idx].items():
                    if len(points) != 0:
                        file_name = cell.get_soma().get_name() + "__synapse_excitatory[" + str(idx) + "]__VAR[" + var_name + "]"
                        plot.curve_per_partes(
                            points,
                            os.path.join(cell_output_dir, file_name + cfg.plot_files_extension),
                            cfg.start_time,
                            cfg.start_time + cfg.nsteps * cfg.dt,
                            cfg.plot_time_step,
                            None,
                            lambda p: print("    Saving plot " + p),
                            get_colour_synapse(),
                            cell.get_excitatory_synapses()[idx].get_short_description()
                            )

        if cfg.recording_config.inhibitory_synapses:
            for idx in cfg.inhibitory_plot_indices:
                for var_name, points in cell.get_inhibitory_synapses_recording()[idx].items():
                    if len(points) != 0:
                        file_name = cell.get_soma().get_name() + "__synapse_inhibitory[" + str(idx) + "]__VAR[" + var_name + "]"
                        plot.curve_per_partes(
                            points,
                            os.path.join(cell_output_dir, file_name + cfg.plot_files_extension),
                            cfg.start_time,
                            cfg.start_time + cfg.nsteps * cfg.dt,
                            cfg.plot_time_step,
                            None,
                            lambda p: print("    Saving plot " + p),
                            get_colour_synapse(),
                            cell.get_excitatory_synapses()[idx].get_short_description()
                            )

        if cfg.recording_config.excitatory_synapses or cfg.recording_config.inhibitory_synapses:
            plot.event_board_per_partes(
                [cfg.excitatory_spike_trains[idx].get_spikes_history() for idx in range(len(cfg.excitatory_spike_trains))] +
                    [cfg.inhibitory_spike_trains[idx].get_spikes_history() for idx in range(len(cfg.inhibitory_spike_trains))] +
                    [cell.get_spikes()],
                os.path.join(cell_output_dir, cell.get_soma().get_name() + "__spikes_board" + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                None,
                lambda p: print("    Saving plot " + p),
                list(map(lambda L: list(map(lambda p: plot.get_colour_pre_excitatory(p[1]), L)),
                    [datalgo.transform_discrete_function_to_inteval_0_1_using_liner_interpolation(
                        datalgo.evaluate_discrete_function_using_liner_interpolation(
                            cfg.excitatory_spike_trains[idx].get_spikes_history(),
                            cell.get_excitatory_synapses_recording()[idx][cell.get_excitatory_synapses()[idx].get_weight_variable_name()],
                            cell.get_excitatory_synapses()[idx].get_neutral_weight()
                            ),
                        cell.get_excitatory_synapses()[idx].get_min_weight(),
                        cell.get_excitatory_synapses()[idx].get_max_weight()
                        ) for idx in range(len(cfg.excitatory_spike_trains))])) +
                    list(map(lambda L: list(map(lambda p: plot.get_colour_pre_inhibitory(p[1]), L)),
                        [datalgo.transform_discrete_function_to_inteval_0_1_using_liner_interpolation(
                            datalgo.evaluate_discrete_function_using_liner_interpolation(
                                cfg.inhibitory_spike_trains[idx].get_spikes_history(),
                                cell.get_inhibitory_synapses_recording()[idx][cell.get_inhibitory_synapses()[idx].get_weight_variable_name()],
                                cell.get_inhibitory_synapses()[idx].get_neutral_weight()
                                ),
                            cell.get_inhibitory_synapses()[idx].get_min_weight(),
                            cell.get_inhibitory_synapses()[idx].get_max_weight()
                            ) for idx in range(len(cfg.inhibitory_spike_trains))])) +
                    [[plot.get_colour_post() for _ in range(len(cell.get_spikes()))]],
                " " + plot.get_title_placeholder() + " " + cell.get_soma().get_name() + " SPIKING BOARD"
                )

    tmprof_end = time.time()

    print("  Time profile of the evaluation [in seconds]:" +
          "\n    Construction of cells: " + utility.duration_string(tmprof_begin_cells_construction, tmprof_begin_simulation) +
          "\n    Simulation: " + utility.duration_string(tmprof_begin_cells_construction, tmprof_begin_save) +
          "\n    Saving results: " + utility.duration_string(tmprof_begin_save, tmprof_end) +
          "\n    TOTAL: " + utility.duration_string(tmprof_begin_cells_construction, tmprof_end))

    print("  Done.")


def evaluate_synapse_and_spike_noise(cfg, force_recompute):
    assert isinstance(cfg, config.SynapseAndSpikeNoise)

    if force_recompute is False and os.path.isdir(cfg.output_dir):
        print("Results of the configuration '" + cfg.name + "' already exit. skipping the computation.")
        return

    print("Evaluating the configuration '" + cfg.name + "'.")

    print("  Constructing and initialising data structures,")
    pre_spike_train = spike_train.create(cfg.pre_spikes_distributions, 0.0)
    post_spike_train = spike_train.create(cfg.post_spikes_distributions, 0.0)
    synapse_recording = dict([(var, [(cfg.start_time, value)])
                              for var, value in cfg.the_synapse.get_variables().items()])

    print("  Starting simulation.")
    t = cfg.start_time
    for step in range(cfg.nsteps):
        print("    " + format(100.0 * step / float(cfg.nsteps), '.1f') + "%", end='\r')
        cfg.the_synapse.integrate(cfg.dt)
        if pre_spike_train.on_time_step(t, cfg.dt):
            cfg.the_synapse.on_pre_synaptic_spike()
        if post_spike_train.on_time_step(t, cfg.dt):
            cfg.the_synapse.on_post_synaptic_spike()
        for key, value in cfg.the_synapse.get_variables().items():
            synapse_recording[key].append((t + cfg.dt, value))
        t += cfg.dt

    print("  Saving results.")

    if os.path.exists(cfg.output_dir):
        shutil.rmtree(cfg.output_dir)
    os.makedirs(cfg.output_dir, exist_ok=True)

    pathname = os.path.join(cfg.output_dir, "isi_pre" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.make_histogram(
            datalgo.make_difference_events(pre_spike_train.get_spikes_history()),
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        normalised=False,
        colours=get_colour_pre_excitatory_and_inhibitory()
        )

    pathname = os.path.join(cfg.output_dir, "isi_post" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.make_histogram(
            datalgo.make_difference_events(post_spike_train.get_spikes_history()),
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        normalised=False,
        colours=get_colour_pre_excitatory_and_inhibitory()
        )

    save_synapse_recording_per_partes(cfg, synapse_recording, "", ".")

    print("  Done.")


def evaluate_pre_post_spike_noises_differences(cfg, force_recompute):
    assert isinstance(cfg, config.PrePostSpikeNoisesDifferences)

    if force_recompute is False and os.path.isdir(cfg.output_dir):
        print("Results of the configuration '" + cfg.name + "' already exit. skipping the computation.")
        return

    print("Evaluating the configuration '" + cfg.name + "'.")

    print("  Constructing and initialising data structures,")
    pre_spike_train = spike_train.create(cfg.pre_spikes_distributions, 0.0)
    post_spike_train = spike_train.create(cfg.post_spikes_distributions, 0.0)

    print("  Starting simulation.")
    delta_post_pre = []
    if cfg.synaptic_input_cooler is not None:
        synaptic_input_vars = dict([(var, [(cfg.start_time, value)])
                                   for var, value in cfg.synaptic_input_cooler.get_variables().items()])
        assert synaptic_input_vars.keys() == {cfg.synaptic_input_cooler.get_var_pre_name(),
                                              cfg.synaptic_input_cooler.get_var_post_name()}
    else:
        synaptic_input_vars = None
    t = cfg.start_time
    for step in range(cfg.nsteps):
        print("    " + format(100.0 * step / float(cfg.nsteps), '.1f') + "%", end='\r')
        is_pre_spike = pre_spike_train.on_time_step(t, cfg.dt)
        is_post_spike = post_spike_train.on_time_step(t, cfg.dt)
        if cfg.synaptic_input_cooler is not None:
            cfg.synaptic_input_cooler.integrate(cfg.dt)
            if is_pre_spike:
                cfg.synaptic_input_cooler.on_pre_synaptic_spike()
            if is_post_spike:
                cfg.synaptic_input_cooler.on_post_synaptic_spike()
            for var, value in cfg.synaptic_input_cooler.get_variables().items():
                synaptic_input_vars[var].append((t + cfg.dt, value))
        if is_pre_spike and is_post_spike:
            delta_post_pre.append((t + cfg.dt, 0.0))
        elif is_pre_spike:
            if len(post_spike_train.get_spikes()) > 0:
                delta_post_pre.append((t + cfg.dt, post_spike_train.get_spikes()[-1] - (t + cfg.dt)))
        elif is_post_spike:
            if len(pre_spike_train.get_spikes()) > 0:
                delta_post_pre.append((t + cfg.dt, (t + cfg.dt) - pre_spike_train.get_spikes()[-1]))
        t += cfg.dt

    print("  Saving results.")

    if os.path.exists(cfg.output_dir):
        shutil.rmtree(cfg.output_dir)
    os.makedirs(cfg.output_dir, exist_ok=True)

    pathname = os.path.join(cfg.output_dir, "isi_pre_orig" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(cfg.pre_spikes_distributions, pathname)

    pathname = os.path.join(cfg.output_dir, "isi_pre" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.make_histogram(
            datalgo.make_difference_events(pre_spike_train.get_spikes()),
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        normalised=False,
        colours=get_colour_pre_excitatory_and_inhibitory()
        )

    pathname = os.path.join(cfg.output_dir, "isi_post_orig" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(cfg.post_spikes_distributions, pathname)

    pathname = os.path.join(cfg.output_dir, "isi_post" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(
        datalgo.make_histogram(
            datalgo.make_difference_events(post_spike_train.get_spikes()),
            cfg.dt,
            cfg.start_time
            ),
        pathname,
        normalised=False,
        colours=get_colour_pre_excitatory_and_inhibitory()
        )

    if cfg.synaptic_input_cooler is None:
        input_vars_sub = None
        input_vars_sign_add = None
        input_vars_sign_mul = None
    else:
        pre_points = synaptic_input_vars[cfg.synaptic_input_cooler.get_var_pre_name()]
        post_points = synaptic_input_vars[cfg.synaptic_input_cooler.get_var_post_name()]
        assert len(pre_points) == len(post_points)
        input_vars_sub = [(pre_points[i][0], post_points[i][1] - pre_points[i][1]) for i in range(len(pre_points))]
        input_vars_sign_add = [(pre_points[i][0], math.copysign(post_points[i][1] + pre_points[i][1],
                                                                post_points[i][1] - pre_points[i][1]))
                               for i in range(len(pre_points))]
        input_vars_sign_mul = [(pre_points[i][0], math.copysign(post_points[i][1] * pre_points[i][1],
                                                                post_points[i][1] - pre_points[i][1]))
                               for i in range(len(pre_points))]

    if cfg.save_per_partes_plots:
        save_spikes_board_per_partes(
            cfg,
            [pre_spike_train.get_spikes()],
            [],
            [[1.0 for _ in range(len(pre_spike_train.get_spikes()))]],
            [],
            post_spike_train.get_spikes(),
            "",
            "spikes_board"
            )
        plot.curve_per_partes(
            delta_post_pre,
            os.path.join(cfg.output_dir, "delta_post_pre", "delta_post_pre" + cfg.plot_files_extension),
            cfg.start_time,
            cfg.start_time + cfg.nsteps * cfg.dt,
            cfg.plot_time_step,
            None,
            lambda p: print("    Saving plot " + p),
            marker="x"
            )
        for var, points in synaptic_input_vars.items():
            plot.curve_per_partes(
                points,
                os.path.join(cfg.output_dir, "synaptic_" + var, "synaptic_" + var + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                None,
                lambda p: print("    Saving plot " + p),
                title="VAR=" + var + ", " + cfg.synaptic_input_cooler.get_short_description()
                )
        if cfg.synaptic_input_cooler is not None:
            plot.curve_per_partes(
                input_vars_sub,
                os.path.join(cfg.output_dir, "input_vars_sub", "input_vars_sub" + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                None,
                lambda p: print("    Saving plot " + p),
                title="[input_post-input_pre], " + cfg.synaptic_input_cooler.get_short_description()
                )
            plot.curve_per_partes(
                input_vars_sign_add,
                os.path.join(cfg.output_dir, "input_vars_sign_add", "input_vars_sign_add" + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                None,
                lambda p: print("    Saving plot " + p),
                title="[sgn(X-Y)*(Y+X),X=input_pre,Y=input_post], " + cfg.synaptic_input_cooler.get_short_description()
                )
            plot.curve_per_partes(
                input_vars_sign_mul,
                os.path.join(cfg.output_dir, "input_vars_sign_mul", "input_vars_sign_mul" + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                None,
                lambda p: print("    Saving plot " + p),
                title="[sgn(X-Y)*(Y*X),X=input_pre,Y=input_post], " + cfg.synaptic_input_cooler.get_short_description()
                )

    pathname = os.path.join(cfg.output_dir, "delta_post_pre_hist" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    delta_post_pre_values = [p[1] for p in delta_post_pre]
    delta_post_pre_min = min(delta_post_pre_values)
    delta_post_pre_max = max(delta_post_pre_values)
    plot.histogram(
        datalgo.make_histogram(
            delta_post_pre_values,
            (delta_post_pre_max - delta_post_pre_min) / 500.0,
            delta_post_pre_min
            ),
        pathname,
        normalised=False
        )

    if cfg.synaptic_input_cooler is not None:
        pathname = os.path.join(cfg.output_dir, "input_vars_sub" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        input_vars_values = [p[1] for p in input_vars_sub]
        input_vars_min = min(input_vars_values)
        input_vars_max = max(input_vars_values)
        plot.histogram(
            datalgo.make_histogram(
                input_vars_values,
                (input_vars_max - input_vars_min) / 500.0,
                input_vars_min
                ),
            pathname,
            normalised=False
            )

        pathname = os.path.join(cfg.output_dir, "input_vars_sign_add" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        input_vars_values = [p[1] for p in input_vars_sign_add]
        input_vars_min = min(input_vars_values)
        input_vars_max = max(input_vars_values)
        input_vars_counts_hist =\
            datalgo.make_histogram(
                input_vars_values,
                (input_vars_max - input_vars_min) / 500.0,
                input_vars_min
                )
        plot.histogram(input_vars_counts_hist, pathname, normalised=False)

        pathname = os.path.join(cfg.output_dir, "input_vars_sign_add_times_var" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.curve([(v, abs(v) * input_vars_counts_hist[v]) for v in sorted(input_vars_counts_hist.keys())], pathname)

        pathname = os.path.join(cfg.output_dir, "input_vars_sign_mul" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        input_vars_values = [p[1] for p in input_vars_sign_mul]
        input_vars_min = min(input_vars_values)
        input_vars_max = max(input_vars_values)
        plot.histogram(
            datalgo.make_histogram(
                input_vars_values,
                (input_vars_max - input_vars_min) / 500.0,
                input_vars_min
                ),
            pathname,
            normalised=False
            )

    print("  Done.")


def _evaluate_configuration_of_input_spike_trains(construction_data):
    assert isinstance(construction_data, config.EffectOfInputSpikeTrains.ConstructionData)

    print("  Building spike trains.")

    tmprof_begin_construction = time.time()

    cfg = construction_data.apply()
    assert isinstance(cfg, config.EffectOfInputSpikeTrains.Configuration)

    print("  Starting simulation.")

    tmprof_begin_simulation = time.time()

    voltage_curve_excitatory = []
    voltage_curve_inhibitory = []
    voltage_curve = []

    t = cfg.start_time
    for step in range(cfg.nsteps):
        utility.print_progress_string(step, cfg.nsteps)

        num_excitatory_spikes = 0
        for i in range(len(cfg.excitatory_spike_trains)):
            if cfg.excitatory_spike_trains[i].on_time_step(t, cfg.dt) is True:
                num_excitatory_spikes += 1
        if num_excitatory_spikes > 0:
            voltage_curve_excitatory.append((t + cfg.dt, num_excitatory_spikes))

        num_inhibitory_spikes = 0
        for i in range(len(cfg.inhibitory_spike_trains)):
            if cfg.inhibitory_spike_trains[i].on_time_step(t, cfg.dt) is True:
                num_inhibitory_spikes += 1
        if num_inhibitory_spikes > 0:
            voltage_curve_inhibitory.append((t + cfg.dt, num_inhibitory_spikes))

        if num_excitatory_spikes > 0 or num_inhibitory_spikes > 0:
            voltage_curve.append((t + cfg.dt, num_excitatory_spikes - num_inhibitory_spikes))

        t += cfg.dt

    print("  Saving results.")

    tmprof_begin_save = time.time()

    if os.path.exists(cfg.output_dir):
        shutil.rmtree(cfg.output_dir)
    os.makedirs(cfg.output_dir)
    plots_output_dir = os.path.join(cfg.output_dir, "plots")
    os.makedirs(plots_output_dir)

    pathname = os.path.join(cfg.output_dir, "construction_data.json")
    print("    Saving construction data for spike trains to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(construction_data.to_json(), sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "configuration.json")
    print("    Saving configuration of spike trains to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(cfg.to_json(), sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "summary_statistics.json")
    print("    Saving summary statistics to " + pathname)
    summary_stats = {}
    summary_stats_excitatory = {}
    summary_stats_inhibitory = {}
    for key in spike_train.SpikeTrain.get_keys_of_statistics():
        summary_stats_excitatory[key] = sum(train.get_statistics()[key] for train in cfg.excitatory_spike_trains)
        summary_stats_inhibitory[key] = sum(train.get_statistics()[key] for train in cfg.inhibitory_spike_trains)
        summary_stats[key] = summary_stats_excitatory[key] + summary_stats_inhibitory[key]
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps({
            "summary": summary_stats,
            "excitatory": summary_stats_excitatory,
            "inhibitory": summary_stats_inhibitory
            }, sort_keys=True, indent=4))

    isi_histogram = []
    for kind, trains, colour in [("excitatory", cfg.excitatory_spike_trains, get_colour_pre_excitatory()),
                                 ("inhibitory", cfg.inhibitory_spike_trains, get_colour_pre_inhibitory())]:
        print("    Building ISI histogram of " + kind + " spike strains.")
        isi_histogram_of_kind = datalgo.merge_histograms(
            [datalgo.make_histogram(datalgo.make_difference_events(train.get_spikes_history()), cfg.dt, cfg.start_time)
             for train in trains],
            cfg.dt,
            cfg.start_time
            )
        pathname = os.path.join(cfg.output_dir, "isi_histogram_" + kind + ".json")
        print("    Saving ISI histogram of " + kind + " spike strains in JSON format to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(isi_histogram_of_kind, sort_keys=True, indent=4))
        pathname = os.path.join(plots_output_dir, "isi_histogram_" + kind + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.histogram(isi_histogram_of_kind, pathname, colours=colour, normalised=False)
        isi_histogram.append(isi_histogram_of_kind)
    isi_histogram = datalgo.merge_histograms(isi_histogram, cfg.dt, cfg.start_time)
    pathname = os.path.join(cfg.output_dir, "isi_histogram.json")
    print("    Saving ISI histogram of spike strains in JSON format to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(isi_histogram, sort_keys=True, indent=4))
    pathname = os.path.join(plots_output_dir, "isi_histogram" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(isi_histogram, pathname, colours=get_colour_pre_excitatory_and_inhibitory(), normalised=False)

    for kind, curve, colour in [("excitatory", voltage_curve_excitatory, get_colour_pre_excitatory()),
                                ("inhibitory", voltage_curve_inhibitory, get_colour_pre_inhibitory())]:
        pathname = os.path.join(cfg.output_dir, "voltage_effect_curve_" + kind + ".json")
        print("    Saving voltage effect curve of " + kind + " spike trains in JSON format to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(curve, sort_keys=True, indent=4))
        plot.curve_per_partes(
            datalgo.reduce_gaps_between_points_along_x_axis(curve, cfg.dt),
            os.path.join(plots_output_dir, "voltage_effect_curve_" + kind + cfg.plot_files_extension),
            cfg.start_time,
            cfg.start_time + cfg.nsteps * cfg.dt,
            cfg.plot_time_step,
            cfg.num_plots_parts,
            lambda p: print("    Saving plot " + p),
            colour,
            plot.get_title_placeholder()
            )
        pathname = os.path.join(cfg.output_dir, "voltage_effect_histogram_" + kind + ".json")
        print("    Saving voltage effect histogram of " + kind + " spike trains in JSON format to " + pathname)
        voltage_histogram = datalgo.make_histogram([p[1] for p in curve], 1.0, 0.0)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(voltage_histogram, sort_keys=True, indent=4))
        plot.histogram(
            voltage_histogram,
            os.path.join(plots_output_dir, "voltage_effect_histogram_" + kind + cfg.plot_files_extension),
            colours=colour,
            normalised=False
            )
    pathname = os.path.join(cfg.output_dir, "voltage_effect_curve" + ".json")
    print("    Saving voltage effect curve of all spike trains in JSON format to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(voltage_curve, sort_keys=True, indent=4))
    plot.curve_per_partes(
        datalgo.reduce_gaps_between_points_along_x_axis(voltage_curve, cfg.dt),
        os.path.join(plots_output_dir, "voltage_effect_curve" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        cfg.num_plots_parts,
        lambda p: print("    Saving plot " + p),
        get_colour_pre_excitatory_and_inhibitory(),
        plot.get_title_placeholder()
        )
    pathname = os.path.join(cfg.output_dir, "voltage_effect_histogram" + ".json")
    print("    Saving voltage effect histogram of all spike trains in JSON format to " + pathname)
    voltage_histogram = datalgo.make_histogram([p[1] for p in voltage_curve], 1.0, 0.0)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(voltage_histogram, sort_keys=True, indent=4))
    plot.histogram(
        voltage_histogram,
        os.path.join(plots_output_dir, "voltage_effect_histogram" + cfg.plot_files_extension),
        colours=get_colour_pre_excitatory_and_inhibitory(),
        normalised=False
        )

    for kind, idx, train, colour in [("excitatory", idx, cfg.excitatory_spike_trains[idx], get_colour_pre_excitatory())
                                     for idx in cfg.excitatory_plot_indices] +\
                                    [("inhibitory", idx, cfg.inhibitory_spike_trains[idx], get_colour_pre_inhibitory())
                                     for idx in cfg.inhibitory_plot_indices]:
        pathname = os.path.join(cfg.output_dir, "spike_train_" + kind + "_index_" + str(idx) + ".json")
        print("    Saving " + kind + "spike train #" + str(idx) + " to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(train.to_json(), sort_keys=True, indent=4))
        difference_events = datalgo.make_difference_events(train.get_spikes_history())
        isi_histogram = datalgo.make_histogram(difference_events, cfg.dt, cfg.start_time)
        pathname = os.path.join(
            plots_output_dir,
            "isi_histogram_of_" + kind + "_spike_train_no_" + str(idx) + cfg.plot_files_extension
            )
        print("    Saving plot " + pathname)
        plot.histogram(isi_histogram, pathname, colours=colour, normalised=False)
        isi_delta = datalgo.make_function_from_events(datalgo.make_difference_events(difference_events))
        plot.curve_per_partes(
            isi_delta,
            os.path.join(plots_output_dir, "isi_delta_curve_of_" + kind + "_spike_train_no_" + str(idx) + cfg.plot_files_extension),
            0,
            len(isi_delta),
            1000,
            3,
            lambda p: print("    Saving plot " + p),
            colour,
            plot.get_title_placeholder()
            )

    num_all_spike_trains = len(cfg.excitatory_spike_trains) + len(cfg.inhibitory_spike_trains)
    assert num_all_spike_trains > 0
    if num_all_spike_trains <= 1000:
        num_board_excitatory_trains = len(cfg.excitatory_spike_trains)
        num_board_inhibitory_trains = len(cfg.inhibitory_spike_trains)
    else:
        num_board_excitatory_trains = int(0.5 + 1000 * len(cfg.excitatory_spike_trains) / num_all_spike_trains)
        num_board_inhibitory_trains = 1000 - num_board_excitatory_trains
    plot.event_board_per_partes(
        [cfg.excitatory_spike_trains[idx].get_spikes_history() for idx in range(num_board_excitatory_trains)] +
            [cfg.inhibitory_spike_trains[idx].get_spikes_history() for idx in range(num_board_inhibitory_trains)],
        os.path.join(plots_output_dir, "spikes_board" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        cfg.num_plots_parts,
        lambda p: print("    Saving plot " + p),
        [[(0.0, 0.0, 1.0) for _ in range(len(cfg.excitatory_spike_trains[idx].get_spikes_history()))]
         for idx in range(num_board_excitatory_trains)] +
        [[(0.0, 1.0, 0.0) for _ in range(len(cfg.inhibitory_spike_trains[idx].get_spikes_history()))]
         for idx in range(num_board_inhibitory_trains)],
        " " + plot.get_title_placeholder() + " SPIKES BOARD"
        )

    tmprof_end = time.time()

    time_profile = {
        "construction": tmprof_begin_simulation - tmprof_begin_construction,
        "simulation": tmprof_begin_save - tmprof_begin_simulation,
        "save": tmprof_end - tmprof_begin_save,
        "TOTAL": tmprof_end - tmprof_begin_construction
    }
    pathname = os.path.join(cfg.output_dir, "time_profile.json")
    print("    Saving time profile to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(time_profile, sort_keys=True, indent=4))

    print("  Time profile of the evaluation [in seconds]:" +
          "\n    Construction: " + utility.duration_string(tmprof_begin_construction, tmprof_begin_simulation) +
          "\n    Simulation: " + utility.duration_string(tmprof_begin_simulation, tmprof_begin_save) +
          "\n    Saving results: " + utility.duration_string(tmprof_begin_save, tmprof_end) +
          "\n    TOTAL: " + utility.duration_string(tmprof_begin_construction, tmprof_end))

    print("  Done.")


def _compute_interconfig_for_effect_of_input_spike_trains(cfg):
    assert isinstance(cfg, config.EffectOfInputSpikeTrains)
    print("Building the inter-configuration summary data to '" + cfg.get_interconfig_output_dir() + "'.")
    tmprof_begin = time.time()

    plots_dir = os.path.join(cfg.get_interconfig_output_dir(), "plots")
    if not os.path.isdir(plots_dir):
        os.makedirs(plots_dir)
    for kind, colour in [("_excitatory", get_colour_pre_excitatory()),
                         ("_inhibitory", get_colour_pre_inhibitory()),
                         ("", get_colour_pre_excitatory_and_inhibitory())]:
        points = []
        surface_points = {}
        for cfg_dir in cfg.get_output_dirs_of_configurations():
            pathname = os.path.join(cfg_dir, "configuration.json")
            print("    Loading configuration " + pathname)
            with open(pathname, "r") as ifile:
                configuration = json.load(ifile)
            num_excitatory_trains = configuration["excitatory_spike_trains"]
            num_inhibitory_trains = configuration["inhibitory_spike_trains"]
            pathname = os.path.join(cfg_dir, "voltage_effect_histogram" + kind + ".json")
            print("    Loading voltage effect histogram " + pathname)
            with open(pathname, "r") as ifile:
                voltage_distribution = distribution.Distribution({float(k): v for k, v in json.load(ifile).items()})
            points.append(
                {
                    "x": num_excitatory_trains,
                    "y": num_inhibitory_trains,
                    "z": voltage_distribution.get_mean(),
                    "error": {
                        "lo": distribution.compute_mean_range_lower_bound(voltage_distribution, 1.0),
                        "hi": distribution.compute_mean_range_upper_bound(voltage_distribution, 1.0)
                    }
                })
            excitatory_trains_percentage = int(0.5 + 100.0 * num_excitatory_trains / (num_excitatory_trains + num_inhibitory_trains))
            if excitatory_trains_percentage not in surface_points:
                surface_points[excitatory_trains_percentage] = {"lo": [], "hi": [], "mean": []}
            surface_points[excitatory_trains_percentage]["lo"].append((num_excitatory_trains, points[-1]["error"]["lo"]))
            surface_points[excitatory_trains_percentage]["hi"].append((num_excitatory_trains, points[-1]["error"]["hi"]))
            surface_points[excitatory_trains_percentage]["mean"].append((num_excitatory_trains, points[-1]["z"]))
        pathname = os.path.join(cfg.get_interconfig_output_dir(), "voltage_surface" + kind + ".json")
        print("    Saving voltage surface to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(
                {
                    "num_dimensions": 3,
                    "description": {
                        "brief": "Voltage-effect of pre-synaptic spikes on a cell for different in-degrees.",
                        "x": "num excitatory trains",
                        "y": "num inhibitory trains",
                        "z": "mean voltage on cell"
                    },
                    "points": points
                }, sort_keys=True, indent=4)
            )
        for percentage in surface_points.keys():
            with plot.Plot(
                    os.path.join(plots_dir, "voltage_surface_" + str(percentage) + "e" + cfg.get_plot_files_extension()),
                    title="Input voltage level on a neuron when " + str(percentage) + "% of trains are excitatory",
                    xaxis_name="number of excitatory input trains",
                    faxis_name="input voltage level"
                    ) as plt:
                for s_kind in [("lo", "lower bound"), ("hi", "upper bound"), ("mean", "average")]:
                    plt.curve(sorted(surface_points[percentage][s_kind[0]], key=lambda x: x[0]), legend=s_kind[1])
            with plot.Plot(
                    os.path.join(plots_dir, "voltage_surface_" + str(percentage) + "e_diff" + cfg.get_plot_files_extension()),
                    title="Input voltage difference from mean on a neuron when " + str(percentage) + "% of trains are excitatory",
                    xaxis_name="number of excitatory input trains",
                    faxis_name="input voltage level"
                    ) as plt:
                mean_points = surface_points[percentage]["mean"]
                for s_kind in [("lo", "lower bound"), ("hi", "upper bound")]:
                    s_points = surface_points[percentage][s_kind[0]]
                    assert len(s_points) == len(mean_points)
                    diff_points = [(s_points[i][0], s_points[i][1] - mean_points[i][1])
                                   for i in range(len(surface_points[percentage]["mean"]))]
                    plt.curve(sorted(diff_points, key=lambda x: x[0]), legend=s_kind[1])
            with plot.Plot(
                    os.path.join(plots_dir, "voltage_99percent_bounds_" + cfg.get_plot_files_extension()),
                    title="Input voltage 99% bounds from mean voltage",
                    xaxis_name="number of excitatory input trains",
                    faxis_name="voltage 99% bound"
                    ) as plt:
                num_points = 500
                dx = max(surface_points[percentage]["mean"], key=lambda x: x[0])[0] / num_points
                hi_points = [(i * dx, neuron.get_99percent_diversion_from_average_excitation_level(i * dx))
                             for i in range(num_points + 1)]
                lo_points = [(p[0], -p[1]) for p in hi_points]
                plt.curve(lo_points, legend="99% lower bound")
                plt.curve(hi_points, legend="99% upper bound")

    tmprof_end = time.time()
    print("  Done in " + utility.duration_string(tmprof_begin, tmprof_end) + " seconds.")


def evaluate_effect_of_input_spike_trains(cfg, force_recompute):
    assert isinstance(cfg, config.EffectOfInputSpikeTrains)
    start_time = time.time()
    for construction_data in cfg.get_list_of_construction_data():
        assert isinstance(construction_data, config.EffectOfInputSpikeTrains.ConstructionData)
        if force_recompute is False and os.path.isdir(construction_data.get_output_root_dir()):
            print("The configuration '" + construction_data.get_name() + "' already exists. Skipping its computation.")
        else:
            print("Building the configuration '" + construction_data.get_name() + "'.")
            _evaluate_configuration_of_input_spike_trains(construction_data)
    if force_recompute or not os.path.exists(cfg.get_interconfig_output_dir()):
        if os.path.exists(cfg.get_interconfig_output_dir()):
            shutil.rmtree(cfg.get_interconfig_output_dir())
        os.makedirs(cfg.get_interconfig_output_dir())
        _compute_interconfig_for_effect_of_input_spike_trains(cfg)
    else:
        print("The inter-configuration summary data '" + cfg.get_interconfig_output_dir() + "' already exist. "
              "Skipping their computation.")
    end_time = time.time()
    print("The whole evaluation finished in " + utility.duration_string(start_time, end_time) + " seconds.")
    print("Done.")


def _evaluate_time_differences_between_pre_post_spikes(construction_data):
    assert isinstance(construction_data, config.TimeDifferencesBetweenPrePostSpikes.ConstructionData)
    print("  Building spike trains.")

    tmprof_begin_construction = time.time()

    cfg = construction_data.apply()
    assert isinstance(cfg, config.TimeDifferencesBetweenPrePostSpikes.Configuration)

    print("  Starting simulation.")

    tmprof_begin_simulation = time.time()

    post_pre_time_differences = []
    spike_times = []
    t = cfg.start_time
    for step in range(cfg.nsteps):
        utility.print_progress_string(step, cfg.nsteps)

        was_pre_spike = cfg.pre_spike_train.on_time_step(t, cfg.dt)
        was_post_spike = cfg.post_spike_train.on_time_step(t, cfg.dt)

        if ((was_pre_spike or was_post_spike) and
                    len(cfg.pre_spike_train.get_spikes_history()) > 0 and
                    len(cfg.post_spike_train.get_spikes_history()) > 0):
            post_pre_time_differences.append(cfg.post_spike_train.get_spikes_history()[-1] - cfg.pre_spike_train.get_spikes_history()[-1])
            spike_times.append(t + cfg.dt)

        t += cfg.dt
    assert len(post_pre_time_differences) == len(spike_times)

    print("  Saving results.")

    tmprof_begin_save = time.time()

    if os.path.exists(cfg.output_dir):
        shutil.rmtree(cfg.output_dir)
    os.makedirs(cfg.output_dir)
    plots_output_dir = os.path.join(cfg.output_dir, "plots")
    os.makedirs(plots_output_dir)

    pathname = os.path.join(cfg.output_dir, "construction_data.json")
    print("    Saving construction data for spike trains to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(construction_data.to_json(), sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "configuration.json")
    print("    Saving configuration of spike trains to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(cfg.to_json(), sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "post_pre_time_differences.json")
    print("    Saving time differences between post- and pre- spikes to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps({
            "post_pre_time_differences": post_pre_time_differences,
            "spike_times": spike_times
        }, sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "pre_spikes_history.json")
    print("    Saving pre-spikes history to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(cfg.pre_spike_train.get_spikes_history(), sort_keys=True, indent=4))

    pathname = os.path.join(cfg.output_dir, "post_spikes_history.json")
    print("    Saving post-spikes history to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(cfg.post_spike_train.get_spikes_history(), sort_keys=True, indent=4))

    pathname = os.path.join(plots_output_dir, "pre_spiking_distribution" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(cfg.pre_spike_train.get_spiking_distribution(), pathname, normalised=False)

    pathname = os.path.join(plots_output_dir, "post_spiking_distribution" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(cfg.post_spike_train.get_spiking_distribution(), pathname, normalised=False)

    post_pre_time_differences_distribution = distribution.Distribution(
        datalgo.make_histogram(post_pre_time_differences, 0.001, 0.0)
        )

    pathname = os.path.join(cfg.output_dir, "post_pre_time_differences_distribution.json")
    print("    Saving distribution of time differences between post- and pre- spikes to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(post_pre_time_differences_distribution.to_json(), sort_keys=True, indent=4))

    pathname = os.path.join(plots_output_dir, "post_pre_time_differences_distribution" + cfg.plot_files_extension)
    print("    Saving plot " + pathname)
    plot.histogram(post_pre_time_differences_distribution, pathname, normalised=False)

    tmprof_end = time.time()

    time_profile = {
        "construction": tmprof_begin_simulation - tmprof_begin_construction,
        "simulation": tmprof_begin_save - tmprof_begin_simulation,
        "save": tmprof_end - tmprof_begin_save,
        "TOTAL": tmprof_end - tmprof_begin_construction
    }
    pathname = os.path.join(cfg.output_dir, "time_profile.json")
    print("    Saving time profile to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(time_profile, sort_keys=True, indent=4))

    print("  Time profile of the evaluation [in seconds]:" +
          "\n    Construction: " + utility.duration_string(tmprof_begin_construction, tmprof_begin_simulation) +
          "\n    Simulation: " + utility.duration_string(tmprof_begin_simulation, tmprof_begin_save) +
          "\n    Saving results: " + utility.duration_string(tmprof_begin_save, tmprof_end) +
          "\n    TOTAL: " + utility.duration_string(tmprof_begin_construction, tmprof_end))

    print("  Done.")


def _compute_interconfig_for_time_differences_between_pre_post_spikes(cfg):
    assert isinstance(cfg, config.TimeDifferencesBetweenPrePostSpikes)
    print("Building the inter-configuration summary data to '" + cfg.get_interconfig_output_dir() + "'.")
    tmprof_begin = time.time()

    def make_comparison_plots_of_pre_post_difference_distributions(cfg):
        print("    Building comparison plots of pre- and post- difference distributions.")
        output_root_dir = os.path.join(cfg.get_interconfig_output_dir(), "compare_distribution_plots")
        os.makedirs(output_root_dir, exist_ok=True)

        considered_percentages_of_regularity_phases = [25.0, 50.0, 75.0]
        considered_mean_frequencies = [12.0, 15.0, 18.0, 48.0, 60.0, 72.0]

        print("        - collecting source distributions.")
        tasks = dict()
        for case_output_dir in cfg.get_output_dirs_of_configurations():
            files = [x for x in os.listdir(case_output_dir) if os.path.isfile(os.path.join(case_output_dir, x))]
            if "construction_data.json" not in files or "post_pre_time_differences_distribution.json" not in files:
                continue
            with open(os.path.join(case_output_dir, "construction_data.json"), "r") as ifile:
                construction_data = json.load(ifile)
            if all(abs(construction_data["pre_percentage_of_regularity_phases"] - p) > 0.001 for p in considered_percentages_of_regularity_phases):
                continue
            if all(abs(construction_data["post_percentage_of_regularity_phases"] - p) > 0.001 for p in considered_percentages_of_regularity_phases):
                continue
            if all(abs(construction_data["pre_mean_frequency"] - f) > 0.001 for f in considered_mean_frequencies):
                continue
            if all(abs(construction_data["post_mean_frequency"] - f) > 0.001 for f in considered_mean_frequencies):
                continue

            task_type = (
                "pre_"  + ("e" if construction_data["pre_is_excitatory"]  is True else "i") + "_"
                "post_" + ("e" if construction_data["post_is_excitatory"] is True else "i")
                )

            task_subtype = (
                "regulatory_" +
                "pre_"  + format(construction_data["pre_percentage_of_regularity_phases"], ".2f") + "_" +
                "post_" + format(construction_data["post_percentage_of_regularity_phases"], ".2f")
                )

            record = {
                "dir": case_output_dir,
                "pre_mean_frequency": construction_data["pre_mean_frequency"],
                "post_mean_frequency": construction_data["post_mean_frequency"],
            }

            if task_type in tasks:
                if task_subtype in tasks[task_type]:
                    tasks[task_type][task_subtype].append(record)
                else:
                    tasks[task_type][task_subtype] = [record]
            else:
                tasks[task_type] = {task_subtype: [record]}
        assert len(tasks) == 4 and all(len(sub) == 9 and all(len(dirs) == 9 for _, dirs in sub.items()) for _, sub in tasks.items())
        print("        - generating plots.")
        for task_name, subtasks in tasks.items():
            for subtask_name, records in subtasks.items():
                full_name = task_name + "__" + subtask_name
                with plot.Plot(os.path.join(output_root_dir, full_name + ".png"), full_name) as plt:
                    for record in records:
                        print("            " + full_name)
                        with open(os.path.join(record["dir"], "post_pre_time_differences_distribution.json"), "r") as ifile:
                            differences_distribution_in_json = json.load(ifile)
                        differences_distribution = distribution.Distribution.from_json(differences_distribution_in_json)
                        plt.curve(
                            datalgo.interpolate_discrete_function(
                                datalgo.approximate_discrete_function(differences_distribution.get_probability_points())
                                ),
                            legend=(
                                "pre " + format(record["pre_mean_frequency"], ".2f") +
                                ", post " + format(record["post_mean_frequency"], ".2f")
                                )
                            )

    make_comparison_plots_of_pre_post_difference_distributions(cfg)

    tmprof_end = time.time()
    print("  Done in " + utility.duration_string(tmprof_begin, tmprof_end) + " seconds.")


def evaluate_time_differences_between_pre_post_spikes(cfg, force_recompute):
    assert isinstance(cfg, config.TimeDifferencesBetweenPrePostSpikes)
    start_time = time.time()
    for construction_data in cfg.get_list_of_construction_data():
        assert isinstance(construction_data, config.TimeDifferencesBetweenPrePostSpikes.ConstructionData)
        if force_recompute is False and os.path.isdir(construction_data.get_output_root_dir()):
            print("The configuration '" + construction_data.get_name() + "' already exists. Skipping its computation.")
        else:
            print("Building the configuration '" + construction_data.get_name() + "'.")
            _evaluate_time_differences_between_pre_post_spikes(construction_data)
    if force_recompute or not os.path.exists(cfg.get_interconfig_output_dir()):
        if os.path.exists(cfg.get_interconfig_output_dir()):
            shutil.rmtree(cfg.get_interconfig_output_dir())
        os.makedirs(cfg.get_interconfig_output_dir())
        _compute_interconfig_for_time_differences_between_pre_post_spikes(cfg)
    else:
        print("The inter-configuration summary data '" + cfg.get_interconfig_output_dir() + "' already exist. "
              "Skipping their computation.")
    end_time = time.time()
    print("The whole evaluation finished in " + utility.duration_string(start_time, end_time) + " seconds.")
    print("Done.")


def _compute_interconfig_for_evaluate_synaptic_plasticity(cfg):
    assert isinstance(cfg, config.SynapticPlasticity)
    points = []
    rgb = []
    for case_source_dir, _, files in os.walk(cfg.output_dir):
        if "weight_derivatives.json" not in files or "source_data_info.json" not in files:
            continue
        with open(os.path.join(case_source_dir, "weight_derivatives.json"), "r") as ifile:
            weight_derivatives = json.load(ifile)
        if "sum_of_derivatives" not in weight_derivatives:
            print("ERROR: Wrong format of the json file " + os.path.join(case_source_dir, "weight_derivatives.json") + ".")
            continue
        with open(os.path.join(case_source_dir, "source_data_info.json"), "r") as ifile:
            source_data_info = json.load(ifile)
        if not isinstance(source_data_info, dict) or "source_data_dir" not in source_data_info:
            print("ERROR: Wrong format of the json file " + os.path.join(case_source_dir, "source_data_info.json") + ".")
            continue
        pathname = os.path.join(source_data_info["source_data_dir"], "construction_data.json")
        if not os.path.isfile(pathname):
            print("ERROR: Cannot find the file " + pathname)
            continue
        with open(pathname, "r") as ifile:
            source_data = json.load(ifile)
        if not isinstance(source_data, dict) or not all(x in source_data for x in ["post_is_excitatory",
                                                                                   "post_mean_frequency",
                                                                                   "post_percentage_of_regularity_phases",
                                                                                   "pre_is_excitatory",
                                                                                   "pre_mean_frequency",
                                                                                   "pre_percentage_of_regularity_phases"]):
            print("ERROR: Wrong format of the json file " + pathname + ".")
            continue
        points.append({
            "x": source_data["pre_mean_frequency"],
            "y": source_data["post_mean_frequency"],
            "z": weight_derivatives["sum_of_derivatives"]
            })
        rgb.append({
            "r": source_data["pre_percentage_of_regularity_phases"] / 100.0,
            "g": 0.0,
            "b": source_data["post_percentage_of_regularity_phases"] / 100.0
            })

    pathname = os.path.join(cfg.get_interconfig_output_dir(), "weight_derivatives.json")
    print("    Saving weight derivatives to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps({
            "description": {
                "brief": "Progress of weight derivatives of a synapse w.r.t. mean frequencies of pre- and post- "
                         "synaptic spike trains.",
                "details": "The pre- spike train is excitatory; the post- spike train is excitatory. "
                           "For each pre- and post- frequency we have 4*4 values of sums of weight derivatives; "
                           "each such value corresponds to a certain levels of noise for pre- and post- spike trains. "
                           "These values are distinguished by their colour: red component is the noise level for "
                           "pre- spike train, green is always 0, and blue component is is the noise level for post- "
                           "spike train.",
                "x": "pre mean frequency",
                "y": "post mean frequency",
                "z": "sum of weight derivatives"
            },
            "num_dimensions": 3,
            "points": points,
            "rgb": rgb
        }, sort_keys=True, indent=4))


def evaluate_synaptic_plasticity(cfg, force_recompute, dependencies):
    assert isinstance(cfg, config.SynapticPlasticity)

    tmprof_begin = time.time()

    source_data_root_dir = None
    for path in dependencies + cfg.dependencies:
        try:
            exp_name = os.path.split(path)[1]
            cfg_name = os.path.split(os.path.split(path)[0])[1]
            if cfg_name == config.TimeDifferencesBetweenPrePostSpikes.__name__ and exp_name == "all_in_one":
                source_data_root_dir = path
                break
        except:
            pass
    if source_data_root_dir is None:
        print("ERROR: Cannot find a path to results of the dependent configuration '" +
              config.TimeDifferencesBetweenPrePostSpikes.__name__ + "/" + "all_in_one" + "'. "
              "Add that path to the command line option --dependencies.")
        return
    cfg.dependencies = [source_data_root_dir]

    if force_recompute or not os.path.exists(cfg.output_dir):
        if os.path.exists(cfg.output_dir):
            shutil.rmtree(cfg.output_dir)
        os.makedirs(cfg.output_dir)

    pathname = os.path.join(cfg.output_dir, "configuration.json")
    print("    Saving configuration to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(cfg.to_json(), sort_keys=True, indent=4))

    tmprof_computation_total = 0.0
    tmprof_save_total = 0.0
    num_computed_cases = 0
    num_skipped_cases = 0
    num_errored_cases = 0

    for case_source_dir, _, files in os.walk(source_data_root_dir):
        if "construction_data.json" not in files or "post_pre_time_differences.json" not in files:
            continue

        case_output_dir = os.path.join(cfg.output_dir, os.path.relpath(case_source_dir, source_data_root_dir))
        case_output_plots_dir = os.path.join(case_output_dir, "plots")
        if force_recompute or not os.path.exists(case_output_dir):
            if os.path.exists(case_output_dir):
                shutil.rmtree(case_output_dir)
            os.makedirs(case_output_dir)
            if os.path.exists(case_output_plots_dir):
                shutil.rmtree(case_output_plots_dir)
            os.makedirs(case_output_plots_dir)
        else:
            print("The results for time difference data in '" + case_source_dir + "' already exist "
                  "(" + case_output_dir + "). Skipping their re-computation.")
            num_skipped_cases += 1
            continue

        print("    Processing time difference data in " + case_source_dir)

        with open(os.path.join(case_source_dir, "construction_data.json"), "r") as ifile:
            constuction_data = json.load(ifile)
        if "pre_is_excitatory" not in constuction_data or "post_is_excitatory" not in constuction_data:
            print("ERROR: Unexpected content of the file '" + os.path.join(case_source_dir, "construction_data.json") + "'. "
                  "Skipping the computation.")
            num_errored_cases += 1
            continue

        with open(os.path.join(case_source_dir, "post_pre_time_differences.json"), "r") as ifile:
            post_pre_time_differences = json.load(ifile)
        if not isinstance(post_pre_time_differences, dict) or (
                "post_pre_time_differences" not in post_pre_time_differences or
                "spike_times" not in post_pre_time_differences or
                not isinstance(post_pre_time_differences["post_pre_time_differences"], list) or
                not isinstance(post_pre_time_differences["spike_times"], list) or
                len(post_pre_time_differences["post_pre_time_differences"]) != len(post_pre_time_differences["spike_times"]) or
                not all(type(x) in [int, float] for x in post_pre_time_differences["post_pre_time_differences"]) or
                not all(type(x) in [int, float] for x in post_pre_time_differences["spike_times"])):
            print("ERROR: Unexpected content of the file '" +
                  os.path.join(case_source_dir, "post_pre_time_differences.json") + "'. "
                  "Skipping the computation.")
            num_errored_cases += 1
            continue

        pathname = os.path.join(case_output_dir, "source_data_info.json")
        print("    Saving source data info to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps({"source_data_dir": case_source_dir}, sort_keys=True, indent=4))

        tmprof_computation_begin = time.time()

        weight_derivative_function = cfg.get_weight_derivative_function(
            constuction_data["pre_is_excitatory"],
            constuction_data["post_is_excitatory"]
        )
        weight_derivatives = [weight_derivative_function(dt) for dt in post_pre_time_differences["post_pre_time_differences"]]

        tmprof_computation_end = time.time()
        tmprof_computation_total += tmprof_computation_end - tmprof_computation_begin
        num_computed_cases += 1

        tmprof_save_begin = time.time()

        pathname = os.path.join(case_output_dir, "weight_derivatives.json")
        print("    Saving weight derivatives to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps({
                "weight_derivatives": weight_derivatives,
                "sum_of_derivatives": sum(weight_derivatives),
                "sum_of_time_differences": sum(post_pre_time_differences["post_pre_time_differences"]),
            }, sort_keys=True, indent=4))

        weight_derivatives_distribution = distribution.Distribution(
            datalgo.make_histogram(weight_derivatives, 0.00001, 0.0)
            )

        pathname = os.path.join(case_output_dir, "weight_derivatives_distribution.json")
        print("    Saving distribution of weight derivatives to " + pathname)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(weight_derivatives_distribution.to_json(), sort_keys=True, indent=4))

        pathname = os.path.join(case_output_plots_dir, "weight_derivatives_distribution" + cfg.plot_files_extension)
        print("    Saving plot " + pathname)
        plot.histogram(weight_derivatives_distribution, pathname, normalised=False)

        tmprof_save_end = time.time()
        tmprof_save_total += tmprof_save_end - tmprof_save_begin

    tmprof_interconfig_begin = time.time()
    if force_recompute or not os.path.exists(cfg.get_interconfig_output_dir()):
        if os.path.exists(cfg.get_interconfig_output_dir()):
            shutil.rmtree(cfg.get_interconfig_output_dir())
        os.makedirs(cfg.get_interconfig_output_dir())
        _compute_interconfig_for_evaluate_synaptic_plasticity(cfg)
    else:
        print("The inter-configuration summary data '" + cfg.get_interconfig_output_dir() + "' already exist. "
              "Skipping their computation.")
    tmprof_end = time.time()

    time_profile = {
        "total_cases_computation": tmprof_computation_total,
        "total_cases_save": tmprof_save_total,
        "total_interconfig": tmprof_end - tmprof_interconfig_begin,
        "TOTAL": tmprof_end - tmprof_begin,
        "num_computed_cases": num_computed_cases,
        "num_skipped_cases": num_skipped_cases,
        "num_errored_cases": num_errored_cases
    }
    pathname = os.path.join(cfg.output_dir, "time_profile.json")
    print("    Saving time profile to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(time_profile, sort_keys=True, indent=4))

    print("  Time profile of the evaluation [in seconds]:" +
          "\n    Computation: " + format(tmprof_computation_total, ".2f") +
          "\n    TOTAL: " + utility.duration_string(tmprof_begin, tmprof_end))

    print("  Done.")


def evaluate_neuron_receives_aligned_input(cfg, force_recompute, dependencies):
    assert isinstance(cfg, config.NeuronReceivesAlignedInput)

    tmprof_begin = time.time()

    print("Simulating pivot train")
    t = cfg.start_time
    for step in range(cfg.nsteps):
        utility.print_progress_string(step, cfg.nsteps)
        cfg.pivot_train.on_time_step(t, cfg.dt)
        t += cfg.dt

    tmprof_pivot_simulation = time.time()

    print("Simulating aligned trains")
    cell = neuron.Neuron(
                cfg.cell_soma,
                [synapse.Synapse.constant() for _ in range(len(cfg.excitatory_trains))],
                [synapse.Synapse.constant() for _ in range(len(cfg.inhibitory_trains))],
                cfg.num_sub_iterations,
                cfg.start_time,
                neuron.RecordingConfig(do_recording_of_key_variables_only=False)
                )

    voltage_curve_excitatory = []
    voltage_curve_inhibitory = []
    voltage_curve = []

    t = cfg.start_time
    for step in range(cfg.nsteps):
        utility.print_progress_string(step, cfg.nsteps)
        cell.integrate(t, cfg.dt)

        num_excitatory_spikes = 0
        for i in range(len(cfg.excitatory_trains)):
            was_spike_generated = cfg.excitatory_trains[i].on_time_step(t, cfg.dt)
            if was_spike_generated:
                cell.on_excitatory_spike(i)
                num_excitatory_spikes += 1
        if num_excitatory_spikes > 0:
            voltage_curve_excitatory.append((t + cfg.dt, num_excitatory_spikes))

        num_inhibitory_spikes = 0
        for i in range(len(cfg.inhibitory_trains)):
            was_spike_generated = cfg.inhibitory_trains[i].on_time_step(t, cfg.dt)
            if was_spike_generated:
                cell.on_inhibitory_spike(i)
                num_inhibitory_spikes += 1
        if num_inhibitory_spikes > 0:
            voltage_curve_inhibitory.append((t + cfg.dt, num_inhibitory_spikes))

        if num_excitatory_spikes > 0 or num_inhibitory_spikes > 0:
            voltage_curve.append((t + cfg.dt, num_excitatory_spikes - num_inhibitory_spikes))

        t += cfg.dt

    tmprof_cell_simulation = time.time()

    print("Saving results")

    if force_recompute or not os.path.exists(cfg.output_dir):
        if os.path.exists(cfg.output_dir):
            shutil.rmtree(cfg.output_dir)
        os.makedirs(cfg.output_dir)

    for var_name, points in cell.get_soma_recording().items():
        if len(points) != 0:
            file_name = "soma_" + cell.get_soma().get_name() + "__VAR[" + var_name + "]"
            plot.curve_per_partes(
                points,
                os.path.join(cfg.output_dir, file_name + cfg.plot_files_extension),
                cfg.start_time,
                cfg.start_time + cfg.nsteps * cfg.dt,
                cfg.plot_time_step,
                5,
                lambda p: print("    Saving plot " + p),
                get_colour_soma(),
                cell.get_soma().get_short_description()
                )

    print("    Saving post spikes ISI histogram")
    plot.histogram(
        datalgo.make_histogram(datalgo.make_difference_events(cell.get_spikes()), cfg.dt, cfg.start_time),
        os.path.join(cfg.output_dir, "hist_isi_post_spikes.png"),
        False
        )

    for i in range(0, len(cfg.excitatory_trains), max(1, len(cfg.excitatory_trains) // 10)):
        print("    Saving excitatory pre spikes ISI histogram of train #" + str(i) + ".")
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(cfg.excitatory_trains[i].get_spikes_history()),
                cfg.dt,
                cfg.start_time
                ),
            os.path.join(cfg.output_dir, "hist_isi_pre_pikes_e" + str(i) + ".png"),
            normalised=False
            )

    for i in range(0, len(cfg.inhibitory_trains), max(1, len(cfg.inhibitory_trains) // 10)):
        print("    Saving inhibitory pre spikes ISI histogram of train #" + str(i) + ".")
        plot.histogram(
            datalgo.make_histogram(
                datalgo.make_difference_events(cfg.inhibitory_trains[i].get_spikes_history()),
                cfg.dt,
                cfg.start_time
                ),
            os.path.join(cfg.output_dir, "hist_isi_pre_pikes_i" + str(i) + ".png"),
            normalised=False
            )

    e_board_histories = []
    for i in range(0, len(cfg.excitatory_trains), max(1, len(cfg.excitatory_trains) // 10)):
        e_board_histories.append(cfg.excitatory_trains[i].get_spikes_history())
    i_board_histories = []
    for i in range(0, len(cfg.inhibitory_trains), max(1, len(cfg.inhibitory_trains) // 10)):
        i_board_histories.append(cfg.inhibitory_trains[i].get_spikes_history())

    plot.event_board_per_partes(
        [cell.get_spikes()] + e_board_histories + i_board_histories,
        os.path.join(cfg.output_dir, "spikes_board.png"),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        1.0,
        5,
        lambda p: print("    Saving spikes board part: " + os.path.basename(p)),
        [[(0.0, 0.0, 0.0)] * len(cell.get_spikes())] + [[plot.get_random_rgb_colour()] * len(spikes_history)
                                                        for spikes_history in e_board_histories]
                                                     + [[plot.get_random_rgb_colour()] * len(spikes_history)
                                                        for spikes_history in i_board_histories],
        " " + plot.get_title_placeholder() + " SPIKES BOARD"
        )

    for kind, curve, colour in [("excitatory", voltage_curve_excitatory, get_colour_pre_excitatory()),
                                ("inhibitory", voltage_curve_inhibitory, get_colour_pre_inhibitory())]:
        pathname = os.path.join(cfg.output_dir, "voltage_effect_curve_" + kind + ".json")
        print("    Saving voltage effect curve of " + kind + " spike trains in JSON format.")
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(curve, sort_keys=True, indent=4))
        plot.curve_per_partes(
            datalgo.reduce_gaps_between_points_along_x_axis(curve, cfg.dt),
            os.path.join(cfg.output_dir, "voltage_effect_curve_" + kind + cfg.plot_files_extension),
            cfg.start_time,
            cfg.start_time + cfg.nsteps * cfg.dt,
            cfg.plot_time_step,
            5,
            lambda p: print("    Saving plot " + p),
            colour,
            plot.get_title_placeholder()
            )
        pathname = os.path.join(cfg.output_dir, "voltage_effect_histogram" + kind + ".json")
        print("    Saving voltage effect histogram of " + kind + " spike trains in JSON format.")
        voltage_histogram = datalgo.make_histogram([p[1] for p in curve], 1.0, 0.0)
        with open(pathname, "w") as ofile:
            ofile.write(json.dumps(voltage_histogram, sort_keys=True, indent=4))
        plot.histogram(
            voltage_histogram,
            os.path.join(cfg.output_dir, "voltage_effect_histogram_" + kind + cfg.plot_files_extension),
            colours=colour,
            normalised=False
            )
    pathname = os.path.join(cfg.output_dir, "voltage_effect_curve" + ".json")
    print("    Saving voltage effect curve of all spike trains in JSON format to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(voltage_curve, sort_keys=True, indent=4))
    plot.curve_per_partes(
        datalgo.reduce_gaps_between_points_along_x_axis(voltage_curve, cfg.dt),
        os.path.join(cfg.output_dir, "voltage_effect_curve" + cfg.plot_files_extension),
        cfg.start_time,
        cfg.start_time + cfg.nsteps * cfg.dt,
        cfg.plot_time_step,
        5,
        lambda p: print("    Saving plot " + p),
        get_colour_pre_excitatory_and_inhibitory(),
        plot.get_title_placeholder()
        )
    pathname = os.path.join(cfg.output_dir, "voltage_effect_histogram" + ".json")
    print("    Saving voltage effect histogram of all spike trains in JSON format to " + pathname)
    voltage_histogram = datalgo.make_histogram([p[1] for p in voltage_curve], 1.0, 0.0)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(voltage_histogram, sort_keys=True, indent=4))
    plot.histogram(
        voltage_histogram,
        os.path.join(cfg.output_dir, "voltage_effect_histogram" + cfg.plot_files_extension),
        colours=get_colour_pre_excitatory_and_inhibitory(),
        normalised=False
        )

    tmprof_end = time.time()

    time_profile = {
        "pivot_simulation": tmprof_pivot_simulation - tmprof_begin,
        "cell_simulation": tmprof_cell_simulation - tmprof_pivot_simulation,
        "save_results": tmprof_end - tmprof_cell_simulation,
        "TOTAL": tmprof_end - tmprof_begin,
        "spike_trains_statistics": spike_train.merge_statistics(
            [train.get_statistics() for train in cfg.excitatory_trains + cfg.inhibitory_trains]
            )
    }
    pathname = os.path.join(cfg.output_dir, "time_profile.json")
    print("    Saving time profile to " + pathname)
    with open(pathname, "w") as ofile:
        ofile.write(json.dumps(time_profile, sort_keys=True, indent=4))

    print("  Time profile of the evaluation [in seconds]:" +
          "\n    pivot_simulation" + utility.duration_string(tmprof_begin, tmprof_pivot_simulation) +
          "\n    cell_simulation" + utility.duration_string(tmprof_pivot_simulation, tmprof_cell_simulation) +
          "\n    save_results" + utility.duration_string(tmprof_cell_simulation, tmprof_end) +
          "\n    TOTAL: " + utility.duration_string(tmprof_begin, tmprof_end))

    print("  Done.")


def main(cmdline):
    if cmdline.test is not None and cmdline.evaluate is None:
        for tst in tests.get_registered_tests():
            if tst["name"] == cmdline.test:
                tst["output_dir"] = cmdline.output_dir
                return tests.run_test(tst)
        print("ERROR: There is no test of the name '" + str(cmdline.test) + "'. Use the option "
              "'--help' to list all available tests.")
        return 1
    for cfg in config.get_registered_configurations():
        if cmdline.evaluate is None or cfg["name"] == cmdline.evaluate:
            cfg["output_dir"] = cmdline.output_dir
            if cfg["class_name"] == config.NeuronWithInputSynapses.__name__:
                evaluate_neuron_with_input_synapses(config.construct_experiment(cfg), cmdline.force_recompute)
            elif cfg["class_name"] == config.SynapseAndSpikeNoise.__name__:
                evaluate_synapse_and_spike_noise(config.construct_experiment(cfg), cmdline.force_recompute)
            elif cfg["class_name"] == config.PrePostSpikeNoisesDifferences.__name__:
                evaluate_pre_post_spike_noises_differences(config.construct_experiment(cfg), cmdline.force_recompute)
            elif cfg["class_name"] == config.EffectOfInputSpikeTrains.__name__:
                evaluate_effect_of_input_spike_trains(config.construct_experiment(cfg), cmdline.force_recompute)
            elif cfg["class_name"] == config.TimeDifferencesBetweenPrePostSpikes.__name__:
                evaluate_time_differences_between_pre_post_spikes(config.construct_experiment(cfg), cmdline.force_recompute)
            elif cfg["class_name"] == config.SynapticPlasticity.__name__:
                evaluate_synaptic_plasticity(config.construct_experiment(cfg), cmdline.force_recompute, cmdline.dependencies)
            elif cfg["class_name"] == config.NeuronReceivesAlignedInput.__name__:
                evaluate_neuron_receives_aligned_input(config.construct_experiment(cfg), cmdline.force_recompute, cmdline.dependencies)
            else:
                print("ERROR: There is not defined the evaluation function for configuration class '" +
                      cfg["class_name"] + "'.")
                return 1
            if cmdline.evaluate:
                return 0
    if cmdline.evaluate is not None:
        print("ERROR: Unknown configuration '" + str(cmdline.evaluate) + "'. Use the option "
              "'--help' to list all available configurations.")
        return 1
    return 0


def parse_command_line_options():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This module provides evaluation of spiking models of neurons and synapses.\n"
                    "Individual experiments are fully defined in so called 'configurations'.\n"
                    "To evaluate an experiment specify the name of its configuration.",
        epilog="Here is the list of all available configurations:\n\n" +
               "\n\n".join(["* " + cfg["name"] + "\n\n" + cfg["description"]
                            for cfg in config.get_registered_configurations()]) +
               "\n\nHere is the list of all tests:\n\n" +
               "\n\n".join(["* " + tst["name"] + "\n\n" + tst["description"]
                            for tst in tests.get_registered_tests()])
        )
    parser.add_argument(
        "--evaluate", type=str, default=None,
        help="Evaluate the experiment defined in the configuration of the passed name. Use the option "
             "--help to list all available configurations. If you omit this option, then all configurations "
             "will be evaluated in a sequence."
        )
    parser.add_argument(
        "--test", type=str,
        help="Runs the test of the passed name. Use the option --help to list all available tests."
        )
    parser.add_argument(
        "--output-dir", type=str,
        help="Allows to specify a root directory under which the chosen evaluation or test will save "
             "data, if any. When this option is omitted then the default output root directory is used, i.e. "
             "either the path '../../dist/evaluation/pycellab' or '.', both relative to the script location. "
             "The first relative path is used the script is located under 'E2/code/pycellab'."
        )
    parser.add_argument(
        "--force-recompute", action="store_true",
        help="When specified and the output directory already exists, then the old directory will be removed "
             "and the data will be recomputed."
        )
    parser.add_argument(
        "--dependencies", nargs='+',
        help="When currently evaluated configuration depends on results of other configurations, then this option"
             "allows to pass it a list of output directories of those configurations in order to find the required "
             "data. It is explicitly stated in the description of each configuration what other configuration it "
             "depends on (if any). NOTE: This option accepts a SPACE SEPARATED list of disk paths. If a path "
             "comprises spaces, then enclose the path into quotes. NOTE: If the current configuration, say 'ABC',"
             "depends on some configuration, say 'XYZ', no path ending with 'XYZ' is passed to this option, and "
             "'some/path/ABC' is the output directory of 'ABC', then the path 'some/path/XYZ' is used in the search "
             "for result data of 'XYZ'."
        )
    cmdline = parser.parse_args()

    if cmdline.output_dir is None:
        my_dir = os.path.dirname(__file__)
        cmdline.output_dir = os.path.normpath(os.path.join(my_dir, "..", "..", "dist", "evaluation", "pycellab")) \
                             if str(my_dir).replace("\\", "/").endswith("E2/code/pycellab") else my_dir

    if cmdline.dependencies is None:
        cmdline.dependencies = []
    else:
        checked_dependencies = []
        for p in cmdline.dependencies:
            path = os.path.abspath(p)
            if not os.path.isdir(path):
                print("WARNING: In option --dependencies: The path '" + path + "' does not reference "
                      "any exising directory. It will be IGNORED during the evaluation!")
            else:
                checked_dependencies.append(path)
        cmdline.dependencies = checked_dependencies

    return cmdline


if __name__ == "__main__":
    exit(main(parse_command_line_options()))
