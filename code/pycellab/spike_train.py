import bisect
import numpy
import time
import distribution


class SpikeTrain:
    """
    The class generates a sequence of spikes (action potentials). Time intervals between individual spikes
    are distributed in the generated sequence according to a given distribution, i.e. so called
    `spiking_distribution'. Other parameters of the __init__ function of the class allows to specify
    a degree of correlation of "Inter-Spikes-Intervals" in the sequence. Regardless of the configuration
    of correlation degree, the generated sequence of spikes always represent events of `spiking_distribution'.
    Finally, an instance of the class provides recording of generated spikes in the sequence. The parameter
    `recording_controller' allows a user to specify when the recoding will be active and when inactive.
    """

    def __init__(
            self,
            spiking_distribution,
            percentage_of_regularity_phases,
            noise_length_distribution,
            regularity_length_distribution,
            max_spikes_buffer_size,
            regularity_chunk_size,
            recording_controller
            ):
        """
        :param spiking_distribution:
            The distribution used for generation of spike events.
        :param percentage_of_regularity_phases:
            Specifies a percentage (in range 0..100) of whole simulation time, when algorithm enforcing
            correlations of inter-spike-intervals will be active. In the remaining time the algorithm will
            be inactive.
        :param noise_length_distribution:
            A distribution specifying durations of phases when the spikes-correlation algorithm is inactive.
        :param regularity_length_distribution:
            A distribution specifying durations of phases when the spikes-correlation algorithm is active.
        :param max_spikes_buffer_size:
            Spikes generated by `spiking_distribution' are stored a buffer, before they proceed to the
            spike train algorithms. Size of the buffer affects correlation degree of spikes in the spikes
            train. Greater value gives greater degree of correlation. Values in range 75..150 give good
            results. The value 100 can be considered as default value. However, we recommend to do
            same experimentation to tune the values to get correlation degree you need.
        :param regularity_chunk_size:

        :param recording_controller:
            It is a function taking two arguments `last_recording_time' and  `current_time' returning a bool.
            It tells the train whether recording of a spike event should be performed at `current_time' or not.
            The first parameter `last_recording_time' represents the last time when this function returned True
            to the train. Note that initial time of the simulation is considered as a time when the function
            returned True. Here are two basic examples of the function:
                lambda last_recording_time, current_time: True      # Record all generated spikes
                lambda last_recording_time, current_time: False     # Disable recording of spikes

        Look also to assertions below to see requirements (preconditions) of the parameters described above.
        """
        assert isinstance(spiking_distribution, distribution.Distribution)
        assert type(percentage_of_regularity_phases) in [int, float]
        assert 0 <= percentage_of_regularity_phases and percentage_of_regularity_phases <= 100
        assert isinstance(noise_length_distribution, distribution.Distribution)
        assert isinstance(regularity_length_distribution, distribution.Distribution)
        assert regularity_length_distribution.get_mean() > 0.0001
        assert isinstance(max_spikes_buffer_size, int) and max_spikes_buffer_size >= 1
        assert isinstance(regularity_chunk_size, int) and regularity_chunk_size in range(1, max_spikes_buffer_size)
        self._spiking_distribution = spiking_distribution
        self._phases_distribution = distribution.Distribution({
            "regularity": percentage_of_regularity_phases,
            "noise": 100 - percentage_of_regularity_phases
            })
        self._noise_length_distribution = noise_length_distribution
        self._regularity_length_distribution = regularity_length_distribution
        self._regularity_chunk_index_low = -1
        self._regularity_chunk_index_high = -1
        self._regularity_chunk_size = regularity_chunk_size
        self._spikes_buffer = []
        self._max_spikes_buffer_size = max_spikes_buffer_size
        self._is_noise_phase_active = True
        self._next_spike_time = None
        self._phase_start_time = None
        self._phase_end_time = None
        self._last_recording_time = None
        self._spikes_history = []
        self._recording_controller = recording_controller
        self._statistics = SpikeTrain.get_initial_statistics()

    @staticmethod
    def get_initial_statistics():
        return {
            "num_generated_spike_events": 0,
            "num_calls_to_do_recording": 0,
            "num_regularity_phases": 0,
            "total_real_time_of_regularity_phases": 0.0,
            "total_desired_time_of_regularity_phases": 0.0,
            "num_noise_phases": 0,
            "total_real_time_of_noise_phases": 0.0,
            "total_desired_time_of_noise_phases": 0.0,
            "time_on_time_step": 0.0,
            "calls_on_time_step": 0,
            "time__recharge_spikes_buffer": 0.0,
            "calls__recharge_spikes_buffer": 0,
        }

    @staticmethod
    def get_keys_of_statistics():
        return SpikeTrain.get_initial_statistics().keys()

    def get_spiking_distribution(self):
        return self._spiking_distribution

    def get_phases_distribution(self):
        return self._phases_distribution

    def get_noise_length_distribution(self):
        return self._noise_length_distribution

    def get_regularity_length_distribution(self):
        return self._regularity_length_distribution

    def get_max_spikes_buffer_size(self):
        return self._max_spikes_buffer_size

    def get_regularity_chunk_size(self):
        return self._regularity_chunk_size

    def get_recording_controller(self):
        return self._recording_controller

    def get_spikes_history(self):
        return self._spikes_history

    def get_statistics(self):
        return self._statistics

    def get_configuration(self):
        return {
            "spiking_distribution_mean": self.get_spiking_distribution().get_mean(),
            "percentage_of_regularity_phases": self.get_phases_distribution().get_histogram()["regularity"],
            "noise_length_distribution_min_duration": self.get_noise_length_distribution().get_events()[0],
            "noise_length_distribution_max_duration": self.get_noise_length_distribution().get_events()[-1],
            "noise_length_distribution_mean_duration": self.get_noise_length_distribution().get_mean(),
            "regularity_length_distribution_min_duration": self.get_regularity_length_distribution().get_events()[0],
            "regularity_length_distribution_max_duration": self.get_regularity_length_distribution().get_events()[-1],
            "regularity_length_distribution_mean_duration": self.get_regularity_length_distribution().get_mean(),
            "max_spikes_buffer_size": self.get_max_spikes_buffer_size(),
            "regularity_chunk_size": self.get_regularity_chunk_size()
        }

    def to_json(self):
        return {
            "spiking_distribution": self.get_spiking_distribution().to_json(),
            "phases_distribution": self.get_phases_distribution().to_json(),
            "noise_length_distribution": self.get_noise_length_distribution().to_json(),
            "regularity_length_distribution": self.get_regularity_length_distribution().to_json(),
            "regularity_chunk_size": self.get_regularity_chunk_size(),
            "max_spikes_buffer_size": self.get_max_spikes_buffer_size(),
            "spikes_history": self.get_spikes_history(),
            "statistics": self.get_statistics(),
        }

    def on_time_step(self, t, dt):
        self._statistics["calls_on_time_step"] += 1
        start_time = time.time()
        if self._next_spike_time is None:
            self._next_spike_time = t + dt + self._get_next_noise_phase_event()
            self._phase_start_time = t + dt
            self._phase_end_time = self._phase_start_time + self.get_noise_length_distribution().next_event()
            self._last_recording_time = t
        assert self._statistics["num_generated_spike_events"] == 1 + len(self._spikes_buffer) + self._statistics["num_calls_to_do_recording"]
        if self._next_spike_time > t + dt:
            self._statistics["time_on_time_step"] += time.time() - start_time
            return False
        self._do_recording(t, dt, self._next_spike_time)
        if self._phase_end_time <= self._next_spike_time:
            if self._is_noise_phase_active:
                self._statistics["num_noise_phases"] += 1
                self._statistics["total_desired_time_of_noise_phases"] += self._phase_end_time - self._phase_start_time
                self._statistics["total_real_time_of_noise_phases"] += self._next_spike_time - self._phase_start_time
            else:
                self._statistics["num_regularity_phases"] += 1
                self._statistics["total_desired_time_of_regularity_phases"] += self._phase_end_time - self._phase_start_time
                self._statistics["total_real_time_of_regularity_phases"] += self._next_spike_time - self._phase_start_time
            self._is_noise_phase_active = True if self.get_phases_distribution().next_event() == "noise" else False
            self._phase_start_time = self._next_spike_time
            self._phase_end_time = self._phase_start_time + (self.get_noise_length_distribution().next_event()
                                                             if self._is_noise_phase_active
                                                             else self.get_regularity_length_distribution().next_event())
            assert self._phase_end_time > t + dt
            self._regularity_chunk_index_low = -1
            self._regularity_chunk_index_high = -1
        self._next_spike_time += (self._get_next_noise_phase_event()
                                  if self._is_noise_phase_active
                                  else self._get_next_regularity_phase_event())
        assert self._next_spike_time > t + dt
        self._statistics["time_on_time_step"] += time.time() - start_time
        return True

    def _get_next_regularity_phase_event(self):
        if self._regularity_chunk_index_low == self._regularity_chunk_index_high:
            self._recharge_spikes_buffer(self.get_max_spikes_buffer_size())
            self._regularity_chunk_index_low = (bisect.bisect_left(self._spikes_buffer, self._next_spike_time)
                                                if self._regularity_chunk_index_low != -1
                                                else int(numpy.random.uniform(0, len(self._spikes_buffer))))
            self._regularity_chunk_index_high = self._regularity_chunk_index_low
            while self._regularity_chunk_index_high - self._regularity_chunk_index_low < self.get_regularity_chunk_size():
                if self._regularity_chunk_index_low == 0:
                    self._regularity_chunk_index_high += 1
                elif self._regularity_chunk_index_high == len(self._spikes_buffer):
                    self._regularity_chunk_index_low -= 1
                elif numpy.random.uniform() < 0.5:
                    self._regularity_chunk_index_low -= 1
                else:
                    self._regularity_chunk_index_high += 1
            assert self._regularity_chunk_index_low >= 0
            assert self._regularity_chunk_index_high <= len(self._spikes_buffer)
        assert self._regularity_chunk_index_low < self._regularity_chunk_index_high
        index = int(numpy.random.uniform(self._regularity_chunk_index_low, self._regularity_chunk_index_high))
        event = self._spikes_buffer.pop(index)
        self._regularity_chunk_index_high -= 1
        return event

    def _get_next_noise_phase_event(self):
        self._recharge_spikes_buffer(1)
        return self._spikes_buffer.pop(int(numpy.random.uniform(0, len(self._spikes_buffer))))

    def _recharge_spikes_buffer(self, desired_size):
        start_time = time.time()
        self._statistics["calls__recharge_spikes_buffer"] += 1
        assert isinstance(desired_size, int) and desired_size >= 1
        while len(self._spikes_buffer) < desired_size:
            event = self.get_spiking_distribution().next_event()
            assert event > 0.00001
            self._spikes_buffer.insert(bisect.bisect_left(self._spikes_buffer, event), event)
            self._statistics["num_generated_spike_events"] += 1
        self._statistics["time__recharge_spikes_buffer"] += time.time() - start_time

    def _do_recording(self, t, dt, spike_time):
        assert spike_time <= t + dt
        self._statistics["num_calls_to_do_recording"] += 1
        if self._recording_controller(self._last_recording_time, t + dt) is True:
            self._last_recording_time = t + dt
            self._spikes_history.append(spike_time)


def create(spiking_distribution,
           percentage_of_regularity_phases=25.0,
           regularity_phase_mean_duration=0.25,
           regularity_phase_min_duration=0.05,
           regularity_phase_max_duration=0.75,
           # regularity_phase_mean_duration=0.15,
           # regularity_phase_min_duration=0.025,
           # regularity_phase_max_duration=0.5,
           noise_phase_mean_duration=0.25,
           noise_phase_min_duration=0.05,
           noise_phase_max_duration=0.75,
           max_spikes_buffer_size=100,
           regularity_chunk_size=17,
           recording_controller=lambda last_recording_time, current_time: True
           ):
    """
    Simplifies construction of the spikes train by automating construction of distributions of
    both regularity and noise phases, provided you know minimal, maximal, and mean durations
    of the distributions.

    :param spiking_distribution:
        See description of the same parameter in SpikeTrain.__init__.
    :param percentage_of_regularity_phases:
        See description of the same parameter in SpikeTrain.__init__.
    :param regularity_phase_mean_duration:
        The mean event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `regularity_length_distribution`.
    :param regularity_phase_min_duration:
        The minimal event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `regularity_length_distribution`.
    :param regularity_phase_max_duration:
        The maximal event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `regularity_length_distribution`.
    :param noise_phase_mean_duration:
        The mean event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `noise_length_distribution`.
    :param noise_phase_min_duration:
        The minimal event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `noise_length_distribution`.
    :param noise_phase_max_duration:
        The maximal event (duration) of the distribution to be passed into SpikeTrain.__init__ as the
        parameter `noise_length_distribution`.
    :param max_spikes_buffer_size:
        See description of the same parameter in SpikeTrain.__init__.
    :param regularity_chunk_size:
        See description of the same parameter in SpikeTrain.__init__.
    :param recording_controller:
        See description of the same parameter in SpikeTrain.__init__.
    """
    return SpikeTrain(spiking_distribution,
                      percentage_of_regularity_phases,
                      distribution.hermit_distribution_with_desired_mean(
                            mean=noise_phase_mean_duration,
                            lo=noise_phase_min_duration,
                            hi=noise_phase_max_duration,
                            max_mean_error=0.01,
                            bin_size=0.0025
                            ),
                      distribution.hermit_distribution_with_desired_mean(
                            mean=regularity_phase_mean_duration,
                            lo=regularity_phase_min_duration,
                            hi=regularity_phase_max_duration,
                            max_mean_error=0.01,
                            bin_size=0.0025
                            ),
                      max_spikes_buffer_size,
                      regularity_chunk_size,
                      recording_controller
                      )
